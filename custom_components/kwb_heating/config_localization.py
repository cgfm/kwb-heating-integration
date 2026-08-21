"""Schema-aware localization for the unified KWB firmware configuration."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


SUPPORTED_LANGUAGES = ("de", "en")


def resolve_localized_value(
    value: Any,
    language: str,
    *,
    fallback: str = "",
) -> str:
    """Resolve one explicitly localized value with deterministic fallbacks."""
    if isinstance(value, str):
        return value
    if not isinstance(value, dict):
        return fallback
    candidates = (language, "en", "de", *value.keys())
    seen: set[str] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        resolved = value.get(candidate)
        if isinstance(resolved, str) and resolved.strip():
            return resolved.strip()
    return fallback


def localize_register(register: dict[str, Any], language: str) -> dict[str, Any]:
    """Resolve only the register fields declared localized by the schema."""
    localized = deepcopy(register)
    localized["name"] = resolve_localized_value(
        register.get("name"),
        language,
        fallback=(
            str(register.get("entity_id") or register.get("parameter") or "Register ")
            + (
                str(register.get("starting_address"))
                if not (register.get("entity_id") or register.get("parameter"))
                else ""
            )
        ),
    )
    if "index" in register:
        localized["index"] = resolve_localized_value(
            register.get("index"), language, fallback=""
        )
    return localized


def localize_value_tables(
    value_tables: dict[str, Any], language: str
) -> dict[str, dict[str, str]]:
    """Resolve value-table labels while retaining the same table/raw keys."""
    localized: dict[str, dict[str, str]] = {}
    for table_name, table in value_tables.items():
        if not isinstance(table, dict):
            continue
        localized[table_name] = {
            str(raw_value): resolve_localized_value(
                labels, language, fallback=str(raw_value)
            )
            for raw_value, labels in table.items()
        }
    return localized


def localize_alarm_codes(
    alarm_codes: list[dict[str, Any]], language: str
) -> list[dict[str, Any]]:
    """Resolve alarm descriptions without changing alarm membership or identity."""
    localized: list[dict[str, Any]] = []
    for alarm in alarm_codes:
        item = deepcopy(alarm)
        item["description"] = resolve_localized_value(
            alarm.get("description"),
            language,
            fallback=f"Alarm {alarm.get('alarm_id', 'unknown')}",
        )
        localized.append(item)
    return localized
