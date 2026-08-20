#!/usr/bin/env python3
"""Validation helpers for finalized or generated KWB configuration trees."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ENTITY_ID_PATTERN = re.compile(r"^[a-z0-9_]+$")


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object and give callers a path-specific failure."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level JSON value must be an object")
    return data


def registers_from(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return either supported register-list shape."""
    registers = data.get("registers", data.get("universal_registers", []))
    return registers if isinstance(registers, list) else []


def logical_register_key(
    relative_path: Path, register: dict[str, Any]
) -> tuple[str, str, str] | None:
    """Build a stable key from file context, KWB parameter, and equipment index."""
    parameter = register.get("parameter")
    if not isinstance(parameter, str) or not parameter.strip():
        return None
    index = str(register.get("index", "")).strip()
    return relative_path.as_posix(), parameter.strip(), index


def _equipment_index_valid(index: Any) -> bool:
    if index in (None, ""):
        return True
    if not isinstance(index, str) or " " not in index:
        return False
    _prefix, identifier = index.split(" ", 1)
    try:
        int(identifier.split(".", 1)[0])
    except ValueError:
        return False
    return True


def validate_config_tree(root: Path) -> list[str]:
    """Validate a version tree without comparing it to any other tree."""
    root = Path(root)
    errors: list[str] = []
    language_registers: dict[
        tuple[str, str], dict[tuple[str, str, str], dict[str, Any]]
    ] = {}

    for language_dir in sorted(root.glob("v*/*")):
        if not language_dir.is_dir():
            continue
        version = language_dir.parent.name
        language = language_dir.name
        value_tables_path = language_dir / "value_tables.json"
        try:
            value_tables_data = load_json(value_tables_path)
            value_tables = value_tables_data.get("value_tables", {})
            if not isinstance(value_tables, dict):
                errors.append(f"{value_tables_path}: value_tables must be an object")
                value_tables = {}
        except ValueError as exc:
            errors.append(str(exc))
            value_tables = {}

        logical: dict[tuple[str, str, str], dict[str, Any]] = {}
        referenced_tables: set[str] = set()
        for path in sorted(language_dir.rglob("*.json")):
            if path == value_tables_path:
                continue
            try:
                data = load_json(path)
            except ValueError as exc:
                errors.append(str(exc))
                continue
            registers = registers_from(data)
            if not registers:
                continue

            seen_ids: dict[str, Any] = {}
            seen_addresses: dict[int, dict[str, Any]] = {}
            relative_path = path.relative_to(language_dir)
            for number, register in enumerate(registers):
                location = f"{path}:{number}"
                if not isinstance(register, dict):
                    errors.append(f"{location}: register must be an object")
                    continue
                address = register.get("starting_address")
                if isinstance(address, bool) or not isinstance(address, int) or address < 0:
                    errors.append(f"{location}: invalid starting_address {address!r}")
                elif address in seen_addresses:
                    errors.append(
                        f"{location}: duplicate address {address} in one register file"
                    )
                else:
                    seen_addresses[address] = register

                entity_id = register.get("entity_id")
                if not isinstance(entity_id, str) or not ENTITY_ID_PATTERN.fullmatch(
                    entity_id
                ):
                    errors.append(f"{location}: invalid entity_id {entity_id!r}")
                elif entity_id in seen_ids:
                    errors.append(
                        f"{location}: duplicate entity_id {entity_id!r} at "
                        f"addresses {seen_ids[entity_id]!r} and {address!r}"
                    )
                else:
                    seen_ids[entity_id] = address

                if relative_path.parts[:1] == ("equipment",) and not _equipment_index_valid(
                    register.get("index")
                ):
                    errors.append(
                        f"{location}: malformed equipment index "
                        f"{register.get('index')!r}"
                    )

                table = register.get("unit_value_table")
                if isinstance(table, str) and table.endswith("_t"):
                    referenced_tables.add(table)

                key = logical_register_key(relative_path, register)
                if key is None:
                    errors.append(f"{location}: missing stable parameter")
                elif key in logical:
                    errors.append(f"{location}: duplicate logical register key {key!r}")
                else:
                    logical[key] = register

        for table in sorted(referenced_tables - set(value_tables)):
            errors.append(
                f"{language_dir}: referenced value table {table!r} does not exist"
            )
        language_registers[(version, language)] = logical

    versions = {version for version, _language in language_registers}
    for version in sorted(versions):
        de = language_registers.get((version, "de"), {})
        en = language_registers.get((version, "en"), {})
        for key in sorted(de.keys() & en.keys()):
            de_id = de[key].get("entity_id")
            en_id = en[key].get("entity_id")
            if de_id != en_id:
                errors.append(
                    f"{version}/{key[0]} parameter={key[1]!r} index={key[2]!r}: "
                    f"German entity_id {de_id!r} != English entity_id {en_id!r}"
                )

    return errors


def validate_or_raise(root: Path) -> None:
    """Raise one readable exception when a tree fails validation."""
    errors = validate_config_tree(root)
    if errors:
        raise ValueError("Configuration validation failed:\n" + "\n".join(errors))

