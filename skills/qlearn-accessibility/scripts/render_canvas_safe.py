#!/usr/bin/env python3
"""Turn a QLearn/Canvas page body (or any HTML) into an accessible, Canvas-safe copy.

What it does, without changing the teaching content:

- keeps every visible word, link target, image (with its alt text), table and
  media reference, and proves it with a before/after inventory;
- keeps only what Canvas's HTML editor allowlist keeps (tags, attributes,
  inline ``style`` properties, URL protocols), so nothing silently vanishes on
  save; ``<style>``/``<script>`` blocks and event handlers are removed and
  reported;
- applies a readable house look with inline styles only: larger text and line
  spacing, a comfortable line length, strong headings, underlined links, large
  "button" links where a link stands alone, bordered tables;
- fixes heading order under the page title (Canvas shows the title as H1) and
  replaces source colours that fail WCAG AA contrast;
- reports what a teacher must decide (missing alt text, base64 images,
  "click here" links, embeds Canvas pages drop) instead of guessing.

Exit status 0 = safe to save as an unpublished copy; 2 = needs teacher action
(see "blocking" in the report); 1 = could not run.

    python3 render_canvas_safe.py lesson.html lesson.accessible.html --report lesson.report.json
"""

from __future__ import annotations

import argparse
import html
import json
import re
import string
import sys
from collections import Counter
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

SKILL_DIR = Path(__file__).resolve().parent.parent
STYLES_PATH = SKILL_DIR / "templates" / "canvas-safe-styles.json"
PAGE_TEMPLATE = SKILL_DIR / "templates" / "accessible_canvas_page.html"

# --- Canvas HTML editor allowlist (community.instructure.com KB 387066, checked 2026-10-21) ---
ALLOWED_TAGS = set(
    """a abbr acronym address area article aside audio b bdo big blockquote br caption cite code col colgroup dd del
    details dfn div dl dt em embed figcaption figure font footer h1 h2 h3 h4 h5 h6 header hr i iframe img ins kbd
    legend li map mark nav object ol p param picture pre q rp rt ruby samp section small source span strike strong
    sub summary sup table tbody td tfoot th thead time tr track tt u ul var video""".split()
)
MATHML_TAGS = set(
    """annotation annotation-xml maction maligngroup malignmark math menclose merror mfenced mfrac mglyph mi mlabeledtr
    mlongdiv mmultiscripts mn mo mover mpadded mphantom mprescripts mroot mrow ms mscarries mscarry msgroup msline
    mspace msqrt msrow mstack mstyle msub msubsup msup mtable mtd mtext mtr munder munderover none semantics""".split()
)
PAGE_REMOVED_TAGS = {"object", "embed", "param"}  # allowlisted elsewhere, but Canvas Pages remove them.
GLOBAL_ATTRS = {"style", "class", "id", "title", "role", "lang", "dir"}
ELEMENT_ATTRS = {
    "a": {"href", "target", "name", "rel", "download"},
    "abbr": {"title"},
    "area": {"alt", "coords", "href", "shape", "target"},
    "audio": {"name", "src", "muted", "controls", "allowfullscreen", "allow", "poster", "width", "height", "playsinline"},
    "blockquote": {"cite"},
    "col": {"span", "width"},
    "colgroup": {"span", "width"},
    "del": {"cite", "datetime"},
    "img": {"align", "alt", "height", "src", "title", "usemap", "width", "srcset", "loading", "decoding"},
    "iframe": {"src", "width", "height", "name", "align", "allowfullscreen", "frameborder", "scrolling", "sandbox",
               "loading", "allow", "webkitallowfullscreen", "mozallowfullscreen"},
    "ins": {"cite", "datetime"},
    "map": {"name"},
    "ol": {"start", "type", "reversed"},
    "q": {"cite"},
    "source": {"height", "media", "sizes", "src", "srcset", "type", "width"},
    "table": {"summary", "width", "border", "cellpadding", "cellspacing", "frame"},
    "tr": {"align", "valign", "dir"},
    "track": {"default", "kind", "label", "src", "srclang"},
    "td": {"abbr", "axis", "colspan", "rowspan", "width", "align", "valign", "dir"},
    "th": {"abbr", "colspan", "rowspan", "width", "align", "valign", "dir", "scope"},
    "ul": {"type"},
    "video": {"name", "src", "allowfullscreen", "muted", "poster", "width", "height", "controls", "playsinline", "allow",
              "preload", "loop"},
}
DISALLOWED_IDS = {"body", "length"}
CSS_PROPERTIES = set(
    """clear display float overflow overflow-x overflow-y position visibility z-index zoom bottom left right top
    aspect-ratio box-sizing height max-height max-width min-height min-width object-fit object-position resize width
    column-gap gap margin padding row-gap color direction font font-feature-settings font-kerning font-optical-sizing
    font-variant-caps font-variant-ligatures font-variant-numeric letter-spacing line-height text-align
    text-align-last text-decoration text-indent text-shadow text-transform text-underline-offset unicode-bidi
    vertical-align word-spacing hyphens line-break overflow-wrap tab-size text-combine-upright text-orientation
    text-overflow white-space word-break word-wrap writing-mode background border border-collapse border-radius
    border-spacing box-shadow outline outline-offset caption-side empty-cells list-style table-layout align-content
    align-items align-self flex grid justify-content justify-items justify-self order place-content place-items
    place-self column-count column-fill column-rule column-span column-width columns animation transform transition
    break-after break-before break-inside page-break-after page-break-before page-break-inside content
    counter-increment counter-reset quotes accent-color appearance caret-color cursor opacity pointer-events
    user-select""".split()
)
SANDBOX_TOKENS = {"allow-modals", "allow-orientation-lock", "allow-pointer-lock", "allow-popups",
                  "allow-popups-to-escape-sandbox", "allow-presentation", "allow-same-origin", "allow-scripts",
                  "allow-storage-access-by-user-activation", "allow-top-navigation-by-user-activation",
                  "allow-downloads", "allow-forms"}
