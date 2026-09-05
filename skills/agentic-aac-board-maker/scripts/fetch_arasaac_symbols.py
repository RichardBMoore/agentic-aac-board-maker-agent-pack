#!/usr/bin/env python3
"""Review ARASAAC candidates and apply only teacher/team-approved pictograms.

The generated boards ship with ``searchTerm`` values but empty ``symbolId``/
``symbolSrc`` fields, which leaves them text-only until a teacher sources
symbols by hand. This script closes that gap:

1. For every button with a ``searchTerm`` (or ``label`` fallback) and no
   existing symbol, query the free ARASAAC API
   (``https://api.arasaac.org/api/pictograms/<locale>/search/<term>``).
2. Write a review manifest and visual contact sheet with several candidates.
3. After a reviewer records ``approvedSymbolId``, set ``symbolId`` and,
   unless ``--ids-only`` is given, download the PNG and
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
  python3 fetch_arasaac_symbols.py board.ir.json --review-out symbol-review.json
  # edit approvedSymbolId values in symbol-review.json, then:
  python3 fetch_arasaac_symbols.py board.ir.json --apply-review symbol-review.json --out board.symbols.ir.json
  # legacy deterministic auto-selection remains available explicitly:
  python3 fetch_arasaac_symbols.py board.ir.json --auto-select
  python3 fetch_arasaac_symbols.py board.ir.json --locale en --resolution 300
  python3 fetch_arasaac_symbols.py board.ir.json --ids-only
  python3 fetch_arasaac_symbols.py board.ir.json --cache .arasaac-cache

Network failures never abort the run: affected buttons keep their text
fallback and are listed in the final report.
"""

from __future__ import annotations

import argparse
import base64
import html
import hashlib
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
USER_AGENT = "agentic-aac-board-maker/0.6 (classroom AAC resource tool)"
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


def search_candidates(term: str, locale: str, fetcher: Fetcher, limit: int = 5) -> list[dict[str, Any]]:
    """Return ranked candidate metadata for human symbol review."""
    encoded = urllib.parse.quote(normalise_term(term))
    if not encoded:
        return []
    url = SEARCH_URL.format(locale=locale, term=encoded)
    try:
        payload = json.loads(fetcher(url).decode("utf-8"))
    except (urllib.error.URLError, ValueError, OSError):
        return []
    if not isinstance(payload, list):
        return []
    entries = [entry for entry in payload if isinstance(entry, dict) and entry.get("_id")]
    entries.sort(key=lambda entry: score_pictogram(entry, term), reverse=True)
    candidates: list[dict[str, Any]] = []
    for rank, entry in enumerate(entries[: max(1, limit)], start=1):
        pid = int(entry["_id"])
        candidates.append(
            {
                "rank": rank,
                "symbolId": pid,
                "score": score_pictogram(entry, term)[0],
                "aac": bool(entry.get("aac")),
                "keywords": [
                    str(keyword.get("keyword", ""))
                    for keyword in entry.get("keywords", [])
                    if isinstance(keyword, dict) and keyword.get("keyword")
                ],
                "imageUrl": IMAGE_URL.format(pid=pid, resolution=300),
            }
        )
    return candidates


def search_pictogram(term: str, locale: str, fetcher: Fetcher) -> int | None:
    """Return the best-matching ARASAAC pictogram id for a search term."""
    candidates = search_candidates(term, locale, fetcher, limit=1)
    return int(candidates[0]["symbolId"]) if candidates else None


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


