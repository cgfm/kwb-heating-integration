#!/usr/bin/env python3
"""Add entity_id field to JSON configs.

This script is useful when Excel source files are not available but the
merged JSON config tree exists (one tree per version, with per-register
"name"/"index" as {"de": ..., "en": ...}). It regenerates language-independent
entity_id values that include the equipment index (e.g., sol_1_status).
"""

import json
from pathlib import Path

from entity_id_generation import compute_entity_id


def add_entity_ids_to_registers(registers: list[dict]) -> int:
    """Add or update entity_id field to registers list (includes index prefix).

    Also removes deprecated entity_index field if present.

    Returns count of registers updated.
    """
    updated = 0
    for reg in registers:
        address = reg.get("starting_address")
        if address is None:
            continue

        entity_id = compute_entity_id(reg)

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


def process_json_file(json_file: Path) -> bool:
    """Process a single JSON file to add entity_id fields.

    Returns True if file was modified.
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        modified = False

        if "universal_registers" in data:
            count = add_entity_ids_to_registers(data["universal_registers"])
            if count > 0:
                modified = True
                print(f"    Updated {count} universal registers")

        if "registers" in data:
            count = add_entity_ids_to_registers(data["registers"])
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
    for json_file in version_dir.rglob("*.json"):
        if json_file.name in ["value_tables.json", "alarm_codes.json"]:
            continue

        relative = json_file.relative_to(version_dir)
        print(f"    {relative}...")
        process_json_file(json_file)


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
