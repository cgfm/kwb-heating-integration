#!/usr/bin/env python3
"""One-time migration: merge each version's existing de/ and en/ JSON trees
into a single unified tree, using the same merge logic convert_modbusinfo.py
now uses when converting from Excel. Run once per repo, then delete this
script's usefulness is done - re-running is a no-op for already-migrated
versions (they no longer have de/en subdirectories to merge).
"""

import json
import shutil
import sys
from pathlib import Path

from convert_modbusinfo import ModbusInfoConverter

REGISTER_FILES = [
    "modbus_registers.json",
]


def load_registers(path: Path) -> list[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    for key in ("universal_registers", "registers"):
        if key in data:
            return data[key]
    return []


def load_value_tables(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8")).get("value_tables", {})


def load_alarm_codes(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8")).get("alarm_codes", [])


def migrate_version(version_dir: Path, converter: ModbusInfoConverter) -> bool:
    de_dir = version_dir / "de"
    en_dir = version_dir / "en"

    if not de_dir.exists() and not en_dir.exists():
        print(f"  {version_dir.name}: already merged, skipping")
        return False

    print(f"  Migrating {version_dir.name} (de={de_dir.exists()}, en={en_dir.exists()})...")

    # Discover every relative register file path across both language trees.
    relative_paths: set[Path] = set()
    for lang_dir in (de_dir, en_dir):
        if not lang_dir.exists():
            continue
        for path in lang_dir.rglob("*.json"):
            if path.name in ("value_tables.json", "alarm_codes.json"):
                continue
            relative_paths.add(path.relative_to(lang_dir))

    for rel in sorted(relative_paths):
        de_regs = load_registers(de_dir / rel)
        en_regs = load_registers(en_dir / rel)
        merged = converter.merge_bilingual_registers(de_regs, en_regs, f"{version_dir.name}/{rel}")

        out_path = version_dir / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        key = "universal_registers" if rel.name == "modbus_registers.json" else "registers"
        out_path.write_text(
            json.dumps({key: merged}, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    de_tables = load_value_tables(de_dir / "value_tables.json")
    en_tables = load_value_tables(en_dir / "value_tables.json")
    merged_tables = converter.merge_bilingual_value_tables(
        de_tables, en_tables, f"{version_dir.name}/value_tables.json"
    )
    (version_dir / "value_tables.json").write_text(
        json.dumps({"value_tables": merged_tables}, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    de_alarms = load_alarm_codes(de_dir / "alarm_codes.json")
    en_alarms = load_alarm_codes(en_dir / "alarm_codes.json")
    merged_alarms = converter.merge_bilingual_alarm_codes(
        de_alarms, en_alarms, f"{version_dir.name}/alarm_codes.json"
    )
    (version_dir / "alarm_codes.json").write_text(
        json.dumps({"alarm_codes": merged_alarms}, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    if de_dir.exists():
        shutil.rmtree(de_dir)
    if en_dir.exists():
        shutil.rmtree(en_dir)

    print(f"  {version_dir.name}: migrated {len(relative_paths)} register files, "
          f"{len(merged_tables)} value tables, {len(merged_alarms)} alarm codes")
    return True


def main():
    script_dir = Path(__file__).parent
    config_dir = script_dir.parent / "custom_components" / "kwb_heating" / "config" / "versions"

    converter = ModbusInfoConverter(script_dir / "modbusinfo", config_dir)

    version_dirs = sorted(config_dir.glob("v*"))
    if len(sys.argv) > 1:
        version_dirs = [config_dir / f"v{sys.argv[1]}"]

    print(f"Migrating {len(version_dirs)} version(s) in {config_dir}")
    migrated = 0
    for version_dir in version_dirs:
        if not version_dir.is_dir():
            continue
        if migrate_version(version_dir, converter):
            migrated += 1

    print(f"\nDone. Migrated {migrated} version(s).")


if __name__ == "__main__":
    main()
