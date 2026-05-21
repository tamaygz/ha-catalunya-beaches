"""Utility helpers for Catalunya Beaches."""

from __future__ import annotations


def parse_coordinate(value: float | str | None) -> float | None:
    """Parse a coordinate into a float value."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
