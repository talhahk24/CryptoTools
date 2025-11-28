"""Placeholder RSI strategy."""
from __future__ import annotations

from typing import Any


def generate_signal(data: Any) -> str:
    """Return a placeholder signal for incoming stream data."""
    if data:
        return "HOLD"
    return "NO_DATA"
