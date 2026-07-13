# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Home Assistant custom integration (HACS) for **KWB heating systems** via Modbus TCP/RTU. Domain: `kwb_heating`. The integration is entirely **data-driven**: register definitions live in versioned JSON files, not in Python code, and the coordinator assembles the right register set at runtime based on detected firmware version, selected language, device model, and configured equipment counts.

A second, independent tool (`modbusinfoConverter/`) converts KWB's official Excel ("ModbusInfo") documentation into the JSON configs consumed by the integration.

## Development Commands

There is no test suite, linter config, or CI in this repo (`requirements-dev.txt` lists `pytest`/`black`/`flake8`/`mypy`, but no config files or `tests/` directory exist — don't assume they're wired up).

Local end-to-end testing uses a dockerized Home Assistant instance, driven by `dev-helper.sh` (bash) / `dev-helper.ps1` (PowerShell):

```bash
docker compose up -d          # or: ./dev-helper.sh reset-full  (fresh HA + HACS install)
./dev-helper.sh restart       # restart the HA container after code changes
./dev-helper.sh reset-kwb     # wipe only the KWB config entry, keep HA running
./dev-helper.sh logs-kwb      # tail HA logs filtered to "kwb"
./dev-helper.sh status        # container + web UI health check
./dev-helper.sh open          # open http://localhost:8123
```

The container mounts `./custom_components/kwb_heating` directly into HA's `custom_components/`, so code edits take effect after `restart` (no rebuild needed). HA config state lives in `ha-config/` (gitignored).

### ModbusInfo converter

```bash
cd modbusinfoConverter
pip install openpyxl
python3 convert_modbusinfo.py                 # ModbusInfo-{lang}-V{version}.xlsx -> config/versions/
python3 json_to_excel.py [version]            # regenerate Excel from existing JSON (e.g. when source missing)
python3 add_entity_ids_from_json.py           # backfill entity_id fields into existing JSON configs
python3 inspect_excel.py                      # dump sheet names/headers/sample rows for debugging
```

Generated output goes to `modbusinfoConverter/config/versions/`; copy it into `custom_components/kwb_heating/config/versions/` to ship it (see `modbusinfoConverter/README.md` for the three copy strategies — full replace vs. single version/language).

## Architecture

### Runtime flow

`__init__.py` → `KWBDataUpdateCoordinator` (coordinator.py) is the center of everything:

1. On setup, it creates a `KWBModbusClient` (modbus_client.py) for the configured TCP/serial connection.
2. `VersionManager` (version_manager.py) detects firmware version by reading registers **8192/8193/8194** (major/minor/patch) over Modbus, with `closest_match` fallback to a known supported version.
3. `LanguageManager` (language_manager.py) resolves the active language: explicit user choice → HA locale → default (`en`) → first supported.
4. `AsyncModularRegisterManager` (async_modular_register_manager.py) loads the JSON register set for that (version, language) pair from `config/versions/vX.Y.Z/{de,en}/...`, filtered by:
   - **access level** (`UserLevel` vs `ExpertLevel`, from `register["user_level"]`/`["expert_level"]`)
   - **device type** (KWB model → `devices/*.json`, with universal registers always included first)
   - **equipment counts** (heating circuits, buffer storage, DHW storage, solar, etc. → `equipment/*.json`, index-filtered by count and 0- vs 1-based indexing per `EQUIPMENT_KEY_CONFIG`)
   - Deduplicated by `starting_address` (universal registers always win over device/equipment duplicates).
5. Coordinator polls on `update_interval`, batches reads via `modbus_client.read_batch_registers()`, and converts raw values via `KWBDataConverter` (data_conversion.py) — signed/unsigned handling, value-table enum lookup, scaling factors like `"1/10°C"`.
6. Platforms (`sensor.py`, `number.py`, `select.py`, `switch.py`) each call `coordinator._initialize_register_manager()` if needed, then create one entity per applicable register. All entity classes extend `KWBBaseEntity` (entity.py), which centralizes entity naming/unique-ID/entity_id generation.

Changing equipment counts or access level in Options triggers a full integration reload (`async_update_options` in `__init__.py`); other option changes just call `coordinator.async_update_config()` for a soft refresh.

### Entity ID stability (important, and the source of most breaking changes in CHANGELOG.md)

Entity IDs must stay stable across language switches and equipment-count changes, so they are derived from **English/German data-driven identifiers**, never from the currently-displayed (translated) name:

- Preferred: the register's own `entity_id` field from the JSON config.
- Fallback: the register's `parameter` field (KWB's internal dotted path, e.g. `HK.i_vorlauf_temperatur.value`), sanitized.
- Last resort: `register_{address}`.

Equipment entity IDs additionally get a German-derived equipment prefix + 1-based index (`buf_1`, `hc_1_1`, `dhwc_1`, ...) via `EQUIPMENT_KEY_CONFIG` in `async_modular_register_manager.py` — see `KWBDataUpdateCoordinator.generate_entity_unique_id()` and `KWBBaseEntity` for where this is assembled. Display *names* are still localized; only entity_id/unique_id are language-independent. Do not change this scheme without updating the CHANGELOG migration notes — HA appends `_2`/`_3` suffixes and silently breaks automations when IDs collide or shift.

### Config directory layout (per version/language)

```
custom_components/kwb_heating/config/versions/v{version}/{de,en}/
├── modbus_registers.json   # universal registers (all KWB systems)
├── value_tables.json       # enum -> localized text mappings
├── alarm_codes.json
├── devices/*.json          # per-model registers; CF1/CF1.5/CF2 inherit Combifire base + overrides
└── equipment/*.json        # per-equipment-type registers, indexed by "HK 1.1", "PUF 0", etc.
```

`version_mapping.json` and `language_config.json` (both in `custom_components/kwb_heating/config/`) drive fallback behavior in `VersionManager`/`LanguageManager`.

### Legacy code — do not extend

`register_manager.py` and `modular_register_manager.py` (synchronous versions) are **unused dead code** superseded by `AsyncModularRegisterManager`; nothing imports them. `complete_modular_setup.py` at the repo root was a one-off migration script referencing a `kwb_config.json` that no longer exists. Don't build on any of these three files — check actual imports before assuming a file is live.

### Raw values

Every sensor/select/switch exposes the pre-conversion register value as the `raw_value` attribute (see `KWBSensor.extra_state_attributes` in sensor.py) — this replaced older standalone `*_rohwert` entities (removed; see README.md "Raw Value Attribute" section for migration guidance if asked about it).