def board_fingerprint(ir: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(ir, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def build_review_manifest(
    ir: dict[str, Any], locale: str = "en", limit: int = 5, fetcher: Fetcher = default_fetcher
) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for page, button in iter_buttons(ir):
        term = button_term(button)
        entries.append(
            {
                "pageId": str(page.get("id", "?")),
                "buttonId": str(button.get("id", "?")),
                "label": str(button.get("label", "")),
                "searchTerm": term,
                "currentSymbolId": button.get("symbolId"),
                "candidates": search_candidates(term, locale, fetcher, limit) if term else [],
                "approvedSymbolId": None,
                "decisionNote": "",
            }
        )
    for entry in entries:
        for candidate in entry["candidates"]:
            png = fetch_image(candidate["symbolId"], 300, fetcher, None)
            candidate["imageData"] = build_data_uri(png) if png else ""
    return {
        "version": "0.2.0",
        "boardFingerprint": board_fingerprint(ir),
        "boardId": str(ir.get("id", "aac-board")),
        "locale": locale,
        "instructions": "Set approvedSymbolId to one listed candidate only after checking meaning, recognisability, culture and student familiarity. Leave null to keep text fallback.",
        "entries": entries,
    }


def render_review_html(manifest: dict[str, Any]) -> str:
    cards: list[str] = []
    for index, entry in enumerate(manifest.get("entries", [])):
        candidates = "".join(
            (
                f'<label class="candidate"><input type="radio" name="entry-{index}" value="{candidate["symbolId"]}" {"disabled" if not candidate.get("imageData") else ""}>'
                f'<img src="{html.escape(str(candidate.get("imageData") or ""), quote=True)}" alt="Candidate ARASAAC symbol {candidate["symbolId"]}">'
                f'<span class="caption">ID {candidate["symbolId"]} · score {candidate["score"]}<br>{html.escape(", ".join(candidate["keywords"][:5]))}</span>'
                '</label>'
            )
            for candidate in entry.get("candidates", [])
        ) or "<p>No candidates found; keep the text fallback or revise the search term.</p>"
        cards.append(
            '<section class="entry">'
            f'<h2>{html.escape(entry.get("label", ""))}</h2>'
            f'<p>Page/button: <code>{html.escape(entry.get("pageId", ""))} / {html.escape(entry.get("buttonId", ""))}</code> · search: <strong>{html.escape(entry.get("searchTerm", ""))}</strong></p>'
            f'<div><label><input type="radio" name="entry-{index}" value="keep" checked>Keep current / pending</label> <label><input type="radio" name="entry-{index}" value="none">None fits — keep current</label> <label><input type="radio" name="entry-{index}" value="text">Use text only</label></div><div class="candidates">{candidates}</div></section>'
        )
    payload = json.dumps(manifest, ensure_ascii=False).replace("<", "\\u003c")
    review_script = r"""const review=JSON.parse(document.getElementById('review-data').textContent);
    document.getElementById('download').onclick=()=>{
      review.entries.forEach((entry,index)=>{
        const value=document.querySelector('input[name="entry-'+index+'"]:checked').value;
        entry.approvedSymbolId=/^\d+$/.test(value)?Number(value):null;
        entry.decisionNote=value==='text'?'text-only':value==='none'?'none-fits':value==='keep'?'keep-current':'approved';
      });
      const url=URL.createObjectURL(new Blob([JSON.stringify(review,null,2)],{type:'application/json'}));
      const a=document.createElement('a');a.href=url;a.download='symbol-review.decisions.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    };"""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Symbol candidate review — {html.escape(str(manifest.get('boardId', 'board')))}</title><style>body{{font-family:Arial,sans-serif;max-width:1400px;margin:auto;padding:24px;color:#17212b}}.entry{{border-top:3px solid #17212b;padding:18px 0}}.candidates{{display:flex;flex-wrap:wrap;gap:18px}}.candidate{{width:180px;margin:0;padding:10px;border:2px solid #64727f;border-radius:10px}}img{{display:block;width:160px;height:160px;object-fit:contain}} .caption{{display:block;margin-top:8px}}@media print{{.entry{{break-inside:avoid}}}}</style></head><body><h1>Symbol candidate review</h1><p>{html.escape(str(manifest.get('instructions', '')))}</p>{''.join(cards)}<footer><p>Review sheet only; available previews are embedded for offline use. Missing previews must not be approved. Pictograms: Sergio Palao / Government of Aragon, CC BY-NC-SA.</p></footer><button id="download" type="button">Download decisions</button><script id="review-data" type="application/json">{payload}</script><script>{review_script}</script></body></html>"""


def apply_review(
    ir: dict[str, Any],
    manifest: dict[str, Any],
    resolution: int = 300,
    ids_only: bool = False,
    fetcher: Fetcher = default_fetcher,
    cache_dir: Path | None = None,
) -> list[dict[str, str]]:
    if manifest.get("boardFingerprint") != board_fingerprint(ir):
        return [{"page": "", "button": "", "term": "", "status": "error: stale or unbound review; regenerate for this board revision"}]
    button_map = {(str(page.get("id")), str(button.get("id"))): button for page, button in iter_buttons(ir)}
    report: list[dict[str, str]] = []
    for entry in manifest.get("entries", []):
        key = (str(entry.get("pageId")), str(entry.get("buttonId")))
        status = {"page": key[0], "button": key[1], "term": str(entry.get("searchTerm", ""))}
        button = button_map.get(key)
        if button is None:
            status["status"] = "error: button is not present in this IR"
            report.append(status)
            continue
        approved = entry.get("approvedSymbolId")
        if approved in (None, "", 0):
            if entry.get("decisionNote") == "text-only":
                button["symbolId"], button["symbolSrc"] = None, ""
            status["status"] = "skipped: no candidate approved (text fallback kept)"
            report.append(status)
            continue
        allowed = {int(candidate["symbolId"]) for candidate in entry.get("candidates", [])}
        try:
            pid = int(approved)
        except (TypeError, ValueError):
            pid = 0
        if pid not in allowed:
            status["status"] = "error: approvedSymbolId is not one of the reviewed candidates"
            report.append(status)
            continue
        status["symbolId"] = str(pid)
        if ids_only:
            button["symbolId"], button["symbolSrc"] = pid, ""
            status["status"] = "ok: approved symbolId set (no image embedded)"
        else:
            png = fetch_image(pid, resolution, fetcher, cache_dir)
            if png is None:
                status["status"] = "partial: image download failed; previous symbol retained"
            else:
                button["symbolId"] = pid
                button["symbolSrc"] = build_data_uri(png)
                status["status"] = "ok: approved symbol embedded"
        report.append(status)
    return report


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
            button["symbolSrc"] = ""
            entry["status"] = "ok: symbolId set (no image embedded)"
            report.append(entry)
            continue
        png = fetch_image(pid, resolution, fetcher, cache_dir)
        if png is None:
            button["symbolSrc"] = ""
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
    parser.add_argument("--review-out", help="Write candidate review JSON and companion HTML without changing the IR")
    parser.add_argument("--apply-review", help="Apply approvedSymbolId choices from a review JSON file")
    parser.add_argument("--candidate-limit", type=int, default=5, help="Candidates per button in review mode (default: 5)")
    parser.add_argument("--auto-select", action="store_true", help="Explicitly use deterministic top-candidate selection without human review")
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
    if args.review_out and args.apply_review:
        print("ERROR: choose --review-out or --apply-review, not both.", file=sys.stderr)
        return 1
    if not args.review_out and not args.apply_review and not args.auto_select:
        print("ERROR: choose review-first --review-out, --apply-review, or explicit --auto-select.", file=sys.stderr)
        return 1
    if args.review_out:
        manifest = build_review_manifest(ir, locale=args.locale, limit=args.candidate_limit)
        review_path = Path(args.review_out)
        review_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        html_path = review_path.with_suffix(".html")
        html_path.write_text(render_review_html(manifest), encoding="utf-8")
        print(f"Wrote candidate review: {review_path}")
        print(f"Wrote visual contact sheet: {html_path}")
        print("No board symbols were changed. Record approvedSymbolId choices, then run --apply-review.")
        return 0
    if args.apply_review:
        try:
            manifest = json.loads(Path(args.apply_review).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            print(f"ERROR: cannot read review manifest: {error}", file=sys.stderr)
            return 1
        report = apply_review(ir, manifest, resolution=args.resolution, ids_only=args.ids_only, cache_dir=cache_dir)
    else:
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
    misses = [entry for entry in report if entry["status"].startswith(("miss", "partial", "error"))]
    for entry in report:
        print(f"[{entry['status']}] page {entry['page']} / {entry['button']} ({entry['term']!r})")
    print(f"\nWrote {out_path} — {ok} approved/resolved symbol(s), {len(misses)} unresolved/error item(s).")
    print(
        "Reminder: ARASAAC pictograms are CC BY-NC-SA (Sergio Palao / Government of Aragon). "
        "Keep the attribution visible and do not sell boards that embed them."
    )
    return 1 if any(entry["status"].startswith("error") for entry in report) else 0


if __name__ == "__main__":
    raise SystemExit(main())
