"""Shared grid placement for HTML and OBF; preserve gaps and row-major scan order."""
from __future__ import annotations
import math


def grid_slots(page):
    rows, columns = page['grid']['rows'], page['grid']['columns']
    occupied = set()
    result = []
    for index, button in enumerate(page['buttons']):
        position = button.get('position')
        row, column = divmod(index, columns)
        if position:
            try:
                x, y = float(position['x']) * columns / 100, float(position['y']) * rows / 100
                width = float(position.get('width', 100 / columns)) * columns / 100
                height = float(position.get('height', 100 / rows)) * rows / 100
                if not all(math.isfinite(v) for v in (x, y, width, height)) or any(abs(v - round(v)) > .001 for v in (x, y)) or abs(width - 1) > .001 or abs(height - 1) > .001:
                    raise ValueError('position must occupy one aligned grid cell')
                row, column = round(y), round(x)
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError(f"{button['id']}: invalid grid position: {error}") from error
        if not (0 <= row < rows and 0 <= column < columns) or (row, column) in occupied:
            raise ValueError(f"{button['id']}: grid position is outside the page or overlaps another button")
        occupied.add((row, column))
        result.append((row, column, button))
    return sorted(result, key=lambda item: (item[0], item[1]))
