#!/usr/bin/env python3
"""Safely migrate legacy DE/EN KWB trees to one multilingual tree per version."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any

try:
    from config_validation import load_json, registers_from, validate_or_raise
    from multilingual_config import merge_language_version, new_report
except ImportError:  # Imported as a package module.
    from .config_validation import load_json, registers_from, validate_or_raise
    from .multilingual_config import merge_language_version, new_report


def _register_membership(language_root: Path) -> set[tuple[Any, ...]]:
    members: set[tuple[Any, ...]] = set()
    for path in language_root.rglob("*.json"):
        relative_path = path.relative_to(language_root).as_posix()
        for register in registers_from(load_json(path)):
            members.add(
                (
                    relative_path,
                    register.get("parameter"),
                    register.get("starting_address"),
                    register.get("entity_id"),
                )
            )
    return members


def _unified_membership(version_root: Path) -> set[tuple[Any, ...]]:
    members: set[tuple[Any, ...]] = set()
    for path in version_root.rglob("*.json"):
        relative_path = path.relative_to(version_root).as_posix()
        for register in registers_from(load_json(path)):
            members.add(
                (
                    relative_path,
                    register.get("parameter"),
                    register.get("starting_address"),
                    register.get("entity_id"),
                )
            )
    return members


def build_migration(
    source_root: Path,
    destination_root: Path,
    *,
    resolve_existing_table_key_gaps: bool,
) -> dict[str, Any]:
    """Build and validate a migration without changing the source tree."""
    report = new_report(
        "Audit of the one-tree multilingual migration from canonical DE/EN history."
    )
    report["coverage_identity_fields"] = [
        "relative_file",
        "parameter",
        "starting_address",
        "entity_id",
    ]
    report["coverage"] = {}
    versions = sorted(
        path
        for path in source_root.glob("v*")
        if (path / "de").is_dir() and (path / "en").is_dir()
    )
    if not versions:
        raise ValueError(f"No legacy DE/EN version trees found below {source_root}")

    for source_version in versions:
        destination_version = destination_root / source_version.name
        merge_language_version(
            source_version,
            destination_version,
            report,
            resolve_existing_table_key_gaps=resolve_existing_table_key_gaps,
        )
        de_members = _register_membership(source_version / "de")
        en_members = _register_membership(source_version / "en")
        unified_members = _unified_membership(destination_version)
        missing = (de_members | en_members) - unified_members
        extra = unified_members - (de_members | en_members)
        report["coverage"][source_version.name] = {
            "old_de_registers": len(de_members),
            "old_en_registers": len(en_members),
            "old_union_registers": len(de_members | en_members),
            "new_unified_registers": len(unified_members),
            "missing_from_unified": len(missing),
            "new_identity_records": len(extra),
        }
        if missing or extra:
            report["items"].append(
                {
                    "kind": "migration_coverage_failure",
                    "blocking": True,
                    "firmware_version": source_version.name,
                    "missing": [list(item) for item in sorted(missing, key=str)],
                    "extra": [list(item) for item in sorted(extra, key=str)],
                }
            )
            report["summary"]["blocking_items"] += 1

    validate_or_raise(destination_root)
    report["blocking_review_required"] = bool(report["summary"]["blocking_items"])
    return report


def _replace_legacy_versions(source_root: Path, staged_root: Path) -> None:
    """Install validated files, then remove only the obsolete language directories."""
    for staged_version in sorted(staged_root.glob("v*")):
        source_version = source_root / staged_version.name
        for path in sorted(staged_version.rglob("*.json")):
            relative_path = path.relative_to(staged_version)
            destination = source_version / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
    for staged_version in sorted(staged_root.glob("v*")):
        source_version = source_root / staged_version.name
        for language in ("de", "en"):
            legacy = source_version / language
            if legacy.is_dir():
                shutil.rmtree(legacy)


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
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
        default=script_dir / "multilingual_migration_audit.json",
    )
    parser.add_argument(
        "--resolve-existing-table-key-gaps",
        action="store_true",
        help=(
            "Resolve audited legacy raw-key coverage gaps as missing translations; "
            "new converter output must not use this migration-only option"
        ),
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Install the validated proposal and remove legacy de/en directories.",
    )
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="kwb-multilingual-migration-") as temp_dir:
        staged_root = Path(temp_dir) / "versions"
        report = build_migration(
            args.root,
            staged_root,
            resolve_existing_table_key_gaps=args.resolve_existing_table_key_gaps,
        )
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        if args.write:
            if report["blocking_review_required"]:
                print(f"Refusing to migrate: blocking items are listed in {args.report}")
                return 2
            _replace_legacy_versions(args.root, staged_root)
            validate_or_raise(args.root)
            print(f"Migrated canonical firmware trees below {args.root}")
        else:
            print(f"Dry run only; migration audit written to {args.report}")
        print(json.dumps(report["coverage"], indent=2))
        print(json.dumps(report["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
