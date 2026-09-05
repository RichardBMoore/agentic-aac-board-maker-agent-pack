# Output quality and supported behaviour

## Access and representation

Standalone HTML supports native click/keyboard and optional pointer dwell. It does not implement single-/two-switch scanning: those settings fail export. Route explicit scanning requests to a player with verified scanning support, or offer partner-assisted print where that matches the request. Partner-assisted scanning is human-led and should set `switchScanning: false`.

Choose familiar symbols, photographs, text or a mix from the supplied context. Text-only is a valid intentional format, not proof that a requested symbol board is finished. Report embedded and missing representations and distinguish learner familiarity from successful image rendering.

`fetch_arasaac_symbols.py --review-out review.json` creates an offline candidate sheet with embedded available previews. Select candidates or keep-current/none-fits/text-only, then Download decisions and apply with `--apply-review symbol-review.decisions.json --out reviewed.ir.json`. Decisions are bound to the exact board revision; regenerate stale reviews. Existing approved images survive failed replacements. Keep an existing reviewed IR as the starting point for related resources; do not assume a mapping approved for one learner/system transfers to another.

## Layout and print

HTML and OBF preserve percentage `position` fields when they occupy one aligned grid cell. Empty cells remain empty; overlap, off-grid and multi-cell positions fail rather than silently moving words. The HTML DOM follows visual row-major order. Open AAC Studio retains its explicit positions.

HTML supports per-button fill/border colours and font family, size, weight and colour, plus label-top/bottom/left/right symbol layouts. Other visual style fields are not guaranteed across formats. Use the actual student's established layout; adding vocabulary should preserve chosen positions where possible.

Render paper settings with `render_html.py board.ir.json board.html --paper A4 --orientation landscape` (also A3/portrait). Print includes numbered scan order and a separate teacher page. Inspect actual print pagination and grayscale output before describing a printable pack as checked. Include source, licence and full attribution in exports.

## Functional acceptance

Use browser tests to start, select, navigate, speak, stop and recover focus through the requested access method. Check speech completion, error and unavailable modes, decoded offline images, and a long-label case at the intended viewport. Metadata and a successful parity check do not prove real-device access.

For curriculum boards, construct at least one complete context-specific message through the actual buttons and include alternatives, repair and uncertainty as appropriate. Preserve valid partial messages. If subject/evidence vocabulary is missing, resolve it from the source or clearly mark the teacher handoff as awaiting content. Do not present generic demonstration content as evidence from a class text.

The evaluator is a static candidate checker, not a model-generation benchmark. It reports symbol coverage and can check expected composed message sequences. Browser interaction, symbol familiarity, actual input devices and print pagination are separately verified.