URL_PROTOCOLS = {"http", "https", "ftp", "mailto", "tel"}
URL_ATTRS = {"href", "src", "poster", "cite"}

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
DROP_WITH_CONTENT = {"script", "style", "template", "noscript", "head", "title", "meta", "link", "base", "svg", "canvas"}
TAG_RENAMES = {"s": "del", "main": "div", "center": "div"}
CONTENT_FORM_TAGS = {"input", "textarea", "select", "button", "form", "label", "option", "optgroup", "fieldset", "output"}
VAGUE_LINK_TEXT = {"click here", "here", "link", "this link", "read more", "more", "click", "this", "go"}
NAMED_COLOURS = {
    "black": "#000000", "white": "#ffffff", "red": "#ff0000", "green": "#008000", "blue": "#0000ff", "yellow": "#ffff00",
    "orange": "#ffa500", "purple": "#800080", "gray": "#808080", "grey": "#808080", "navy": "#000080", "maroon": "#800000",
    "teal": "#008080", "silver": "#c0c0c0", "lime": "#00ff00", "aqua": "#00ffff", "fuchsia": "#ff00ff", "olive": "#808000",
    "pink": "#ffc0cb", "brown": "#a52a2a", "darkblue": "#00008b", "darkred": "#8b0000", "darkgreen": "#006400",
    "lightgray": "#d3d3d3", "lightgrey": "#d3d3d3", "lightblue": "#add8e6", "lightyellow": "#ffffe0",
}


# --------------------------------------------------------------------------- tiny DOM


@dataclass
class Element:
    tag: str
    attrs: list[tuple[str, str]] = field(default_factory=list)
    children: list["Element | str"] = field(default_factory=list)

    def get(self, name: str, default: str = "") -> str:
        for key, value in self.attrs:
            if key == name:
                return value
        return default

    def set(self, name: str, value: str) -> None:
        for index, (key, _) in enumerate(self.attrs):
            if key == name:
                self.attrs[index] = (name, value)
                return
        self.attrs.append((name, value))

    def remove(self, name: str) -> None:
        self.attrs = [(key, value) for key, value in self.attrs if key != name]

    def iter(self) -> Iterable["Element"]:
        yield self
        for child in self.children:
            if isinstance(child, Element):
                yield from child.iter()

    def text(self) -> str:
        parts: list[str] = []
        for child in self.children:
            parts.append(child if isinstance(child, str) else child.text())
        return "".join(parts)


class TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Element("#root")
        self.stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        element = Element(tag.lower(), [(name.lower(), value if value is not None else "") for name, value in attrs])
        self.stack[-1].children.append(element)
        if element.tag not in VOID:
            self.stack.append(element)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        element = Element(tag.lower(), [(name.lower(), value if value is not None else "") for name, value in attrs])
        self.stack[-1].children.append(element)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        self.stack[-1].children.append(data)


def parse(text: str) -> Element:
    """Parse HTML; for a whole document return the body plus anything a browser would still show after it."""
    builder = TreeBuilder()
    builder.feed(text)
    builder.close()
    root = builder.root

    def is_tag(node: Element | str, name: str) -> bool:
        return isinstance(node, Element) and node.tag == name

    html_element = next((child for child in root.children if is_tag(child, "html")), None)
    container = html_element if html_element is not None else root
    body = next((child for child in container.children if is_tag(child, "body")), None)
    if body is None and html_element is None:
        return root
    nodes: list[Element | str] = []
    for owner in ([html_element] if html_element is not None else []) + [root]:
        for child in owner.children:
            if child is html_element or is_tag(child, "head"):
                continue
            if child is body:
                nodes.extend(body.children)
            else:
                nodes.append(child)
    return Element("#root", children=nodes)


