"""Utility helpers for Catalunya Beaches."""

from __future__ import annotations


def parse_coordinate(
    value: float | str | None,
    min_val: float | None = None,
    max_val: float | None = None,
) -> float | None:
    """Parse a coordinate into a float value with optional range validation."""
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if min_val is not None and result < min_val:
        return None
    if max_val is not None and result > max_val:
        return None
    return result
