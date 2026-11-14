"""Does a board's bottom row fit on the screen? Fit maths at the IR level.

The house layout puts Help, Different and Finished on the bottom row, so a page
that is too tall for the device clips exactly the repair words. The renderer's
grid cannot shrink below ``minimumTargetSizePx``; when rows x target is taller
than the viewport the page does not scroll, it is cut off.

Constants were measured on the pack's own renderer in Chrome at 1264 x 600
(first grid row starts 103 px down without a message bar, 173 px with one) and
carry a 7 px allowance for platform font differences. They must stay equal to
the ones in skills/accent-display-fit/scripts/check_accent_display.py
(tests/test_display_fit.py enforces this).
"""

from __future__ import annotations

from typing import Any

MUST_FIT_FLOOR = (1264, 600)  # maximised Edge on an Accent 1400-30 at 150% scaling
CHROME_PLAIN = 110
CHROME_MESSAGE_BAR = 180
GAP = 12
GAP_CVI = 24
HORIZONTAL_PADDING = 24
OFF_SCREEN_PROFILES = {"print-only", "partner-assisted-print"}
DWELL_METHODS = {"eye-gaze-dwell", "mouse-dwell"}
MINIMUM_DWELL_TARGET = 120
MINIMUM_TOUCH_TARGET = 44


def page_chrome(ir: dict[str, Any]) -> int:
    message_bar = ir.get("messageBar")
    return CHROME_MESSAGE_BAR if isinstance(message_bar, dict) and message_bar.get("enabled") else CHROME_PLAIN


def grid_gap(ir: dict[str, Any]) -> int:
    display = ir.get("display")
    return GAP_CVI if isinstance(display, dict) and display.get("visualProfile") == "cvi" else GAP


def stop_column(ir: dict[str, Any]) -> bool:
    """The renderer reserves a column one target wide at the right edge for Stop speech."""
    controls = ir.get("studentControls")
    return not isinstance(controls, dict) or controls.get("stopSpeechDuringPlayback", True) is not False


def needed_size(rows: int, columns: int, target: int, chrome: int, gap: int = GAP, stop: bool = False) -> tuple[int, int]:
    """Smallest viewport (width, height) that shows a rows x columns grid of target-sized cells.

    With ``stop`` the width also holds the Stop speech column (one target plus a
    gap); without room for it the control overlaps the last column of the grid.
    """
    width = columns * target + (columns - 1) * gap + HORIZONTAL_PADDING + ((target + gap) if stop else 0)
    height = rows * target + (rows - 1) * gap + chrome
    return width, height


def largest_target(rows: int, columns: int, chrome: int, gap: int = GAP, floor: tuple[int, int] = MUST_FIT_FLOOR, stop: bool = False) -> int:
    """Largest target size (px) at which a rows x columns grid still fits the floor."""
    by_height = (floor[1] - chrome - (rows - 1) * gap) // rows
    by_width = (floor[0] - HORIZONTAL_PADDING - (columns - 1) * gap - (gap if stop else 0)) // (columns + (1 if stop else 0))
    return max(0, min(by_height, by_width))


def is_on_screen(ir: dict[str, Any]) -> bool:
    access = ir.get("access")
    profile = access.get("profile") if isinstance(access, dict) else None
    return profile not in OFF_SCREEN_PROFILES


def board_fit(ir: dict[str, Any], floor: tuple[int, int] = MUST_FIT_FLOOR) -> list[dict[str, Any]]:
    """One entry per distinct grid size on the board, worst first.

    Each entry: rows, columns, pages (ids), target, neededWidth, neededHeight,
    fits, overflowPx (how much of the bottom row is cut off), largestTarget and
    smallestAllowedTarget (120 px for gaze/dwell, 44 px otherwise).
    """
    access = ir.get("access") if isinstance(ir.get("access"), dict) else {}
    try:
        target = int(access.get("minimumTargetSizePx"))
    except (TypeError, ValueError):
        return []
    chrome, gap, stop = page_chrome(ir), grid_gap(ir), stop_column(ir)
    methods = set(access.get("intended") or []) | {access.get("profile")}
    smallest = MINIMUM_DWELL_TARGET if methods & DWELL_METHODS else MINIMUM_TOUCH_TARGET
    grids: dict[tuple[int, int], list[str]] = {}
    for page in ir.get("pages") or []:
        if not isinstance(page, dict):
            continue
        grid = page.get("grid") if isinstance(page.get("grid"), dict) else {}
        try:
            rows, columns = int(grid.get("rows")), int(grid.get("columns"))
        except (TypeError, ValueError):
            continue
        if rows > 0 and columns > 0:
            grids.setdefault((rows, columns), []).append(str(page.get("id", "")))
    results = []
    for (rows, columns), pages in grids.items():
        width, height = needed_size(rows, columns, target, chrome, gap, stop)
        results.append({
            "rows": rows,
            "columns": columns,
            "pages": pages,
            "target": target,
            "neededWidth": width,
            "neededHeight": height,
            "fits": width <= floor[0] and height <= floor[1],
            "overflowPx": max(0, height - floor[1]),
            "largestTarget": largest_target(rows, columns, chrome, gap, floor, stop),
            "smallestAllowedTarget": smallest,
        })
    return sorted(results, key=lambda item: (item["fits"], -item["neededHeight"], -item["neededWidth"]))


def describe(entry: dict[str, Any], floor: tuple[int, int] = MUST_FIT_FLOOR) -> str:
    """One-line explanation with the numbers an author needs to fix it."""
    grid = f"{entry['rows']}x{entry['columns']}"
    count = len(entry["pages"])
    where = f"{count} page{'s' if count != 1 else ''} ({', '.join(entry['pages'][:3])}{', ...' if count > 3 else ''})"
    if entry["fits"]:
        return f"{grid} at {entry['target']} px needs {entry['neededWidth']}x{entry['neededHeight']} px: fits {floor[0]}x{floor[1]} ({where})."
    if entry["overflowPx"]:
        problem = f"about {entry['overflowPx']} px of the bottom row (where Help, Different and Finished live) is cut off"
    else:
        problem = "the last column is overlapped by the Stop speech control or cut off"
    fewer = "use fewer rows per page" if entry["overflowPx"] else "use fewer columns per page (for spelling, the grouped keyboard)"
    if entry["largestTarget"] >= entry.get("smallestAllowedTarget", MINIMUM_DWELL_TARGET):
        remedy = f"use targets of {entry['largestTarget']} px or less on this grid, {fewer}"
    else:
        remedy = fewer + f" (targets cannot go below {entry.get('smallestAllowedTarget', MINIMUM_DWELL_TARGET)} px for this access method)"
    return (
        f"{grid} at {entry['target']} px needs {entry['neededWidth']}x{entry['neededHeight']} px but the screen floor is "
        f"{floor[0]}x{floor[1]}: {problem} on {where}. To fix: {remedy}, or confirm the device's real viewport is larger."
    )