def serialise(node: Element | str) -> str:
    if isinstance(node, str):
        return html.escape(node, quote=False)
    if node.tag == "#root":
        return "".join(serialise(child) for child in node.children)
    attrs = "".join(f' {name}="{html.escape(value, quote=True)}"' if value != "" or name not in BOOLEAN_ATTRS else f" {name}"
                    for name, value in node.attrs)
    if node.tag in VOID:
        return f"<{node.tag}{attrs}>"
    return f"<{node.tag}{attrs}>" + "".join(serialise(child) for child in node.children) + f"</{node.tag}>"


BOOLEAN_ATTRS = {"allowfullscreen", "controls", "muted", "playsinline", "loop", "reversed", "default", "download",
                 "webkitallowfullscreen", "mozallowfullscreen"}


# --------------------------------------------------------------------------- CSS and colour


def parse_style(value: str) -> list[tuple[str, str]]:
    declarations: list[tuple[str, str]] = []
    for chunk in re.split(r";(?![^(]*\))", value or ""):
        if ":" not in chunk:
            continue
        name, raw = chunk.split(":", 1)
        # !important is meaningless inline and would hide values from the checks below.
        name, raw = name.strip().lower(), re.sub(r"\s*!\s*important\s*$", "", raw.strip(), flags=re.IGNORECASE)
        if name and raw:
            declarations.append((name, raw))
    return declarations


def style_text(declarations: list[tuple[str, str]]) -> str:
    return " ".join(f"{name}: {value};" for name, value in declarations)


# Shorthands whose longhands Canvas keeps (margin-top, border-left-color, font-size...). Other
# hyphenated names (content-visibility, text-wrap...) are not on the allowlist.
SHORTHANDS = ("margin", "padding", "border", "background", "font", "text-decoration", "list-style", "outline",
              "flex", "grid", "column-rule", "columns", "animation", "transition", "overflow", "place")


def css_property_allowed(name: str) -> bool:
    if name in CSS_PROPERTIES:
        return True
    return any(name.startswith(prefix + "-") for prefix in SHORTHANDS)


Colour = tuple[float, float, float, float]


def parse_colour(value: str) -> Colour | None:
    value = value.strip().lower()
    if value == "transparent":
        return (0.0, 0.0, 0.0, 0.0)
    value = NAMED_COLOURS.get(value, value)
    match = re.fullmatch(r"#([0-9a-f]{3}|[0-9a-f]{6})", value)
    if match:
        digits = match.group(1)
        if len(digits) == 3:
            digits = "".join(character * 2 for character in digits)
        return (int(digits[0:2], 16) / 255, int(digits[2:4], 16) / 255, int(digits[4:6], 16) / 255, 1.0)
    match = re.fullmatch(r"rgba?\(\s*(\d+)[\s,]+(\d+)[\s,]+(\d+)(?:[\s,/]+([\d.]+)(%?))?\s*\)", value)
    if match:
        alpha = 1.0
        if match.group(4) is not None:
            alpha = float(match.group(4)) / (100 if match.group(5) else 1)
        return (min(int(match.group(1)), 255) / 255, min(int(match.group(2)), 255) / 255,
                min(int(match.group(3)), 255) / 255, max(0.0, min(alpha, 1.0)))
    return None


def blend(colour: Colour, under: Colour) -> Colour:
    alpha = colour[3]
    return (colour[0] * alpha + under[0] * (1 - alpha), colour[1] * alpha + under[1] * (1 - alpha),
            colour[2] * alpha + under[2] * (1 - alpha), 1.0)


def to_hex(colour: Colour) -> str:
    return "#" + "".join(f"{round(channel * 255):02x}" for channel in colour[:3])


