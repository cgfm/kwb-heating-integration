"""Helpers for capability-based register discovery."""
from __future__ import annotations

from typing import Any


def normalize_register_address(value: Any) -> int | None:
    """Normalize a configured Modbus address without accepting booleans."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def find_register_by_parameter(
    registers: list[dict[str, Any]], parameter: str
) -> dict[str, Any] | None:
    """Return the first register with the exact manufacturer parameter."""
    return next(
        (register for register in registers if register.get("parameter") == parameter),
        None,
    )
