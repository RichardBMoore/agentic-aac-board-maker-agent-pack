from __future__ import annotations

import base64
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FETCHER_PATH = ROOT / "skills" / "agentic-aac-board-maker" / "scripts" / "fetch_arasaac_symbols.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fetch_symbols = load_module(FETCHER_PATH, "fetch_arasaac_symbols")

PNG_BYTES = b"\x89PNG\r\n\x1a\nfakepixels"


def search_payload(*entries) -> bytes:
    return json.dumps(list(entries)).encode("utf-8")


def picto(pid: int, keyword: str, aac: bool = False) -> dict:
    return {"_id": pid, "aac": aac, "keywords": [{"keyword": keyword}]}


class FakeFetcher:
    """Maps URL substrings to responses; records requested URLs."""

    def __init__(self, routes: dict[str, bytes]):
        self.routes = routes
        self.requested: list[str] = []

    def __call__(self, url: str) -> bytes:
        self.requested.append(url)
        for fragment, payload in self.routes.items():
            if fragment in url:
                if isinstance(payload, Exception):
                    raise payload
                return payload
        raise OSError(f"no route for {url}")


def make_ir(**button_overrides) -> dict:
    button = {
        "id": "btn-hello",
        "label": "Hello",
        "searchTerm": "hello",
        "symbolId": None,
        "symbolSrc": "",
    }
    button.update(button_overrides)
    return {
        "attribution": "Pictograms author: Sergio Palao. Origin: ARASAAC. License: CC BY-NC-SA. Owner: Government of Aragon.",
        "pages": [{"id": "page-1", "buttons": [button]}],
    }


class SearchSelectionTests(unittest.TestCase):
    def test_exact_keyword_match_beats_first_result(self) -> None:
        fetcher = FakeFetcher(
            {"search/hello": search_payload(picto(2, "hello there"), picto(9, "hello"))}
        )
        self.assertEqual(9, fetch_symbols.search_pictogram("hello", "en", fetcher))

    def test_aac_flag_breaks_ties_and_lowest_id_is_deterministic(self) -> None:
        fetcher = FakeFetcher(
            {"search/hello": search_payload(picto(30, "hello"), picto(20, "hello", aac=True))}
        )
        self.assertEqual(20, fetch_symbols.search_pictogram("hello", "en", fetcher))
        fetcher = FakeFetcher(
            {"search/hello": search_payload(picto(30, "hello"), picto(20, "hello"))}
        )
        self.assertEqual(20, fetch_symbols.search_pictogram("hello", "en", fetcher))

    def test_network_failure_returns_none(self) -> None:
        fetcher = FakeFetcher({})
        self.assertIsNone(fetch_symbols.search_pictogram("hello", "en", fetcher))


class EmbedSymbolsTests(unittest.TestCase):
    def routes(self) -> dict[str, bytes]:
        return {
            "search/hello": search_payload(picto(6522, "hello", aac=True)),
            "6522/6522_300.png": PNG_BYTES,
        }

    def test_embeds_data_uri_and_symbol_id(self) -> None:
        ir = make_ir()
        report = fetch_symbols.embed_symbols(ir, fetcher=FakeFetcher(self.routes()))
        button = ir["pages"][0]["buttons"][0]
        self.assertEqual(6522, button["symbolId"])
        expected = "data:image/png;base64," + base64.b64encode(PNG_BYTES).decode("ascii")
        self.assertEqual(expected, button["symbolSrc"])
        self.assertTrue(report[0]["status"].startswith("ok"))

    def test_ids_only_sets_id_without_image(self) -> None:
        ir = make_ir()
        fetch_symbols.embed_symbols(ir, ids_only=True, fetcher=FakeFetcher(self.routes()))
        button = ir["pages"][0]["buttons"][0]
        self.assertEqual(6522, button["symbolId"])
        self.assertEqual("", button["symbolSrc"])

    def test_ids_only_overwrite_clears_stale_embedded_image(self) -> None:
        ir = make_ir(symbolId=111, symbolSrc="data:image/png;base64,b2xk")
        fetch_symbols.embed_symbols(
            ir,
            ids_only=True,
            overwrite=True,
            fetcher=FakeFetcher(self.routes()),
        )
        button = ir["pages"][0]["buttons"][0]
        self.assertEqual(6522, button["symbolId"])
        self.assertEqual("", button["symbolSrc"])

    def test_existing_symbol_is_not_overwritten_by_default(self) -> None:
        ir = make_ir(symbolId=111)
        fetcher = FakeFetcher(self.routes())
        report = fetch_symbols.embed_symbols(ir, fetcher=fetcher)
        self.assertEqual(111, ir["pages"][0]["buttons"][0]["symbolId"])
        self.assertEqual([], fetcher.requested)
        self.assertIn("skipped", report[0]["status"])

    def test_overwrite_replaces_existing_symbol(self) -> None:
        ir = make_ir(symbolId=111)
        fetch_symbols.embed_symbols(ir, overwrite=True, fetcher=FakeFetcher(self.routes()))
        self.assertEqual(6522, ir["pages"][0]["buttons"][0]["symbolId"])

    def test_image_failure_keeps_symbol_id_and_reports_partial(self) -> None:
        routes = {"search/hello": search_payload(picto(6522, "hello"))}
        ir = make_ir()
        report = fetch_symbols.embed_symbols(ir, fetcher=FakeFetcher(routes))
        button = ir["pages"][0]["buttons"][0]
        self.assertEqual(6522, button["symbolId"])
        self.assertEqual("", button["symbolSrc"])
        self.assertTrue(report[0]["status"].startswith("partial"))

    def test_image_failure_during_overwrite_clears_stale_embedded_image(self) -> None:
        routes = {"search/hello": search_payload(picto(6522, "hello"))}
        ir = make_ir(symbolId=111, symbolSrc="data:image/png;base64,b2xk")
        report = fetch_symbols.embed_symbols(
            ir,
            overwrite=True,
            fetcher=FakeFetcher(routes),
        )
        button = ir["pages"][0]["buttons"][0]
        self.assertEqual(6522, button["symbolId"])
        self.assertEqual("", button["symbolSrc"])
        self.assertTrue(report[0]["status"].startswith("partial"))

    def test_search_miss_keeps_text_fallback(self) -> None:
        routes = {"search/hello": search_payload()}
        ir = make_ir()
        report = fetch_symbols.embed_symbols(ir, fetcher=FakeFetcher(routes))
        self.assertIsNone(ir["pages"][0]["buttons"][0]["symbolId"])
        self.assertTrue(report[0]["status"].startswith("miss"))

    def test_label_used_when_search_term_missing(self) -> None:
        ir = make_ir(searchTerm="")
        fetch_symbols.embed_symbols(ir, fetcher=FakeFetcher(self.routes()))
        self.assertEqual(6522, ir["pages"][0]["buttons"][0]["symbolId"])


class AttributionGuardTests(unittest.TestCase):
    def test_ir_without_arasaac_attribution_is_detected(self) -> None:
        ir = make_ir()
        ir["attribution"] = ""
        self.assertFalse(fetch_symbols.has_attribution(ir))
        self.assertTrue(fetch_symbols.has_attribution(make_ir()))


if __name__ == "__main__":
    unittest.main()