def luminance(colour: Colour) -> float:
    def channel(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in colour[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(foreground: str, background: str) -> float | None:
    """Contrast of foreground text over an opaque background; see-through text is blended first."""
    fg, bg = parse_colour(foreground), parse_colour(background)
    if fg is None or bg is None:
        return None
    bg = blend(bg, (1.0, 1.0, 1.0, 1.0))
    fg = blend(fg, bg)
    high, low = sorted((luminance(fg), luminance(bg)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def background_colour(declarations: list[tuple[str, str]]) -> str | None:
    """The element's own background colour token (may be see-through), or None."""
    for name, value in reversed(declarations):
        if name == "background-color" and parse_colour(value):
            return value
        if name == "background":
            for token in re.findall(r"#[0-9a-fA-F]{3,6}\b|rgba?\([^)]*\)|[a-zA-Z]+", value):
                if parse_colour(token):
                    return token
    return None


def resolve_background(token: str | None, inherited: str) -> str:
    """Opaque hex background actually behind the text."""
    under = parse_colour(inherited) or (1.0, 1.0, 1.0, 1.0)
    own = parse_colour(token) if token else None
    return to_hex(blend(own, under)) if own else to_hex(blend(under, (1.0, 1.0, 1.0, 1.0)))


MIN_TEXT_PX = 16


def font_size_px(value: str) -> float | None:
    match = re.match(r"\s*([\d.]+)\s*(px|pt|rem|em|%)\s*$", value)
    if not match:
        named = {"xx-small": 9, "x-small": 10, "small": 13, "smaller": 13, "medium": 16}
        return named.get(value.strip().lower())
    number, unit = float(match.group(1)), match.group(2)
    return number * {"px": 1, "pt": 4 / 3, "rem": 16, "em": 16, "%": 0.16}[unit]


def shorthand_font_size_px(value: str) -> float | None:
    """Size inside a `font:` shorthand such as `italic 11px/1.4 Arial`."""
    match = re.search(r"(?:^|\s)([\d.]+(?:px|pt|rem|em|%))(?:/|\s|$)", value)
    return font_size_px(match.group(1)) if match else None


def is_large_text(declarations: list[tuple[str, str]], tag: str) -> bool:
    if tag in {"h2", "h3", "h4"}:
        return True  # House headings are bold and at least 20px: WCAG "large text".
    for name, value in declarations:
        if name == "font-size":
            size = font_size_px(value)
            if size is not None:
                return size >= 24
    return False


# --------------------------------------------------------------------------- inventory


BLOCK_TAGS = set(
    """address article aside blockquote br caption center dd details div dl dt fieldset figcaption figure footer form
    h1 h2 h3 h4 h5 h6 header hr legend li main nav ol p pre section summary table tbody td tfoot th thead tr ul
    iframe video audio img""".split()
)


def visible_words(root: Element) -> list[str]:
    """Words a reader sees, joining inline runs exactly as a browser would."""
    parts: list[str] = []

    def walk(node: Element | str) -> None:
        if isinstance(node, str):
            parts.append(node)
            return
        if node.tag in DROP_WITH_CONTENT:
            return
        block = node.tag in BLOCK_TAGS
        if block:
            parts.append(" ")
        for child in node.children:
            walk(child)
        if block:
            parts.append(" ")

    walk(root)
    return "".join(parts).split()


def inventory(root: Element) -> dict:
    links, images, media, headings = [], [], [], []
    tables = 0
    header_cells = 0
    for element in root.iter():
        if element.tag == "a" and element.get("href"):
            links.append(element.get("href"))
        elif element.tag == "img":
            images.append({"src": element.get("src"), "alt": element.get("alt", None)})  # type: ignore[arg-type]
        elif element.tag in {"iframe", "video", "audio", "source", "track", "embed", "object"}:
            reference = element.get("src") or element.get("data")
            if reference:
                media.append(reference)
        elif re.fullmatch(r"h[1-6]", element.tag):
            headings.append(" ".join(element.text().split()))
        elif element.tag == "table":
            tables += 1
        elif element.tag == "th":
            header_cells += 1
    return {
        "words": len(visible_words(root)),
        "links": links,
        "images": images,
        "media": media,
        "headings": headings,
        "tables": tables,
        "headerCells": header_cells,
    }


def normalise_word(word: str) -> str:
    return word.strip()


def lost_content(source: Element, output: Element) -> dict[str, list]:
    source_words = Counter(normalise_word(word) for word in visible_words(source))
    output_words = Counter(normalise_word(word) for word in visible_words(output))
    missing_words = sorted((source_words - output_words).elements())
    source_inventory, output_inventory = inventory(source), inventory(output)
    missing_links = sorted((Counter(source_inventory["links"]) - Counter(output_inventory["links"])).elements())
    out_images = Counter((image["src"], image["alt"]) for image in output_inventory["images"])
    missing_images = [image for image in source_inventory["images"] if not out_images[(image["src"], image["alt"])]]
    missing_media = sorted((Counter(source_inventory["media"]) - Counter(output_inventory["media"])).elements())
    return {"words": missing_words, "links": missing_links, "images": missing_images, "media": missing_media}


# --------------------------------------------------------------------------- <style> rules -> inline styles

SIMPLE_SELECTOR = re.compile(r"^(?P<tag>[a-z][a-z0-9]*)?(?P<classes>(?:\.[A-Za-z0-9_-]+)*)(?:#(?P<id>[A-Za-z0-9_-]+))?$")


@dataclass
class CssRule:
    tag: str | None
    classes: tuple[str, ...]
    element_id: str | None
    declarations: list[tuple[str, str]]
    order: int

    @property
    def specificity(self) -> tuple[int, int, int, int]:
        return (1 if self.element_id else 0, len(self.classes), 1 if self.tag else 0, self.order)

    def matches(self, element: Element) -> bool:
        if self.tag and element.tag != self.tag:
            return False
        if self.element_id and element.get("id") != self.element_id:
            return False
        classes = set(element.get("class").split())
        return all(name in classes for name in self.classes)


def strip_at_rules(css: str) -> tuple[str, int]:
    """Remove @media/@font-face/@import blocks (cannot be inlined); return css and how many were removed."""
    out: list[str] = []
    index = 0
    removed = 0
    while index < len(css):
        if css[index] == "@":
            removed += 1
            brace = css.find("{", index)
            semicolon = css.find(";", index)
            if semicolon != -1 and (brace == -1 or semicolon < brace):
                index = semicolon + 1
                continue
            if brace == -1:
                break
            depth = 0
            for position in range(brace, len(css)):
                if css[position] == "{":
                    depth += 1
                elif css[position] == "}":
                    depth -= 1
                    if depth == 0:
                        index = position + 1
                        break
            else:
                index = len(css)
            continue
        out.append(css[index])
        index += 1
    return "".join(out), removed


def parse_css_rules(css: str) -> tuple[list[CssRule], int]:
    """Parse simple rules; return (rules, number of selectors/blocks that could not be inlined)."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    css, skipped = strip_at_rules(css)
    rules: list[CssRule] = []
    for match in re.finditer(r"(?P<selectors>[^{}]+)\{(?P<body>[^{}]*)\}", css):
        declarations = parse_style(match.group("body"))
        for selector in match.group("selectors").split(","):
            selector = selector.strip()
            parsed = SIMPLE_SELECTOR.match(selector)
            if not selector or not parsed or selector in {"html", "body"} or not any(parsed.groups()):
                skipped += 1
                continue
            classes = tuple(name for name in parsed.group("classes").split(".") if name)
            rules.append(CssRule(parsed.group("tag"), classes, parsed.group("id"), declarations, len(rules)))
    return rules, skipped


def collect_style_blocks(root: Element) -> str:
    return "\n".join(element.text() for element in root.iter() if element.tag == "style")


def inline_css_rules(root: Element, rules: list[CssRule]) -> int:
    """Copy matching rule declarations into each element's style attribute (inline wins). Returns elements changed."""
    changed = 0
    if not rules:
        return 0
    for element in root.iter():
        if element.tag == "#root":
            continue
        matching = sorted((rule for rule in rules if rule.matches(element)), key=lambda rule: rule.specificity)
        if not matching:
            continue
        merged: dict[str, str] = {}
        for rule in matching:
            for name, value in rule.declarations:
                merged[name] = value
        for name, value in parse_style(element.get("style")):
            merged[name] = value
        element.set("style", style_text(list(merged.items())))
        changed += 1
    return changed


# --------------------------------------------------------------------------- transformation


@dataclass
class Result:
    html: str
    blocking: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    changes: list[str] = field(default_factory=list)
    report: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.blocking


def load_styles(path: Path = STYLES_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def url_allowed(value: str) -> bool:
    value = value.strip()
    if not value or value.startswith(("#", "/", "?")):
        return True
    scheme = urlparse(value).scheme.lower()
    return scheme in URL_PROTOCOLS or scheme == ""


class Transformer:
    def __init__(self, styles: dict, fix_headings: bool = True) -> None:
        self.styles = styles
        self.fix_headings = fix_headings
        self.blocking: list[str] = []
        self.warnings: list[str] = []
        self.changes: Counter[str] = Counter()

    # -- element cleaning ---------------------------------------------------
    def clean(self, node: Element) -> list[Element | str]:
        """Return the cleaned replacement for ``node`` (may be several nodes or none)."""
        tag = node.tag
        if tag in DROP_WITH_CONTENT:
            if tag in {"script", "style"}:
                self.changes[f"removed <{tag}> block (Canvas strips it)"] += 1
            elif tag == "svg":
                self.blocking.append("an inline <svg> graphic is not allowed on Canvas pages; upload it as an image file and add alt text")
            elif tag == "canvas":
                self.blocking.append("a <canvas> drawing cannot be kept on a Canvas page; replace it with an image or package the activity as SCORM")
            elif tag in {"noscript", "template"}:
                self.changes[f"removed <{tag}>"] += 1
            return []
        if tag in PAGE_REMOVED_TAGS:
            reference = node.get("src") or node.get("data")
            self.blocking.append(f"<{tag}> {reference or ''} is removed from Canvas pages; embed it with an iframe or Canvas media instead".strip())
            return []
        if tag in CONTENT_FORM_TAGS:
            if tag in {"input", "textarea", "select"}:
                label = node.get("value") or node.get("placeholder") or node.get("aria-label")
                self.blocking.append(f"a form field <{tag}>{' (' + label + ')' if label else ''} cannot work on a Canvas page; use a Canvas quiz/assignment or a SCORM activity")
            else:
                self.changes[f"unwrapped <{tag}> (Canvas pages do not keep form controls; text kept)"] += 1
                if tag == "button":
                    for handler_name, handler in node.attrs:
                        if handler_name.startswith("on") and re.search(r"location|window\.open|href|navigate|https?:", handler, re.IGNORECASE):
                            self.blocking.append(f"button '{' '.join(node.text().split())[:40]}' went somewhere with a script ({handler[:60]}); replace it with a link")
                    self.warnings.append(f"button '{' '.join(node.text().split())[:40]}' did something with a script; on a Canvas page it is plain text")
            return self.clean_children(node)
        if tag in TAG_RENAMES:
            original = tag
            node = Element(TAG_RENAMES[tag], node.attrs, node.children)
            if original == "center":
                node.set("style", (node.get("style") + "; text-align: center").strip("; "))
            self.changes[f"<{original}> changed to <{node.tag}> (Canvas allowlist)"] += 1
            tag = node.tag
        if tag not in ALLOWED_TAGS and tag not in MATHML_TAGS:
            self.changes[f"unwrapped <{tag}> (not on the Canvas allowlist; text kept)"] += 1
            return self.clean_children(node)

        cleaned = Element(tag)
        for name, value in node.attrs:
            if name.startswith("on"):
                if re.search(r"location|window\.open|href|navigate|\.html?\b|https?:", value, re.IGNORECASE):
                    self.blocking.append(f"a script action on <{tag}> went somewhere ({value[:60]}); replace it with an ordinary link so the destination is kept")
                else:
                    self.changes["removed inline event handler (on…=)"] += 1
                continue
            allowed = (name in GLOBAL_ATTRS or name.startswith(("aria-", "data-")) or name in ELEMENT_ATTRS.get(tag, set())
                       or (tag in MATHML_TAGS and not name.startswith("on")))
            if not allowed:
                if name == "srcdoc" and value.strip():
                    self.blocking.append("an iframe's built-in content (srcdoc) is removed by Canvas; put that content on the page itself")
                    continue
                self.changes[f"removed {name}= attribute from <{tag}> (not on the Canvas allowlist)"] += 1
                continue
            if name == "id" and value.lower() in DISALLOWED_IDS:
                self.changes[f"removed reserved id=\"{value}\""] += 1
                continue
            if name in URL_ATTRS and not url_allowed(value):
                if tag == "img" and value.startswith("data:"):
                    self.blocking.append("an image is embedded as base64 data; upload it to the course Files and link it (alt: "
                                         f"{node.get('alt') or 'missing'})")
                    cleaned.attrs.append((name, value))  # Kept so the gap stays visible in preview; Canvas will drop it.
                    continue
                self.blocking.append(f"<{tag} {name}=\"{value[:60]}\"> uses a protocol Canvas removes; replace the link")
                continue
            if name == "sandbox":
                kept = [token for token in value.split() if token in SANDBOX_TOKENS]
                if len(kept) != len(value.split()):
                    self.changes["removed unsupported iframe sandbox tokens"] += 1
                value = " ".join(kept)
            cleaned.attrs.append((name, value))
        cleaned.children = self.clean_children(node)
        return [cleaned]

    def clean_children(self, node: Element) -> list[Element | str]:
        children: list[Element | str] = []
        for child in node.children:
            if isinstance(child, str):
                children.append(child)
            else:
                children.extend(self.clean(child))
        return children

    # -- headings -----------------------------------------------------------
    def fix_heading_levels(self, root: Element) -> None:
        headings = [element for element in root.iter() if re.fullmatch(r"h[1-6]", element.tag)]
        if not headings or not self.fix_headings:
            if any(element.tag == "h1" for element in headings):
                self.warnings.append("page body uses <h1>; Canvas already shows the page title as the H1")
            return
        top = min(int(element.tag[1]) for element in headings)
        previous = 1
        for element in headings:
            level = int(element.tag[1]) - top + 2
            level = max(2, min(level, previous + 1, 6))
            if f"h{level}" != element.tag:
                self.changes["heading level adjusted so headings sit under the page title without skipping levels"] += 1
                element.tag = f"h{level}"
            previous = level

    # -- styling ------------------------------------------------------------
    def apply_styles(self, root: Element, inherited_bg: str, inherited_fg: str) -> None:
        elements = self.styles["elements"]
        for child in root.children:
            if not isinstance(child, Element):
                continue
            source = [(name, value) for name, value in parse_style(child.get("style"))]
            kept: list[tuple[str, str]] = []
            for name, value in source:
                if not css_property_allowed(name):
                    self.changes[f"removed style property '{name}' (Canvas strips it)"] += 1
                    continue
                if name == "position" and value.strip().lower() in {"fixed", "sticky"}:
                    self.changes["removed position: fixed/sticky (Canvas strips it)"] += 1
                    continue
                size = font_size_px(value) if name == "font-size" else shorthand_font_size_px(value) if name == "font" else None
                if size is not None and size < MIN_TEXT_PX:
                    self.changes[f"removed text sizes under {MIN_TEXT_PX}px so text stays readable"] += 1
                    continue
                kept.append((name, value))
            house = parse_style(elements.get(child.tag, ""))
            house_names = {name for name, _ in house}
            merged = house + [(name, value) for name, value in kept if name not in house_names]
            if child.tag == "a" and self.is_standalone_link(child):
                button_look = parse_style(self.styles["standaloneLink"])
                button_names = {name for name, _ in button_look}
                merged = button_look + [(n, v) for n, v in kept if n not in button_names]
                self.changes["standalone link given a large, button-sized target"] += 1

            background = resolve_background(background_colour(merged), inherited_bg)
            needed = 3.0 if is_large_text(merged, child.tag) else 4.5
            source_colour = next((value for name, value in reversed(kept) if name == "color"), None)
            merged_colour = next((value for name, value in reversed(merged) if name == "color"), None)
            if source_colour is not None and parse_colour(source_colour) is None:
                self.warnings.append(f"could not check the contrast of colour '{source_colour}' on <{child.tag}>; check it by eye")
                foreground = source_colour
            else:
                # Prefer the teacher's own colour, then the house colour, then the inherited colour,
                # taking the first that is readable on the real background behind it.
                candidates = [c for c in (source_colour, merged_colour, inherited_fg) if c is not None]
                chosen = next((c for c in candidates if (contrast_ratio(c, background) or 0) >= needed), None)
                if chosen is None:
                    chosen = max((self.styles["ink"], "#ffffff"), key=lambda c: contrast_ratio(c, background) or 0)
                    if (contrast_ratio(chosen, background) or 0) < needed:
                        self.warnings.append(f"background {background} behind '{' '.join(child.text().split())[:40]}' is too mid-toned for AA text; change it")
                if source_colour is not None and chosen != source_colour:
                    self.changes["low-contrast colour replaced so text meets WCAG AA"] += 1
                    self.warnings.append(f"colour changed on '{' '.join(child.text().split())[:40]}': check colour did not carry meaning on its own")
                if chosen != (merged_colour or inherited_fg):
                    if merged_colour is not None:
                        merged = [(n, chosen if n == "color" else v) for n, v in merged]
                    else:
                        merged = merged + [("color", chosen)]
                foreground = chosen

            hidden = any((n == "display" and v.lower() == "none") or (n == "visibility" and v.lower() in {"hidden", "collapse"})
                         or (n == "opacity" and v.strip() in {"0", "0.0", "0%"}) for n, v in merged)
            if hidden and visible_words(child):
                self.blocking.append(f"'{' '.join(visible_words(child))[:50]}' is hidden (display:none or similar); with no scripts on a "
                                     "Canvas page it would stay hidden for good. Show it, or put it in a <details> 'Show answer' box")

            if child.tag == "img" and not any(name == "alt" for name, _ in child.attrs):
                self.blocking.append(f"image {child.get('src')[:80]} has no alt text; write alt text (or alt=\"\" if decorative)")
            if child.tag == "a":
                label = " ".join(child.text().split()).lower()
                if label in VAGUE_LINK_TEXT or re.fullmatch(r"https?://\S+", label or ""):
                    self.warnings.append(f"link text '{label or child.get('href')}' does not say where it goes; consider clearer wording")
                if not label and not any(n.tag == "img" and n.get("alt") for n in child.iter()):
                    self.blocking.append(f"link to {child.get('href')} has no text a screen reader can say")
            if child.tag == "table" and not any(element.tag == "th" for element in child.iter()):
                self.warnings.append("a table has no header cells (<th>); check whether its first row or column should be headers")
            if child.tag == "iframe" and not child.get("title"):
                self.warnings.append(f"embedded frame {child.get('src')[:60]} has no title; add one so screen readers can name it")
            if child.tag in {"video", "audio"} and not any(isinstance(n, Element) and n.tag == "track" for n in child.children):
                self.warnings.append(f"<{child.tag}> has no captions/subtitles track; check captions are available")

            if merged:
                child.set("style", style_text(merged))
            elif child.get("style"):
                child.remove("style")
            self.apply_styles(child, background, foreground)

    @staticmethod
    def is_standalone_link(link: Element) -> bool:
        return getattr(link, "_standalone", False)

    def mark_standalone_links(self, root: Element) -> None:
        for element in root.iter():
            if element.tag not in {"p", "li", "div"}:
                continue
            meaningful = [child for child in element.children if not (isinstance(child, str) and not child.strip())]
            if len(meaningful) == 1 and isinstance(meaningful[0], Element) and meaningful[0].tag == "a":
                setattr(meaningful[0], "_standalone", True)


def transform(source_html: str, *, styles: dict | None = None, fix_headings: bool = True, lang: str = "en-AU") -> Result:
    styles = styles or load_styles()
    source = parse(source_html)
    # Re-wrap an earlier canvas-safe copy instead of nesting wrappers.
    top_level = [child for child in source.children if not (isinstance(child, str) and not child.strip())]
    if len(top_level) == 1 and isinstance(top_level[0], Element) and top_level[0].get("data-aac-canvas-safe"):
        source = Element("#root", children=top_level[0].children)
    transformer = Transformer(styles, fix_headings=fix_headings)
    rules, skipped_rules = parse_css_rules(collect_style_blocks(source))
    body = Element("#root", children=transformer.clean_children(source))
    inlined = inline_css_rules(body, rules)
    if inlined:
        transformer.changes[f"copied <style> rules onto {inlined} element(s) as inline styles"] += 1
    if skipped_rules:
        transformer.warnings.append(f"{skipped_rules} <style> rule(s) (hover effects, media queries, complex selectors, page rules) cannot be inlined; check nothing important depended on them")
    transformer.fix_heading_levels(body)
    transformer.mark_standalone_links(body)
    transformer.apply_styles(body, styles["background"], styles["ink"])

    template = string.Template(PAGE_TEMPLATE.read_text(encoding="utf-8"))
    output_html = template.substitute(lang=html.escape(lang, quote=True), wrapper_style=html.escape(styles["wrapper"], quote=True), content=serialise(body).strip())
    output = parse(output_html)
    lost = lost_content(source, output)
    blocking = list(dict.fromkeys(transformer.blocking))
    for kind, items in lost.items():
        for item in items[:10]:
            blocking.append(f"{kind[:-1]} lost in conversion: {item}")
    warnings = list(dict.fromkeys(transformer.warnings))
    changes = [f"{message} (x{count})" if count > 1 else message for message, count in transformer.changes.items()]
    report = {
        "ok": not blocking,
        "blocking": blocking,
        "warnings": warnings,
        "changes": changes,
        "inventory": {"source": inventory(source), "output": inventory(output)},
        "lost": lost,
    }
    return Result(html=output_html, blocking=blocking, warnings=warnings, changes=changes, report=report)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Make an accessible, Canvas-safe copy of a QLearn page body.")
    parser.add_argument("source", type=Path, help="page body HTML (for example from canvas_client.py get-page --out)")
    parser.add_argument("output", type=Path, help="where to write the Canvas-safe HTML")
    parser.add_argument("--report", type=Path, help="write the JSON report here")
    parser.add_argument("--keep-heading-levels", action="store_true", help="do not adjust heading levels")
    parser.add_argument("--lang", default="en-AU")
    args = parser.parse_args(argv)
    try:
        result = transform(args.source.read_text(encoding="utf-8"), fix_headings=not args.keep_heading_levels, lang=args.lang)
    except (OSError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    args.output.write_text(result.html, encoding="utf-8")
    if args.report:
        args.report.write_text(json.dumps(result.report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    source_inv, output_inv = result.report["inventory"]["source"], result.report["inventory"]["output"]
    print(f"Kept {output_inv['words']}/{source_inv['words']} words, {len(output_inv['links'])}/{len(source_inv['links'])} links, "
          f"{len(output_inv['images'])}/{len(source_inv['images'])} images, {len(output_inv['media'])}/{len(source_inv['media'])} media.")
    for change in result.changes:
        print(f"CHANGED: {change}")
    for warning in result.warnings:
        print(f"CHECK: {warning}")
    for item in result.blocking:
        print(f"NEEDS TEACHER: {item}")
    print(f"Wrote {args.output}" + ("" if result.ok else " — not ready to save until the NEEDS TEACHER items are resolved"))
    return 0 if result.ok else 2


if __name__ == "__main__":
    sys.exit(main())
