#!/usr/bin/env python3
"""Fill AAC Board IR buttons with real ARASAAC pictograms.

The generated boards ship with ``searchTerm`` values but empty ``symbolId``/
``symbolSrc`` fields, which leaves them text-only until a teacher sources
symbols by hand. This script closes that gap:

1. For every button with a ``searchTerm`` (or ``label`` fallback) and no
   existing symbol, query the free ARASAAC API
   (``https://api.arasaac.org/api/pictograms/<locale>/search/<term>``).
2. Pick the best pictogram (exact keyword match first, then AAC-flagged
   pictograms, then lowest id for determinism).
3. Set ``symbolId`` and, unless ``--ids-only`` is given, download the PNG and
   embed it into ``symbolSrc`` as a ``data:image/png;base64`` URI so the board
   stays single-file and offline-capable.

The existing renderers already understand both fields: ``render_obf.py`` maps
``symbolId`` to a static ARASAAC URL with a CC BY-NC-SA license block and maps
``symbolSrc`` data URIs to embedded OBF image data; the Open AAC Studio
renderer passes both through.

Licensing: ARASAAC pictograms are CC BY-NC-SA (author Sergio Palao, owner
Government of Aragon). Boards embedding them must keep attribution and must
not be sold. The script refuses to run if the IR has no attribution note.

Usage:
  python3 fetch_arasaac_symbols.py board.ir.json
  python3 fetch_arasaac_symbols.py board.ir.json --out board.symbols.ir.json
  python3 fetch_arasaac_symbols.py board.ir.json --locale en --resolution 300
  python3 fetch_arasaac_symbols.py board.ir.json --ids-only
  python3 fetch_arasaac_symbols.py board.ir.json --cache .arasaac-cache

Network failures never abort the run: affected buttons keep their text
fallback and are listed in the final report.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable

SEARCH_URL = "https://api.arasaac.org/api/pictograms/{locale}/search/{term}"
IMAGE_URL = "https://static.arasaac.org/pictograms/{pid}/{pid}_{resolution}.png"
VALID_RESOLUTIONS = (300, 500, 2500)
USER_AGENT = "agentic-aac-board-maker/0.5 (classroom AAC resource tool)"
TIMEOUT_SECONDS = 20

Fetcher = Callable[[str], bytes]


def default_fetcher(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return response.read()


def normalise_term(term: str) -> str:
    return " ".join(term.strip().lower().split())


def score_pictogram(entry: dict[str, Any], term: str) -> tuple[int, int]:
    """Higher score wins; ties broken by lowest pictogram id (deterministic)."""
    wanted = normalise_term(term)
    keywords = [
        normalise_term(str(keyword.get("keyword", "")))
        for keyword in entry.get("keywords", [])
        if isinstance(keyword, dict)
    ]
    score = 0
    if wanted in keywords:
        score += 2
    if entry.get("aac"):
        score += 1
    return (score, -int(entry.get("_id", 0)))


def search_pictogram(term: str, locale: str, fetcher: Fetcher) -> int | None:
    """Return the best-matching ARASAAC pictogram id for a search term."""
    encoded = urllib.parse.quote(normalise_term(term))
    if not encoded:
        return None
    url = SEARCH_URL.format(locale=locale, term=encoded)
    try:
        payload = json.loads(fetcher(url).decode("utf-8"))
    except (urllib.error.URLError, ValueError, OSError):
        return None
    if not isinstance(payload, list) or not payload:
        return None
    entries = [entry for entry in payload if isinstance(entry, dict) and entry.get("_id")]
    if not entries:
        return None
    best = max(entries, key=lambda entry: score_pictogram(entry, term))
    return int(best["_id"])


def fetch_image(pid: int, resolution: int, fetcher: Fetcher, cache_dir: Path | None) -> bytes | None:
    cache_file = None
    if cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"{pid}_{resolution}.png"
        if cache_file.exists():
            return cache_file.read_bytes()
    try:
        data = fetcher(IMAGE_URL.format(pid=pid, resolution=resolution))
    except (urllib.error.URLError, OSError):
        return None
    if not data:
        return None
    if cache_file is not None:
        cache_file.write_bytes(data)
    return data


def build_data_uri(png_bytes: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii")


def iter_buttons(ir: dict[str, Any]):
    for page in ir.get("pages", []):
        if not isinstance(page, dict):
            continue
        for button in page.get("buttons", []):
            if isinstance(button, dict):
                yield page, button


def button_term(button: dict[str, Any]) -> str:
    return str(button.get("searchTerm") or button.get("label") or "").strip()


def has_symbol(button: dict[str, Any]) -> bool:
    return bool(str(button.get("symbolSrc") or "").strip()) or button.get("symbolId") not in (None, "", 0)


def has_attribution(ir: dict[str, Any]) -> bool:
    text = json.dumps(ir.get("attribution", "")) + json.dumps(ir.get("symbolStrategy", ""))
    return "arasaac" in text.lower()


def embed_symbols(
    ir: dict[str, Any],
    locale: str = "en",
    resolution: int = 300,
    ids_only: bool = False,
    overwrite: bool = False,
    fetcher: Fetcher = default_fetcher,
    cache_dir: Path | None = None,
) -> list[dict[str, str]]:
    """Mutate the IR in place. Returns a per-button report."""
    report: list[dict[str, str]] = []
    for page, button in iter_buttons(ir):
        term = button_term(button)
        entry = {
            "page": str(page.get("id", "?")),
            "button": str(button.get("id", "?")),
            "term": term,
        }
        if not term:
            entry["status"] = "skipped: no searchTerm or label"
            report.append(entry)
            continue
        if has_symbol(button) and not overwrite:
            entry["status"] = "skipped: symbol already set (use --overwrite to replace)"
            report.append(entry)
            continue
        pid = search_pictogram(term, locale, fetcher)
        if pid is None:
            entry["status"] = "miss: no ARASAAC result (text fallback kept)"
            report.append(entry)
            continue
        button["symbolId"] = pid
        entry["symbolId"] = str(pid)
        if ids_only:
            entry["status"] = "ok: symbolId set (no image embedded)"
            report.append(entry)
            continue
        png = fetch_image(pid, resolution, fetcher, cache_dir)
        if png is None:
            entry["status"] = "partial: symbolId set, image download failed (text fallback kept)"
            report.append(entry)
            continue
        button["symbolSrc"] = build_data_uri(png)
        entry["status"] = "ok: symbolId set, image embedded"
        report.append(entry)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ir_path", help="Path to the AAC Board IR JSON file")
    parser.add_argument("--out", help="Output path (default: overwrite the input IR)")
    parser.add_argument("--locale", default="en", help="ARASAAC search locale (default: en)")
    parser.add_argument(
        "--resolution",
        type=int,
        default=300,
        choices=VALID_RESOLUTIONS,
        help="Pictogram resolution: 300 screen, 500 large screen, 2500 print (default: 300)",
    )
    parser.add_argument("--ids-only", action="store_true", help="Set symbolId only; do not embed image data")
    parser.add_argument("--overwrite", action="store_true", help="Replace symbols that are already set")
    parser.add_argument("--cache", help="Directory to cache downloaded pictograms")
    args = parser.parse_args(argv)

    ir_path = Path(args.ir_path)
    try:
        ir = json.loads(ir_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        print(f"ERROR: cannot read IR file: {error}", file=sys.stderr)
        return 1

    if not has_attribution(ir):
        print(
            "ERROR: the IR has no ARASAAC attribution note. Add the required attribution "
            "(author Sergio Palao, owner Government of Aragon, CC BY-NC-SA) to the IR's "
            "attribution/symbolStrategy fields before embedding pictograms.",
            file=sys.stderr,
        )
        return 1

    cache_dir = Path(args.cache) if args.cache else None
    report = embed_symbols(
        ir,
        locale=args.locale,
        resolution=args.resolution,
        ids_only=args.ids_only,
        overwrite=args.overwrite,
        cache_dir=cache_dir,
    )

    out_path = Path(args.out) if args.out else ir_path
    out_path.write_text(json.dumps(ir, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    ok = sum(1 for entry in report if entry["status"].startswith("ok"))
    misses = [entry for entry in report if entry["status"].startswith(("miss", "partial"))]
    for entry in report:
        print(f"[{entry['status']}] page {entry['page']} / {entry['button']} ({entry['term']!r})")
    print(f"\nWrote {out_path} — {ok} symbol(s) resolved, {len(misses)} miss(es).")
    print(
        "Reminder: ARASAAC pictograms are CC BY-NC-SA (Sergio Palao / Government of Aragon). "
        "Keep the attribution visible and do not sell boards that embed them."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
