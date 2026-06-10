#!/usr/bin/env python3
"""Run static release checks for the Agentic AAC Board Maker pack."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import ast
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


class ElementCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: list[tuple[str, dict[str, str]]] = []
        # (aria-label, visible label-span text) per button, for Label-in-Name checks.
        self.button_labels: list[tuple[str, str]] = []
        self._button_attrs: dict[str, str] | None = None
        self._button_label_parts: list[str] = []
        self._in_label_span = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {name.lower(): value or "" for name, value in attrs}
        self.elements.append((tag.lower(), attr_map))
        if tag.lower() == "button":
            self._button_attrs = attr_map
            self._button_label_parts = []
        elif tag.lower() == "span" and self._button_attrs is not None:
            if "label" in attr_map.get("class", "").split():
                self._in_label_span += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "span" and self._in_label_span:
            self._in_label_span -= 1
        elif tag.lower() == "button" and self._button_attrs is not None:
            self.button_labels.append(
                (self._button_attrs.get("aria-label", ""), " ".join(self._button_label_parts).strip())
            )
            self._button_attrs = None

    def handle_data(self, data: str) -> None:
        if self._in_label_span and data.strip():
            self._button_label_parts.append(data.strip())

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)


def find_css_block(css: str, selector: str) -> str:
    match = re.search(re.escape(selector) + r"\s*\{(?P<body>.*?)\}", css, re.DOTALL)
    return match.group("body") if match else ""


def resolve_css_px(css: str, block: str, property_name: str) -> int | None:
    match = re.search(property_name + r"\s*:\s*(?P<value>[^;}]+)", block)
    if not match:
        return None
    value = match.group("value").strip()
    direct = re.match(r"(?P<px>\d+)px$", value)
    if direct:
        return int(direct.group("px"))
    var_match = re.match(r"var\((?P<name>--[a-zA-Z0-9_-]+)\)$", value)
    if not var_match:
        return None
    variable = re.search(re.escape(var_match.group("name")) + r"\s*:\s*(?P<px>\d+)px", css)
    if not variable:
        return None
    return int(variable.group("px"))


def normalise_label_text(value: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", "", value.lower()).strip()


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
    # Spec note: Codex only hard-requires `name` in .codex-plugin/plugin.json;
    # the other requirements below are house rules for this pack. The Codex
    # interface block also caps defaultPrompt at 3 entries of <=128 chars each
    # (excess is warn-dropped by the Codex parser).
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
    prompts = data.get("interface", {}).get("defaultPrompt") or []
    if isinstance(prompts, str):
        prompts = [prompts]
    if len(prompts) > 3 or any(len(prompt) > 128 for prompt in prompts):
        fail("plugin.json interface.defaultPrompt exceeds Codex limits (max 3 prompts of 128 chars)")
        return False
    ok("plugin manifest has required product fields")

    # Claude Code only reads .claude-plugin/plugin.json (Codex reads both),
    # so the dual-platform pack must ship the Claude manifest too.
    claude_path = ROOT / ".claude-plugin" / "plugin.json"
    if not claude_path.exists():
        fail(".claude-plugin/plugin.json missing (required for Claude Code plugin install)")
        return False
    if not parse_json(claude_path):
        return False
    claude_data = json.loads(claude_path.read_text(encoding="utf-8"))
    if claude_data.get("name") != data.get("name"):
        fail(".claude-plugin/plugin.json name does not match .codex-plugin/plugin.json")
        return False
    if "interface" in claude_data:
        fail(".claude-plugin/plugin.json must not carry the Codex-only interface block")
        return False
    ok("Claude plugin manifest present and consistent")
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
        description = frontmatter.get("description", "").strip('"')
        if missing or extra:
            fail(f"{skill_md.relative_to(ROOT)} frontmatter missing={sorted(missing)} extra={sorted(extra)}")
            success = False
        elif not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,62}[a-z0-9]", name):
            fail(f"{skill_md.relative_to(ROOT)} name is not valid hyphen-case: {name}")
            success = False
        elif len(name) > 64:
            # Codex hard-fails skills whose name exceeds 64 chars.
            fail(f"{skill_md.relative_to(ROOT)} name exceeds Codex's 64-char limit")
            success = False
        elif len(description) > 1024:
            # Codex hard-fails skills whose description exceeds 1024 chars.
            fail(f"{skill_md.relative_to(ROOT)} description exceeds Codex's 1024-char limit ({len(description)} chars)")
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


def is_external(value: str) -> bool:
    if not value or value.startswith(("#", "data:", "blob:", "about:")):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} or value.startswith("//")


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


def normalise_export(data: dict) -> dict:
    """Drop the render timestamps so shipped exports can be diffed against a re-render."""
    cleaned = dict(data)
    cleaned.pop("created", None)
    cleaned.pop("modified", None)
    return cleaned


def check_generated_resource_fixtures() -> bool:
    """Validate every generated proof-of-concept IR and its paired outputs."""
    generated = ROOT / "generated"
    validator = SKILLS / "agentic-aac-board-maker" / "scripts" / "validate_board_ir.py"
    renderer = SKILLS / "agentic-aac-board-maker" / "scripts" / "render_open_aac_studio.py"
    obf_renderer = SKILLS / "agentic-aac-board-maker" / "scripts" / "render_obf.py"
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
        shipped_export = ir.with_name(f"{stem}.open-aac-studio.json")
        expected_outputs = [
            shipped_export,
            ir.with_name(f"{stem}.html"),
            ir.parent / "README.md",
            ir.parent / "teacher-notes.md",
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

        ir_data = json.loads(ir.read_text(encoding="utf-8"))
        page_count = len(ir_data.get("pages") or [])
        obf_suffix = ".obf" if page_count == 1 else ".obz"
        shipped_obf = ir.with_name(f"{stem}{obf_suffix}")

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

            # The shipped export must match a fresh render (timestamps aside),
            # so committed exports cannot silently drift from their IRs.
            shipped_data = json.loads(shipped_export.read_text(encoding="utf-8"))
            if normalise_export(shipped_data) != normalise_export(data):
                fail(f"{shipped_export.relative_to(ROOT)} has drifted from its IR; re-run render_open_aac_studio.py")
                success = False
                continue

            # Open Board Format export keeps boards importable into mainstream
            # AAC apps (CoughDrop, AsTeRICS Grid, OptiKey, Cboard).
            if not shipped_obf.exists():
                fail(f"{rel} missing paired Open Board Format output: {shipped_obf.name}")
                success = False
                continue
            rendered_obf = Path(tmp) / f"render{obf_suffix}"
            if not run_command([sys.executable, str(obf_renderer), str(ir), str(rendered_obf)]):
                fail(f"{rel} failed Open Board Format rendering")
                success = False
                continue
            if obf_suffix == ".obf":
                obf_match = json.loads(rendered_obf.read_text(encoding="utf-8")) == json.loads(
                    shipped_obf.read_text(encoding="utf-8")
                )
            else:
                import zipfile

                with zipfile.ZipFile(rendered_obf) as fresh, zipfile.ZipFile(shipped_obf) as shipped:
                    fresh_entries = {name: fresh.read(name) for name in sorted(fresh.namelist())}
                    shipped_entries = {name: shipped.read(name) for name in sorted(shipped.namelist())}
                obf_match = fresh_entries == shipped_entries
            if not obf_match:
                fail(f"{shipped_obf.relative_to(ROOT)} has drifted from its IR; re-run render_obf.py")
                success = False
                continue

            ok(f"{rel} validates and renders ({len(pages)} page(s), {buttons} button(s), OBF in sync)")

    return success


def check_generated_html_accessibility() -> bool:
    """Run static access/offline checks against generated HTML fixtures."""
    success = True
    html_files = sorted((ROOT / "generated").glob("*/*.html"))
    if not html_files:
        warn("generated/ contains no HTML fixtures; skipping HTML accessibility checks")
        return True

    for html_file in html_files:
        rel = html_file.relative_to(ROOT)
        text = html_file.read_text(encoding="utf-8")
        lower = text.lower()
        collector = ElementCollector()
        collector.feed(text)

        elements = collector.elements
        html_attrs = next((attrs for tag, attrs in elements if tag == "html"), {})
        buttons = [attrs for tag, attrs in elements if tag == "button"]
        external_assets = [
            f"{tag}[{attr}]={attrs[attr]}"
            for tag, attrs in elements
            for attr in ("src", "href", "poster")
            if is_external(attrs.get(attr, ""))
        ]

        local_ok = True
        if html_attrs.get("lang") != "en-AU":
            fail(f"{rel} should declare <html lang=\"en-AU\">")
            local_ok = False
        if "name=\"viewport\"" not in lower and "name='viewport'" not in lower:
            fail(f"{rel} missing viewport meta")
            local_ok = False
        if not buttons:
            fail(f"{rel} has no semantic button elements")
            local_ok = False
        missing_labels = [attrs for attrs in buttons if not attrs.get("aria-label") and not attrs.get("aria-labelledby")]
        if missing_labels:
            fail(f"{rel} has {len(missing_labels)} button(s) without aria-label/aria-labelledby")
            local_ok = False
        # WCAG 2.5.3 Label in Name: an aria-label must contain the visible label
        # text so speech-input users can say what they see.
        label_mismatches = [
            (aria, visible)
            for aria, visible in collector.button_labels
            if aria and visible and normalise_label_text(visible) not in normalise_label_text(aria)
        ]
        if label_mismatches:
            aria, visible = label_mismatches[0]
            fail(f"{rel} has {len(label_mismatches)} button(s) whose aria-label omits the visible text (e.g. '{visible}' vs '{aria}')")
            local_ok = False
        # Native buttons activated via click listeners are keyboard-operable
        # (Enter/Space fire click); custom keydown Enter handling also counts.
        has_click_activation = "addEventListener('click'" in text or 'addEventListener("click"' in text or "onclick" in lower
        has_keydown_activation = "keydown" in text and "Enter" in text
        if not has_click_activation and not has_keydown_activation:
            fail(f"{rel} missing obvious keyboard activation handling")
            local_ok = False
        if "aria-live" not in text and "role=\"status\"" not in lower and "role='status'" not in lower:
            fail(f"{rel} missing aria-live/status feedback")
            local_ok = False
        if "ARASAAC" not in text:
            fail(f"{rel} missing ARASAAC/text-fallback attribution note")
            local_ok = False
        if "@media print" not in text:
            fail(f"{rel} missing print stylesheet")
            local_ok = False
        if external_assets:
            fail(f"{rel} has external assets: {', '.join(external_assets[:5])}")
            local_ok = False
        if "dwell" in lower:
            if "pointerenter" not in text and "mouseenter" not in text:
                fail(f"{rel} mentions dwell but has no pointer/mouse enter handler")
                local_ok = False
            if "pointerleave" not in text and "mouseleave" not in text and "blur" not in text:
                fail(f"{rel} mentions dwell but has no cancellation handler")
                local_ok = False
            css = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", text, flags=re.DOTALL | re.IGNORECASE))
            dwell_block = find_css_block(css, ".dwell-btn")
            min_width = resolve_css_px(css, dwell_block, "min-width") if dwell_block else None
            min_height = resolve_css_px(css, dwell_block, "min-height") if dwell_block else None
            if min_width is None or min_height is None:
                fail(f"{rel} dwell target min-width/min-height is not statically resolvable from .dwell-btn CSS")
                local_ok = False
            elif min_width < 120 or min_height < 120:
                fail(f"{rel} dwell targets are {min_width}x{min_height}px; gaze targets need at least 120px")
                local_ok = False
            # Dwell resources must also pass the strict eye-gaze checker, so the
            # documented release gate and the enforced one stay in agreement.
            checker = SKILLS / "build-aac-student-supports" / "scripts" / "check_eye_gaze_html.py"
            if checker.exists() and not run_command([sys.executable, str(checker), str(html_file)]):
                fail(f"{rel} failed the eye-gaze HTML checker")
                local_ok = False

        if local_ok:
            ok(f"{rel} static HTML accessibility/offline checks")
        success = local_ok and success
    return success


def check_reference_paths() -> bool:
    """Check common backticked local paths in markdown files."""
    success = True
    path_pattern = re.compile(r"`((?:references|templates|scripts|fixtures|assets)/[^`]+|\.\./[^`]+)`")
    markdown_files = [md for md in ROOT.rglob("*.md") if "__pycache__" not in md.parts and "node_modules" not in md.parts]
    for md in sorted(markdown_files):
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
        check_generated_html_accessibility,
        check_eye_gaze_template,
        check_reference_paths,
    ]
    success = True
    for check in checks:
        success = check() and success
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
