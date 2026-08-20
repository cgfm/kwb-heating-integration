#!/usr/bin/env python3
"""Safely finalize generated templates into canonical integration configuration."""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import tempfile
from typing import Any

try:
    from config_validation import (
        load_json,
        logical_register_key,
        registers_from,
        validate_or_raise,
    )
except ImportError:  # Imported as modbusinfoConverter.import_generated_config.
    from .config_validation import (
        load_json,
        logical_register_key,
        registers_from,
        validate_or_raise,
    )


REGISTER_CONTAINER_KEYS = ("registers", "universal_registers")


def _register_container(data: dict[str, Any]) -> str | None:
    return next((key for key in REGISTER_CONTAINER_KEYS if key in data), None)


def _comparison_without_published_id(register: dict[str, Any]) -> dict[str, Any]:
    comparable = dict(register)
    comparable.pop("entity_id", None)
    return comparable


def _merge_register_file(
    relative_path: Path,
    generated: dict[str, Any],
    canonical: dict[str, Any],
    report: dict[str, Any],
) -> dict[str, Any]:
    """Preserve finalized registers and add only unambiguous new registers."""
    generated_key = _register_container(generated)
    canonical_key = _register_container(canonical)
    if generated_key is None or canonical_key is None:
        return deepcopy(canonical)

    generated_registers = registers_from(generated)
    canonical_registers = registers_from(canonical)
    canonical_by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    canonical_by_address: dict[Any, list[dict[str, Any]]] = {}
    matched_keys: set[tuple[str, str, str]] = set()
    for register in canonical_registers:
        key = logical_register_key(relative_path, register)
        if key is not None:
            canonical_by_key.setdefault(key, []).append(register)
        canonical_by_address.setdefault(register.get("starting_address"), []).append(
            register
        )

    merged_registers = deepcopy(canonical_registers)
    for generated_register in generated_registers:
        key = logical_register_key(relative_path, generated_register)
        matches = canonical_by_key.get(key, []) if key is not None else []
        if len(matches) == 1:
            existing = matches[0]
            matched_keys.add(key)
            if existing.get("entity_id"):
                report["summary"]["published_entity_ids_preserved"] += 1
            if _comparison_without_published_id(existing) != (
                _comparison_without_published_id(generated_register)
            ):
                report["items"].append(
                    {
                        "kind": "existing_register_changed",
                        "blocking": True,
                        "file": relative_path.as_posix(),
                        "parameter": generated_register.get("parameter"),
                        "index": generated_register.get("index"),
                        "canonical": existing,
                        "generated": generated_register,
                        "decision": (
                            "Canonical register retained; review and apply intended "
                            "semantic changes manually."
                        ),
                    }
                )
            continue
        if len(matches) > 1:
            report["items"].append(
                {
                    "kind": "ambiguous_logical_match",
                    "blocking": True,
                    "file": relative_path.as_posix(),
                    "generated": generated_register,
                    "conflicting_entities": matches,
                }
            )
            continue

        address_matches = canonical_by_address.get(
            generated_register.get("starting_address"), []
        )
        if address_matches:
            report["items"].append(
                {
                    "kind": "unmatched_register_address_conflict",
                    "blocking": True,
                    "file": relative_path.as_posix(),
                    "generated": generated_register,
                    "conflicting_entities": address_matches,
                }
            )
            continue

        merged_registers.append(deepcopy(generated_register))
        report["summary"]["new_registers_added"] += 1

    for key, matches in canonical_by_key.items():
        if key not in matched_keys:
            report["items"].append(
                {
                    "kind": "canonical_only_register_preserved",
                    "blocking": False,
                    "file": relative_path.as_posix(),
                    "parameter": key[1],
                    "index": key[2],
                    "canonical_entities": matches,
                }
            )

    result = deepcopy(canonical)
    result[canonical_key] = merged_registers
    return result


def _merge_value_tables(
    relative_path: Path,
    generated: dict[str, Any],
    canonical: dict[str, Any],
    report: dict[str, Any],
) -> dict[str, Any]:
    """Preserve production refinements and add genuinely new tables."""
    result = deepcopy(canonical)
    canonical_tables = result.setdefault("value_tables", {})
    generated_tables = generated.get("value_tables", {})
    for name, table in generated_tables.items():
        if name not in canonical_tables:
            canonical_tables[name] = deepcopy(table)
            report["summary"]["new_value_tables_added"] += 1
        elif canonical_tables[name] != table:
            report["items"].append(
                {
                    "kind": "value_table_changed",
                    "blocking": True,
                    "file": relative_path.as_posix(),
                    "value_table": name,
                    "canonical": canonical_tables[name],
                    "generated": table,
                    "decision": "Canonical value table retained for review.",
                }
            )
    return result


def _merge_alarm_codes(
    relative_path: Path,
    generated: dict[str, Any],
    canonical: dict[str, Any],
    report: dict[str, Any],
) -> dict[str, Any]:
    """Preserve finalized alarms and append only new stable alarm keys."""
    result = deepcopy(canonical)
    canonical_alarms = result.setdefault("alarm_codes", [])
    generated_alarms = generated.get("alarm_codes", [])
    existing = {
        (alarm.get("starting_address"), alarm.get("alarm_id")): alarm
        for alarm in canonical_alarms
    }
    for alarm in generated_alarms:
        key = (alarm.get("starting_address"), alarm.get("alarm_id"))
        if key not in existing:
            canonical_alarms.append(deepcopy(alarm))
            report["summary"]["new_alarm_codes_added"] += 1
        elif existing[key] != alarm:
            report["items"].append(
                {
                    "kind": "alarm_code_changed",
                    "blocking": True,
                    "file": relative_path.as_posix(),
                    "canonical": existing[key],
                    "generated": alarm,
                    "decision": "Canonical alarm retained for review.",
                }
            )
    return result


