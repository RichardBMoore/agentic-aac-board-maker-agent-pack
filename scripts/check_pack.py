#!/usr/bin/env python3
"""Run static release checks for the Agentic AAC Board Maker pack."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


def ok(message: str) -> None:
    print(f"PASS: {message}")


def fail(message: str) -> None:
    print(f"FAIL: {message}")


def warn(message: str) -> None:
    print(f"WARN: {message}")


def parse_json(path: Path) -> bool:
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except Exception as error:  # noqa: BLE001 - release checker should report all parse failures.
        fail(f"{path.relative_to(ROOT)} JSON parse failed: {error}")
        return False
    ok(f"{path.relative_to(ROOT)} parses as JSON")
    return True


def check_plugin_manifest() -> bool:
    path = ROOT / ".codex-plugin" / "plugin.json"
    if not path.exists():
        fail(".codex-plugin/plugin.json missing")
        return False
    if not parse_json(path):
        return False
    data = json.loads(path.read_text(encoding="utf-8"))
    required = ["name", "version", "description", "license", "skills", "interface"]
    missing = [field for field in required if not data.get(field)]
    if missing:
        fail(f"plugin.json missing required fields: {', '.join(missing)}")
        return False
    if data.get("skills") != "./skills/":
        fail("plugin.json skills should be './skills/'")
        return False
    ok("plugin manifest has required product fields")
    return True


def parse_frontmatter(text: str) -> dict[str, str] | None:
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return None
    result: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if line and not line.startswith(" ") and ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip()
    return result


def check_skills() -> bool:
    allowed = {"name", "description", "license", "allowed-tools", "metadata"}
    success = True
    for skill_md in sorted(SKILLS.glob("*/SKILL.md")):
        frontmatter = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        if frontmatter is None:
            fail(f"{skill_md.relative_to(ROOT)} missing YAML frontmatter")
            success = False
            continue
        missing = {"name", "description"} - set(frontmatter)
        extra = set(frontmatter) - allowed
        name = frontmatter.get("name", "").strip('"')
        if missing or extra:
            fail(f"{skill_md.relative_to(ROOT)} frontmatter missing={sorted(missing)} extra={sorted(extra)}")
            success = False
        elif not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,62}[a-z0-9]", name):
            fail(f"{skill_md.relative_to(ROOT)} name is not valid hyphen-case: {name}")
            success = False
        else:
            ok(f"{skill_md.parent.name} skill frontmatter")

        openai_yaml = skill_md.parent / "agents" / "openai.yaml"
        if not openai_yaml.exists():
            fail(f"{skill_md.parent.name} missing agents/openai.yaml")
            success = False
        else:
            content = openai_yaml.read_text(encoding="utf-8")
            needed = ["display_name:", "short_description:", "default_prompt:"]
            missing_yaml = [item for item in needed if item not in content]
            if missing_yaml:
                fail(f"{openai_yaml.relative_to(ROOT)} missing {missing_yaml}")
                success = False
            else:
                ok(f"{openai_yaml.relative_to(ROOT)} has UI metadata")
    return success


def check_python_scripts() -> bool:
    success = True
    for script in sorted(list((ROOT / "scripts").glob("*.py")) + list(SKILLS.glob("*/scripts/*.py"))):
        try:
            ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
        except SyntaxError as error:
            fail(f"{script.relative_to(ROOT)} has syntax error: {error}")
            success = False
        else:
            ok(f"{script.relative_to(ROOT)} parses")
    return success


def run_command(args: list[str]) -> bool:
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)
    return result.returncode == 0


def check_ir_pipeline() -> bool:
    ir = SKILLS / "agentic-aac-board-maker" / "templates" / "board-json-skeleton.json"
    validator = SKILLS / "agentic-aac-board-maker" / "scripts" / "validate_board_ir.py"
    renderer = SKILLS / "agentic-aac-board-maker" / "scripts" / "render_open_aac_studio.py"
    if not run_command([sys.executable, str(validator), str(ir)]):
        fail("canonical IR skeleton failed validation")
        return False

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "open-aac-studio.json"
        if not run_command([sys.executable, str(renderer), str(ir), str(out)]):
            fail("Open AAC Studio renderer failed")
            return False
        try:
            data = json.loads(out.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            fail(f"Rendered Open AAC Studio JSON did not parse: {error}")
            return False
        if data.get("app") != "Open AAC Studio" or not data.get("pages"):
            fail("Rendered Open AAC Studio JSON missing app/pages")
            return False
        ok("IR validates and renders to Open AAC Studio JSON")
    return True


def check_json_files() -> bool:
    success = True
    for path in sorted(ROOT.rglob("*.json")):
        if "__pycache__" in path.parts:
            continue
        success = parse_json(path) and success
    return success


def check_eye_gaze_template() -> bool:
    checker = SKILLS / "build-aac-student-supports" / "scripts" / "check_eye_gaze_html.py"
    template = SKILLS / "build-aac-student-supports" / "assets" / "eye-gaze-single-file-template.html"
    if not checker.exists() or not template.exists():
        warn("eye-gaze checker/template not found; skipping")
        return True
    if run_command([sys.executable, str(checker), str(template)]):
        ok("eye-gaze single-file template passes static gaze checks")
        return True
    fail("eye-gaze single-file template failed static gaze checks")
    return False


def check_generated_resource_fixtures() -> bool:
    """Validate every generated proof-of-concept IR and its paired outputs."""
    generated = ROOT / "generated"
    validator = SKILLS / "agentic-aac-board-maker" / "scripts" / "validate_board_ir.py"
    renderer = SKILLS / "agentic-aac-board-maker" / "scripts" / "render_open_aac_studio.py"
    if not generated.exists():
        warn("generated/ folder not found; skipping proof-of-concept fixture checks")
        return True

    ir_files = sorted(generated.glob("*/*.ir.json"))
    if not ir_files:
        fail("generated/ contains no *.ir.json proof-of-concept fixtures")
        return False

    success = True
    for ir in ir_files:
        stem = ir.name.removesuffix(".ir.json")
        rel = ir.relative_to(ROOT)
        expected_outputs = [
            ir.with_name(f"{stem}.open-aac-studio.json"),
            ir.with_name(f"{stem}.html"),
            ir.parent / "README.md",
        ]
        missing_outputs = [path.name for path in expected_outputs if not path.exists()]
        if missing_outputs:
            fail(f"{rel} missing paired outputs: {', '.join(missing_outputs)}")
            success = False
            continue

        if not run_command([sys.executable, str(validator), str(ir)]):
            fail(f"{rel} failed AAC Board IR validation")
            success = False
            continue

        with tempfile.TemporaryDirectory() as tmp:
            rendered = Path(tmp) / "open-aac-studio.json"
            if not run_command([sys.executable, str(renderer), str(ir), str(rendered)]):
                fail(f"{rel} failed Open AAC Studio rendering")
                success = False
                continue
            try:
                data = json.loads(rendered.read_text(encoding="utf-8"))
            except json.JSONDecodeError as error:
                fail(f"{rel} rendered JSON did not parse: {error}")
                success = False
                continue
            pages = data.get("pages") or []
            buttons = sum(len(page.get("buttons", [])) for page in pages if isinstance(page, dict))
            if data.get("app") != "Open AAC Studio" or not pages or buttons == 0:
                fail(f"{rel} rendered output missing app/pages/buttons")
                success = False
                continue
            ok(f"{rel} validates and renders ({len(pages)} page(s), {buttons} button(s))")

    return success


def check_reference_paths() -> bool:
    """Check common backticked local paths in markdown files."""
    success = True
    path_pattern = re.compile(r"`((?:references|templates|scripts|fixtures|assets)/[^`]+|\.\./[^`]+)`")
    for md in sorted(list(ROOT.glob("*.md")) + list(SKILLS.glob("*/*.md")) + list(SKILLS.glob("*/references/*.md"))):
        skill_root = None
        try:
            rel = md.relative_to(SKILLS)
            if len(rel.parts) >= 2:
                skill_root = SKILLS / rel.parts[0]
        except ValueError:
            pass

        for match in path_pattern.finditer(md.read_text(encoding="utf-8")):
            raw = match.group(1)
            if any(token in raw for token in ("<", ">", " ", "|")):
                continue
            if "*" in raw:
                continue

            candidates: list[Path] = []
            if raw.startswith("../"):
                candidates.append((md.parent / raw).resolve())
            else:
                if skill_root is not None:
                    candidates.append((skill_root / raw).resolve())
                candidates.append((md.parent / raw).resolve())
                candidates.append((ROOT / raw).resolve())

            if not any(candidate.exists() for candidate in candidates):
                fail(f"{md.relative_to(ROOT)} references missing path `{raw}`")
                success = False
    if success:
        ok("common markdown reference paths resolve")
    return success


def main() -> int:
    checks = [
        check_plugin_manifest,
        check_skills,
        check_python_scripts,
        check_json_files,
        check_ir_pipeline,
        check_generated_resource_fixtures,
        check_eye_gaze_template,
        check_reference_paths,
    ]
    success = True
    for check in checks:
        success = check() and success
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
