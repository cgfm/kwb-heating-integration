#!/usr/bin/env python3
"""Add entity_id field to JSON configs using English data.

This script is useful when Excel source files are not available but both
German and English JSON configs exist. It generates language-independent
entity_id values that include the equipment index (e.g., sol_1_status).
"""

import json
from pathlib import Path

from entity_id_generation import compute_entity_id


def load_english_data_from_json(en_dir: Path) -> dict[int, dict[str, str]]:
    """Load English register data (name and index) from JSON files.

    Returns a mapping of starting_address -> {"name": str, "index": str}.
    """
    english_data: dict[int, dict[str, str]] = {}

    # Process all JSON files in the English directory
    for json_file in en_dir.rglob("*.json"):
        if json_file.name in ["value_tables.json", "alarm_codes.json"]:
            continue  # Skip non-register files

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Handle different JSON structures
            registers = []
            if "universal_registers" in data:
                registers = data["universal_registers"]
            elif "registers" in data:
                registers = data["registers"]

            for reg in registers:
                address = reg.get("starting_address")
                name = reg.get("name")
                index = reg.get("index")
                if address is not None and name:
                    entry = {"name": str(name).strip()}
                    if index:
                        entry["index"] = str(index).strip()
                    english_data[int(address)] = entry

        except Exception as e:
            print(f"  Warning: Could not process {json_file}: {e}")

    return english_data


def add_entity_ids_to_registers(registers: list[dict], english_data: dict[int, dict[str, str]]) -> int:
    """Add or update entity_id field to registers list (includes index prefix).

    Also removes deprecated entity_index field if present.

    Returns count of registers updated.
    """
    updated = 0
    for reg in registers:
        address = reg.get("starting_address")
        if address is None:
            continue

        entity_id = compute_entity_id(reg, english_data)

        # Check if update is needed
        current_entity_id = reg.get("entity_id", "")
        has_entity_index = "entity_index" in reg
        needs_update = (current_entity_id != entity_id) or has_entity_index

        if entity_id and needs_update:
            # Rebuild register with updated entity_id and without entity_index
            new_reg = {}
            for key, value in reg.items():
                if key == "entity_index":
                    continue  # Remove deprecated field
                if key == "entity_id":
                    continue  # Skip old entity_id, we'll insert the new one
                new_reg[key] = value
                if key == "name":
                    new_reg["entity_id"] = entity_id
            reg.clear()
            reg.update(new_reg)
            updated += 1

    return updated


def process_json_file(json_file: Path, english_data: dict[int, dict[str, str]]) -> bool:
    """Process a single JSON file to add entity_id fields.

    Returns True if file was modified.
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        modified = False

        # Handle different JSON structures
        if "universal_registers" in data:
            count = add_entity_ids_to_registers(data["universal_registers"], english_data)
            if count > 0:
                modified = True
                print(f"    Updated {count} universal registers")

        if "registers" in data:
            count = add_entity_ids_to_registers(data["registers"], english_data)
            if count > 0:
                modified = True
                print(f"    Updated {count} registers")

        if modified:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True

    except Exception as e:
        print(f"  Error processing {json_file}: {e}")

    return False


def process_version(version_dir: Path) -> None:
    """Process a version directory to add entity_id fields."""
    en_dir = version_dir / "en"
    de_dir = version_dir / "de"

    if not en_dir.exists():
        print(f"  No English directory found, skipping")
        return

    print(f"  Loading English data from {en_dir}...")
    english_data = load_english_data_from_json(en_dir)
    print(f"  Loaded {len(english_data)} English entries")

    # Process both language directories
    for lang_dir in [de_dir, en_dir]:
        if not lang_dir.exists():
            continue

        print(f"  Processing {lang_dir.name}/...")

        for json_file in lang_dir.rglob("*.json"):
            if json_file.name in ["value_tables.json", "alarm_codes.json"]:
                continue

            relative = json_file.relative_to(lang_dir)
            print(f"    {relative}...")
            process_json_file(json_file, english_data)


def main():
    """Main entry point."""
    import sys

    # Default to custom_components config directory
    script_dir = Path(__file__).parent.parent
    config_dir = script_dir / "custom_components" / "kwb_heating" / "config" / "versions"

    # Allow specifying a specific version
    if len(sys.argv) > 1:
        version = sys.argv[1]
        version_dirs = [config_dir / f"v{version}"]
    else:
        # Process all versions
        version_dirs = sorted(config_dir.glob("v*"))

    print("Adding entity_id fields to JSON configs")
    print(f"Config directory: {config_dir}")
    print("=" * 60)

    for version_dir in version_dirs:
        if not version_dir.is_dir():
            continue

        print(f"\nProcessing {version_dir.name}...")
        process_version(version_dir)

    print("\n" + "=" * 60)
    print("Done!")


if __name__ == "__main__":
    main()
