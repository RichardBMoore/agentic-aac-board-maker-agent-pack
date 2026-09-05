#!/usr/bin/env python3
"""Evaluate newly generated AAC resource folders against proof fixture expectations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

try:
    from jsonschema import Draft202012Validator
except ModuleNotFoundError:
    Draft202012Validator = None

try:
    from canonicalize_board_ir import canonicalize
    from validate_board_ir import validate as semantic_validate
    from validate_html_parity import validate as parity_validate
except ModuleNotFoundError:  # Supports importlib-based unit tests.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from canonicalize_board_ir import canonicalize
    from validate_board_ir import validate as semantic_validate
    from validate_html_parity import validate as parity_validate


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DEFAULT_MANIFEST = SKILL_DIR / "fixtures" / "proof-of-concept-prompts.json"
SCHEMA_PATH = SKILL_DIR / "references" / "aac-board-ir.schema.json"


def text_blob(ir: dict[str, Any], notes_text: str = "") -> str:
    return (json.dumps(ir, ensure_ascii=False) + "\n" + notes_text).lower()


def buttons(ir: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        button
        for page in ir.get("pages", []) if isinstance(page, dict)
        for button in page.get("buttons", []) if isinstance(button, dict)
    ]


def labels(ir: dict[str, Any]) -> list[str]:
    return [str(button.get("label", "")).lower() for button in buttons(ir)]


def functions(ir: dict[str, Any]) -> set[str]:
    return {str(button.get("function", "")) for button in buttons(ir)}


def action_types(ir: dict[str, Any]) -> set[str]:
    result: set[str] = set()
    for button in buttons(ir):
        for action in button.get("actions", []):
            result.add(str(action.get("type", "")) if isinstance(action, dict) else str(action))
    return result


def contains_label(ir: dict[str, Any], *terms: str) -> bool:
    return any(any(term in label for term in terms) for label in labels(ir))


def check_named(name: str, ir: dict[str, Any], html_text: str, notes_text: str) -> tuple[bool, str]:
    blob = text_blob(ir, notes_text)
    access = ir.get("access", {})
    intended = set(access.get("intended", []))
    named: dict[str, Callable[[], bool]] = {
        "dwell-safe": lambda: bool({"eye-gaze-dwell", "mouse-dwell"} & intended) and bool(access.get("dwellTimeMs")) and max(len(page.get("buttons", [])) for page in ir.get("pages", [])) <= access.get("visibleTargetLimit", 0),
        "large-targets": lambda: int(access.get("minimumTargetSizePx", 0)) >= 120,
        "repair-option": lambda: bool(functions(ir) & {"repair", "refuse", "regulate-rest"}),
        "keyboard-fallback": lambda: "keyboard" in intended,
        "qcia-evidence": lambda: bool(ir.get("evidencePlan") or ir.get("teacherNotes", {}).get("evidence")),
        "safety-language": lambda: "safety" in blob or "supervision" in blob,
        "help-route": lambda: contains_label(ir, "help"),
        "privacy-note": lambda: bool(ir.get("privacy", {}).get("level")) and "privacy" in blob,
        "opinion": lambda: contains_label(ir, "think", "opinion"),
        "because": lambda: contains_label(ir, "because"),
        "rehearse-or-speak": lambda: "speak-message" in action_types(ir) or "rehears" in blob,
        "schedule-order": lambda: "schedule" in blob and bool(access.get("scanOrder")),
        "wait-help-change": lambda: all(contains_label(ir, term) for term in ("wait", "help", "change")),
        "not-full-aac-claim": lambda: "not a replacement" in blob or "not the student’s full" in blob or "not the student's full" in blob,
        "age-respectful": lambda: "age-respectful" in str(ir.get("audience", {}).get("tone", "")),
        "repair-language": lambda: len(functions(ir) & {"repair", "refuse", "regulate-rest", "ask"}) >= 2,
        "privacy-safe": lambda: ir.get("privacy", {}).get("containsSensitiveData") is False,
        "not-behaviour-control": lambda: "behaviour-control" in blob or "behavior-control" in blob or "behaviour control" in blob,
        "scan-order": lambda: bool(access.get("scanOrder")) and "scan" in blob,
        "black-and-white-readable": lambda: "@media print" in html_text and "border" in html_text,
        "partner-wait-confirm": lambda: "wait" in blob and "confirm" in blob,
        "attribution": lambda: bool(ir.get("attribution")),
    }
    check = named.get(name)
    if check is None:
        return False, f"unknown required check '{name}'"
    try:
        passed = bool(check())
    except (TypeError, ValueError, StopIteration):
        passed = False
    return passed, name


def evaluate_fixture(root: Path, fixture: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    folder = root / fixture["id"]
    checks: list[dict[str, Any]] = []

    def record(name: str, passed: bool, detail: str = "") -> None:
        checks.append({"name": name, "passed": passed, "detail": detail})

    if not folder.is_dir():
        record("fixture-folder", False, f"missing {folder}")
        return {"id": fixture["id"], "passed": False, "checks": checks}
    ir_files = sorted(folder.glob("*.ir.json"))
    html_files = sorted(folder.glob("*.html"))
    notes_files = sorted(folder.glob("*teacher*notes*.md"))
    record("one-ir", len(ir_files) == 1, f"found {len(ir_files)}")
    record("html-output", bool(html_files), f"found {len(html_files)}")
    record("teacher-notes", bool(notes_files), f"found {len(notes_files)}")
    if len(ir_files) != 1:
        return {"id": fixture["id"], "passed": False, "checks": checks}
    try:
        raw = json.loads(ir_files[0].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        record("parse-ir", False, str(error))
        return {"id": fixture["id"], "passed": False, "checks": checks}
    if not isinstance(raw, dict):
        record("parse-ir", False, "top-level JSON is not an object")
        return {"id": fixture["id"], "passed": False, "checks": checks}
    ir = canonicalize(raw)
    record("canonical-ir", raw == ir, "fresh output must already be canonical IR 0.4.0")
    if Draft202012Validator is None:
        record("json-schema", False, "install requirements-dev.txt")
    else:
        errors = list(Draft202012Validator(schema).iter_errors(ir))
        record("json-schema", not errors, errors[0].message if errors else "")
    failures, warnings = semantic_validate(ir)
    record("semantic-validator", not failures, "; ".join(failures))
    html_text = html_files[0].read_text(encoding="utf-8") if html_files else ""
    notes_text = "\n".join(path.read_text(encoding="utf-8") for path in notes_files)
    if html_text:
        parity_failures = parity_validate(ir, html_text)
        record("html-ir-parity", not parity_failures, "; ".join(parity_failures))

    expectations = fixture.get("expectations", {})
    board_labels = labels(ir)
    for required in expectations.get("requiredLabels", []):
        record(f"label:{required}", any(required.lower() in label for label in board_labels))
    symbol_buttons = buttons(ir)
    embedded = sum(str(button.get("symbolSrc", "")).startswith("data:image/") for button in symbol_buttons)
    if expectations.get("requiredEmbeddedSymbols") is not None:
        record("embedded-symbol-count", embedded >= expectations["requiredEmbeddedSymbols"])
    for example in expectations.get("messageSequences", []):
        lookup = {button["id"]: button for button in symbol_buttons}
        parts = []
        for button_id in example["buttonIds"]:
            for action in lookup.get(button_id, {}).get("actions", []):
                if action.get("type") == "add-to-message":
                    parts.append(action.get("text") or lookup[button_id].get("spokenText", ""))
        record("message:" + example["expected"], " ".join(parts) == example["expected"])
    realised = functions(ir)
    for required in expectations.get("requiredFunctions", []):
        record(f"function:{required}", required in realised)
    profile_options = expectations.get("accessProfiles", [])
    if profile_options:
        record("access-profile", ir.get("access", {}).get("profile") in profile_options)
    blob = text_blob(ir, notes_text)
    for forbidden in expectations.get("forbiddenPhrases", []):
        record(f"forbidden:{forbidden}", forbidden.lower() not in blob)
    for name in fixture.get("requiredChecks", []):
        passed, detail = check_named(name, ir, html_text, notes_text)
        record(f"fixture:{name}", passed, detail)

    return {"id": fixture["id"], "passed": all(item["passed"] for item in checks), "checks": checks, "warnings": warnings, "symbols": {"total": len(symbol_buttons), "embedded": embedded, "withoutEmbeddedImage": len(symbol_buttons) - embedded}, "unverified": ["real input device", "speech voice", "learner symbol familiarity", "print pagination"]}


def evaluate(root: Path, manifest: dict[str, Any], fixture_ids: set[str] | None = None) -> dict[str, Any]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    fixtures = [fixture for fixture in manifest.get("fixtures", []) if fixture_ids is None or fixture.get("id") in fixture_ids]
    results = [evaluate_fixture(root, fixture, schema) for fixture in fixtures]
    return {"validationScope": "static-structure-only; browser interaction and learner review are separate", "manifestVersion": manifest.get("version"), "candidateRoot": str(root), "passed": bool(results) and all(result["passed"] for result in results), "fixtures": results}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate_root", type=Path, help="Folder containing one subfolder per fixture id")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--fixture", action="append", dest="fixtures", help="Evaluate only this fixture id (repeatable)")
    parser.add_argument("--report", type=Path, help="Write the complete JSON report")
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"FAIL: cannot read fixture manifest: {error}", file=sys.stderr)
        return 1
    report = evaluate(args.candidate_root, manifest, set(args.fixtures) if args.fixtures else None)
    for fixture in report["fixtures"]:
        print(f"{'PASS' if fixture['passed'] else 'FAIL'}: {fixture['id']}")
        for item in fixture["checks"]:
            if not item["passed"]:
                print(f"  FAIL: {item['name']} — {item['detail']}")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {args.report}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
