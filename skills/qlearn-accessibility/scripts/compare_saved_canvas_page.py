#!/usr/bin/env python3
"""Check what survived when QLearn/Canvas saved a page.

Canvas sanitises page HTML on save. After creating an unpublished copy, read
the page back from QLearn and compare:

    python3 compare_saved_canvas_page.py sent.html saved.html --source original.html

It reports, in plain language:

- content lost: words, links, images (with alt text), media, headings, tables;
- styling Canvas removed (style properties that were sent but not saved);
- attributes Canvas removed or renamed.

Exit 0 when every word, link, image and media reference survived (style losses
are warnings); 2 when content is missing, so the copy must not be treated as
validated; 1 when it could not run.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse

try:
    import render_canvas_safe as canvas_safe
except ModuleNotFoundError:  # Supports importlib-based unit tests.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import render_canvas_safe as canvas_safe

QLEARN_HOSTS = {"qlearn.eq.edu.au", "qed09.instructure.com"}
IGNORED_QUERY = {"wrap", "verifier", "download_frd"}


def normalise_url(value: str, hosts: set[str] = QLEARN_HOSTS) -> str:
    """Compare links the way Canvas stores them (host-relative file links, extra wrap/verifier params)."""
    parsed = urlparse(value.strip())
    path = parsed.path
    if parsed.netloc and parsed.netloc.lower() not in hosts:
        path = f"{parsed.scheme}://{parsed.netloc.lower()}{parsed.path}"
    query = urlencode(sorted((key, val) for key, val in parse_qsl(parsed.query) if key not in IGNORED_QUERY))
    return path + (f"?{query}" if query else "") + (f"#{parsed.fragment}" if parsed.fragment else "")


def style_properties(root: canvas_safe.Element) -> Counter:
    counter: Counter = Counter()
    for element in root.iter():
        for name, _ in canvas_safe.parse_style(element.get("style")):
            counter[(element.tag, name)] += 1
    return counter


def attributes(root: canvas_safe.Element) -> Counter:
    counter: Counter = Counter()
    for element in root.iter():
        for name, _ in element.attrs:
            if name != "style":
                counter[(element.tag, name)] += 1
    return counter


def content_inventory(root: canvas_safe.Element, hosts: set[str]) -> dict:
    inv = canvas_safe.inventory(root)
    return {
        "words": Counter(canvas_safe.visible_words(root)),
        "links": Counter(normalise_url(href, hosts) for href in inv["links"]),
        "images": Counter((normalise_url(image["src"] or "", hosts), image["alt"]) for image in inv["images"]),
        "media": Counter(normalise_url(src, hosts) for src in inv["media"]),
        "headings": Counter(inv["headings"]),
        "tables": inv["tables"],
    }


def compare(expected_html: str, saved_html: str, hosts: set[str] = QLEARN_HOSTS) -> dict:
    expected = canvas_safe.parse(expected_html)
    saved = canvas_safe.parse(saved_html)
    want, got = content_inventory(expected, hosts), content_inventory(saved, hosts)
    lost = {
        "words": sorted((want["words"] - got["words"]).elements()),
        "links": sorted((want["links"] - got["links"]).elements()),
        "images": [{"src": src, "alt": alt} for src, alt in (want["images"] - got["images"]).elements()],
        "media": sorted((want["media"] - got["media"]).elements()),
        "headings": sorted((want["headings"] - got["headings"]).elements()),
        "tables": max(0, want["tables"] - got["tables"]),
    }
    added_words = sorted((got["words"] - want["words"]).elements())
    sent_styles, saved_styles = style_properties(expected), style_properties(saved)
    styles_removed = sorted(f"{name} on <{tag}> (x{count})" for (tag, name), count in (sent_styles - saved_styles).items())
    sent_attrs, saved_attrs = attributes(expected), attributes(saved)
    attrs_removed = sorted(f"{name}= on <{tag}> (x{count})" for (tag, name), count in (sent_attrs - saved_attrs).items())
    content_lost = any(lost[key] for key in ("words", "links", "images", "media", "headings")) or lost["tables"] > 0
    return {
        "contentIntact": not content_lost,
        "lost": lost,
        "addedWords": added_words,
        "stylesRemoved": styles_removed,
        "attributesRemoved": attrs_removed,
    }


def print_summary(label: str, result: dict) -> None:
    if result["contentIntact"]:
        print(f"PASS: {label}: every word, link, image, media item, heading and table survived")
    else:
        lost = result["lost"]
        for key in ("words", "links", "images", "media", "headings"):
            if lost[key]:
                print(f"FAIL: {label}: {len(lost[key])} {key} missing: {lost[key][:8]}")
        if lost["tables"]:
            print(f"FAIL: {label}: {lost['tables']} table(s) missing")
    if result["addedWords"]:
        print(f"NOTE: {label}: words present in the saved page but not sent: {result['addedWords'][:8]}")
    for item in result["stylesRemoved"]:
        print(f"WARN: {label}: QLearn removed style {item}")
    for item in result["attributesRemoved"]:
        print(f"WARN: {label}: QLearn removed attribute {item}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare the HTML sent to QLearn with the HTML it saved.")
    parser.add_argument("sent", type=Path, help="HTML that was sent (for example render_canvas_safe.py output)")
    parser.add_argument("saved", type=Path, help="page body read back from QLearn after saving")
    parser.add_argument("--source", type=Path, help="the original page body, to check nothing from it was lost end to end")
    parser.add_argument("--host", action="append", default=[], help="extra QLearn host name to treat as the same site")
    parser.add_argument("--report", type=Path, help="write a JSON report here")
    args = parser.parse_args(argv)
    hosts = QLEARN_HOSTS | {host.lower() for host in args.host}
    try:
        sent, saved = args.sent.read_text(encoding="utf-8"), args.saved.read_text(encoding="utf-8")
        report = {"sentVsSaved": compare(sent, saved, hosts)}
        if args.source:
            report["sourceVsSaved"] = compare(args.source.read_text(encoding="utf-8"), saved, hosts)
            # Style differences against the raw source are expected (that is the restyle); only content matters there.
            report["sourceVsSaved"]["stylesRemoved"] = []
            report["sourceVsSaved"]["attributesRemoved"] = []
    except OSError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print_summary("sent → saved", report["sentVsSaved"])
    if "sourceVsSaved" in report:
        print_summary("original → saved", report["sourceVsSaved"])
    if args.report:
        args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=list) + "\n", encoding="utf-8")
    intact = all(part["contentIntact"] for part in report.values())
    print("RESULT: " + ("content intact — ready for teacher review in QLearn" if intact else "content missing — do not treat this copy as validated"))
    return 0 if intact else 2


if __name__ == "__main__":
    sys.exit(main())
