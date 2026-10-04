#!/usr/bin/env python3
"""One-off team review of the house symbol set.

The house word list (references/house-lexicon.json) gives every recurring word
one symbol. Symbols start as "proposed" (chosen by the agent). The team reviews
them once; approved symbols then apply to every board when
apply_house_standards.py is re-run.

  # 1. Make an offline review sheet (proposed symbol first, then alternatives)
  python3 review_house_symbols.py --review-out house-symbol-review.json
  # 2. Open house-symbol-review.html, choose a symbol (or text only) per word,
  #    press "Download decisions", then apply them:
  python3 review_house_symbols.py --apply-review house-symbol-review.decisions.json
  # Or approve proposed symbols the team has already agreed on:
  python3 review_house_symbols.py --approve-proposed help,stop,finished
  # 3. Re-apply house standards to each board and re-render.

Network is only used to fetch alternative candidates and newly chosen images.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import house_standards as hs  # noqa: E402
from fetch_arasaac_symbols import (  # noqa: E402
    build_data_uri,
    default_fetcher,
    fetch_image,
    render_review_html,
    search_candidates,
)

LEXICON_PATH = hs.REFERENCES / "house-lexicon.json"


def lexicon_fingerprint(lexicon: dict[str, Any]) -> str:
    words = {word_id: {"label": entry["label"], "symbol": entry.get("symbol")} for word_id, entry in lexicon["words"].items()}
    return hashlib.sha256(json.dumps(words, sort_keys=True).encode()).hexdigest()


def build_manifest(lexicon: dict[str, Any], limit: int = 4, fetcher=default_fetcher) -> dict[str, Any]:
    entries = []
    for word_id, entry in lexicon["words"].items():
        symbol = entry.get("symbol", {})
        candidates = []
        if symbol.get("id"):
            path = hs.SYMBOL_DIR / f"arasaac-{symbol['id']}.png"
            candidates.append({
                "rank": 0, "symbolId": int(symbol["id"]), "score": 99, "aac": True, "keywords": ["proposed"],
                "imageData": build_data_uri(path.read_bytes()) if path.exists() else "",
            })
        for candidate in search_candidates(entry["searchTerm"], "en", fetcher, limit):
            if candidate["symbolId"] in {item["symbolId"] for item in candidates}:
                continue
            png = fetch_image(candidate["symbolId"], 300, fetcher, None)
            candidate["imageData"] = build_data_uri(png) if png else ""
            candidates.append(candidate)
        entries.append({
            "pageId": "house", "buttonId": word_id, "label": f"{entry['label']} (status: {symbol.get('status', 'none')})",
            "searchTerm": entry["searchTerm"], "currentSymbolId": symbol.get("id"), "candidates": candidates,
            "approvedSymbolId": None, "decisionNote": "",
        })
    return {
        "version": "0.2.0",
        "boardFingerprint": lexicon_fingerprint(lexicon),
        "boardId": "house-symbol-set",
        "locale": "en",
        "instructions": (
            "House symbol review: choose one symbol per word for every board (the first candidate is the current proposal). "
            "Check meaning, recognisability, age-respect and culture. 'Use text only' removes the symbol."
        ),
        "entries": entries,
    }


def save_symbol(symbol_id: int, fetcher=default_fetcher) -> bool:
    path = hs.SYMBOL_DIR / f"arasaac-{symbol_id}.png"
    if path.exists():
        return True
    png = fetch_image(symbol_id, 300, fetcher, None)
    if not png:
        return False
    path.write_bytes(png)
    return True


def apply_decisions(lexicon: dict[str, Any], manifest: dict[str, Any], fetcher=default_fetcher) -> list[str]:
    if manifest.get("boardFingerprint") != lexicon_fingerprint(lexicon):
        return ["error: the review is out of date for this word list; make a new review sheet."]
    report = []
    for decision in manifest.get("entries", []):
        word_id = decision.get("buttonId")
        entry = lexicon["words"].get(word_id)
        if entry is None:
            report.append(f"error: unknown house word {word_id}")
            continue
        approved = decision.get("approvedSymbolId")
        if decision.get("decisionNote") == "text-only":
            entry["symbol"] = {"source": "text-only", "id": None, "status": "none", "note": "Team chose text only."}
            report.append(f"{word_id}: text only")
        elif approved:
            allowed = {int(candidate["symbolId"]) for candidate in decision.get("candidates", [])}
            if int(approved) not in allowed:
                report.append(f"error: {word_id}: chosen symbol was not one of the reviewed candidates")
                continue
            if not save_symbol(int(approved), fetcher):
                report.append(f"error: {word_id}: could not download symbol {approved}")
                continue
            entry["symbol"] = {"source": "ARASAAC", "id": int(approved), "status": "approved"}
            report.append(f"{word_id}: approved symbol {approved}")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--review-out", type=Path, help="Write a review manifest plus an offline HTML review sheet")
    parser.add_argument("--apply-review", type=Path, help="Apply downloaded review decisions to the house word list")
    parser.add_argument("--approve-proposed", help="Comma-separated house word ids whose proposed symbol the team approves")
    args = parser.parse_args(argv)
    lexicon = json.loads(LEXICON_PATH.read_text(encoding="utf-8"))
    if args.review_out:
        manifest = build_manifest(lexicon)
        args.review_out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        args.review_out.with_suffix(".html").write_text(render_review_html(manifest), encoding="utf-8")
        print(f"Wrote {args.review_out} and {args.review_out.with_suffix('.html')}")
        return 0
    if args.apply_review:
        manifest = json.loads(args.apply_review.read_text(encoding="utf-8"))
        report = apply_decisions(lexicon, manifest)
    elif args.approve_proposed:
        report = []
        for word_id in [item.strip() for item in args.approve_proposed.split(",") if item.strip()]:
            symbol = lexicon["words"].get(word_id, {}).get("symbol", {})
            if symbol.get("status") == "proposed" and symbol.get("id"):
                symbol["status"] = "approved"
                report.append(f"{word_id}: approved proposed symbol {symbol['id']}")
            else:
                report.append(f"error: {word_id} has no proposed symbol")
    else:
        parser.error("choose --review-out, --apply-review or --approve-proposed")
        return 2
    LEXICON_PATH.write_text(json.dumps(lexicon, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for line in report:
        print(line)
    print("Re-run apply_house_standards.py on each board, then re-render, so every board uses the reviewed symbols.")
    return 1 if any(line.startswith("error") for line in report) else 0


if __name__ == "__main__":
    raise SystemExit(main())