def _conversion_review_items(generated_root: Path, version: str) -> list[dict]:
    report_path = generated_root / "conversion_review.json"
    if not report_path.exists():
        return []
    data = load_json(report_path)
    return [
        item
        for item in data.get("items", [])
        if str(item.get("firmware_version")) == version.removeprefix("v")
    ]


def build_finalized_version(
    generated_root: Path,
    canonical_root: Path,
    version: str,
) -> tuple[dict[Path, dict[str, Any]], dict[str, Any]]:
    """Build a validated proposal without mutating canonical configuration."""
    version = f"v{version.removeprefix('v')}"
    generated_version = Path(generated_root) / version
    canonical_version = Path(canonical_root) / version
    if not generated_version.is_dir():
        raise ValueError(f"Generated version does not exist: {generated_version}")

    report: dict[str, Any] = {
        "version": version,
        "generated_root": str(Path(generated_root)),
        "canonical_root": str(Path(canonical_root)),
        "items": [],
        "summary": {
            "published_entity_ids_preserved": 0,
            "new_registers_added": 0,
            "new_value_tables_added": 0,
            "new_alarm_codes_added": 0,
            "files_added": 0,
        },
    }
    for item in _conversion_review_items(Path(generated_root), version):
        report["items"].append(
            {"kind": "converter_review_required", "blocking": True, "detail": item}
        )

    proposed: dict[Path, dict[str, Any]] = {}
    canonical_files = (
        {path.relative_to(canonical_version) for path in canonical_version.rglob("*.json")}
        if canonical_version.is_dir()
        else set()
    )
    generated_files = {
        path.relative_to(generated_version) for path in generated_version.rglob("*.json")
    }

    for relative_path in sorted(canonical_files | generated_files):
        generated_path = generated_version / relative_path
        canonical_path = canonical_version / relative_path
        if not generated_path.exists():
            proposed[relative_path] = load_json(canonical_path)
            report["items"].append(
                {
                    "kind": "canonical_only_file_preserved",
                    "blocking": False,
                    "file": relative_path.as_posix(),
                }
            )
            continue
        generated_data = load_json(generated_path)
        if not canonical_path.exists():
            proposed[relative_path] = deepcopy(generated_data)
            report["summary"]["files_added"] += 1
            continue

        canonical_data = load_json(canonical_path)
        if relative_path.name == "value_tables.json":
            proposed[relative_path] = _merge_value_tables(
                relative_path, generated_data, canonical_data, report
            )
        elif relative_path.name == "alarm_codes.json":
            proposed[relative_path] = _merge_alarm_codes(
                relative_path, generated_data, canonical_data, report
            )
        elif _register_container(generated_data) is not None:
            proposed[relative_path] = _merge_register_file(
                relative_path, generated_data, canonical_data, report
            )
        else:
            proposed[relative_path] = deepcopy(canonical_data)
            if canonical_data != generated_data:
                report["items"].append(
                    {
                        "kind": "unrecognized_file_changed",
                        "blocking": True,
                        "file": relative_path.as_posix(),
                    }
                )

    with tempfile.TemporaryDirectory(prefix="kwb-config-finalize-") as temp_dir:
        validation_root = Path(temp_dir)
        for relative_path, data in proposed.items():
            destination = validation_root / version / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        validate_or_raise(validation_root)

    report["blocking_review_required"] = any(
        item.get("blocking", False) for item in report["items"]
    )
    return proposed, report


def write_finalized_version(
    canonical_root: Path,
    version: str,
    proposed: dict[Path, dict[str, Any]],
) -> None:
    """Write a fully validated proposal to the canonical tree."""
    version = f"v{version.removeprefix('v')}"
    for relative_path, data in proposed.items():
        destination = Path(canonical_root) / version / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temporary.replace(destination)


def main() -> int:
    """CLI entry point; dry-run is the safe default."""
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    parser = argparse.ArgumentParser(
        description=(
            "Finalize generated KWB templates while preserving published production IDs."
        )
    )
    parser.add_argument("version", help="Firmware version, for example 25.7.1")
    parser.add_argument(
        "--generated-root",
        type=Path,
        default=script_dir / "config" / "versions",
    )
    parser.add_argument(
        "--canonical-root",
        type=Path,
        default=(
            project_root
            / "custom_components"
            / "kwb_heating"
            / "config"
            / "versions"
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Review-report path (default: generated root/import_review_<version>.json)",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write the validated proposal; without this flag the command is dry-run only.",
    )
    args = parser.parse_args()

    proposed, report = build_finalized_version(
        args.generated_root, args.canonical_root, args.version
    )
    report_path = args.report or (
        args.generated_root / f"import_review_v{args.version.removeprefix('v')}.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    if args.write:
        if report["blocking_review_required"]:
            print(f"Refusing to write: blocking review items are listed in {report_path}")
            return 2
        write_finalized_version(args.canonical_root, args.version, proposed)
        print(f"Finalized v{args.version.removeprefix('v')} into {args.canonical_root}")
    else:
        print(f"Dry run only; review report written to {report_path}")
    print(json.dumps(report["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

