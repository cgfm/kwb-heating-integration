# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0] - 2026-07-13

### Breaking Changes

#### Entity IDs Are Now Derived From the KWB Parameter Path, Not the Display Name

**This release changes the entity_id/unique_id of nearly every entity. Update your automations, scripts, and dashboards after upgrading.**

Entity IDs were previously generated from the (translated) English display name plus equipment index. Several distinct KWB registers share an identical display name - for example, a boolean pump-status register and a completely separate pump-speed-percentage register are both simply called "Pump 1" in KWB's own documentation. Two registers with the same name and equipment index generated the same entity_id, and Home Assistant silently kept only one of the two colliding entities - the other was never created, with no error or warning anywhere.

Entity IDs are now derived from each register's own KWB `parameter` path (e.g. `SOL.pumpe_1_steuerstufe`), which is the manufacturer's stable, unique key, combined with the equipment index where applicable. This is the same value already exposed as the `parameter` field and used internally as the register's canonical identity - it just wasn't previously used to name the entity itself.

**Impact**: every entity's `entity_id` changes on upgrade. For example, `sensor.cf2_sol_1_pump_1` becomes `sensor.cf2_sol_1_sol_pumpe_1_steuerstufe`.

**Migration**: after upgrading, check **Developer Tools → States** for your device prefix and update any automations, scripts, or Lovelace cards that reference the old entity IDs.

**Why**: this is the only way to guarantee entity IDs never silently collide again. A display name is only meant to be human-readable, not unique; the KWB parameter path already is unique by construction.

### Fixed
- Solar pump modulation-level sensors (`SOL.pumpe_1_steuerstufe`, `SOL.pumpe_2_steuerstufe`) were silently never created due to an entity_id collision with the boolean pump-status register sharing the same display name ("Pump 1")
- Same silent-collision issue for the main boiler pump's modulation level (`KSM.kesselpumpe_steuerstufe`), the "simple" boiler status variant (`KSM.kesselstatus_anzeige_simple`), the CF-model boiler temperature setpoint (`CF2.kesseltemp_soll_1`), and the pellet-module full-load-hours counter (`CF2.PM_Betriebsminuten_Summe`)
- EasyAir Plus "silent mode" time-window registers (`EAPDEV.fluester1_beginn`/`fluester2_beginn`/etc., up to 8 units) all collapsed onto a single entity, because the equipment-index lookup only consulted the English-language sheet, which is missing these rows entirely for this device. The lookup now falls back to the register's own index when the English data has no entry for that address
- `%` in a register's display name was silently stripped during entity_id sanitization instead of being converted to a word (unlike `&`/`@`, which already were)
- **Transfer stations produced no entities at all**, even though "Number of transfer stations" was a fully working option in the setup/options UI. The equipment type was never added to `AsyncModularRegisterManager.EQUIPMENT_KEY_CONFIG`, so the register manager silently never loaded `equipment/transfer_station.json` regardless of the configured count. Also removed a stray duplicate `uebergabestation.json` (v25.7.1/de only) that defined the same registers under KWB's German sheet name instead of the standard English filename. This is additive, not breaking - no transfer-station entities existed before, so none are renamed.
- `entity.py` referenced an undefined `_LOGGER` in the fallback path used when a register has neither `entity_id` nor `parameter` (e.g. an incomplete hand-added custom register) - this raised `NameError` and crashed entity setup instead of logging a warning and falling back to an address-based ID
- Re-adding an already-configured device in the config flow could show a generic "Unknown error" instead of properly aborting with "already configured" - `_abort_if_unique_id_configured()` was called inside a `try`/`except Exception` block, and the `AbortFlow` it raises is itself an `Exception` subclass, so it was being caught by the broad handler. The uniqueness check now runs before the connection is even tested, both fixing this and failing faster for duplicate devices
- The pymodbus `unit=`/`slave=` keyword-argument version-compatibility detection in `modbus_client.py` was computed but never actually used - every single register read/write retried the full unit→slave→bare fallback cascade on every call instead of reusing the previously-detected keyword, silently costing 1-2 wasted failed calls per register on every poll cycle
- The "Last Firewood Fire" sensor (and the new fuel-split sensors below) are now gated purely on whether their required registers actually exist for the connected device (looked up by `parameter`, e.g. `CF2.betriebsmodus`), instead of a hardcoded device-type allowlist. This fixed a real, pre-existing mismatch: `FIREWOOD_DEVICE_TYPES` listed "KWB Multifire" as supported, but Multifire has never actually had the register (`CF2.kesselstatus_anzeige_sh`) that sensor needs, so it was silently never created for Multifire despite being documented as supported. Register presence is now the single source of truth for both device-type eligibility and register addresses, removing a second, independently-maintained (and in this case incorrect) copy of the same information

### Added
- KWB firmware v26.6.1 support (register definitions and version mapping), including the new solar program-select register (`SOL.programm`)
- **Pellet/log-wood energy split sensors** for dual-fuel Combifire-family devices: `sensor.<prefix>_pellet_energy_total` and `sensor.<prefix>_log_wood_energy_total`. KWB only exposes one combined lifetime heat-output counter (`KSM.waermemenge_gesamt_kwh`) for these boilers - there's no separate per-fuel energy register - so these sensors split it after the fact using the operating-mode register (`CF2.betriebsmodus`): each increase in the combined counter is attributed to whichever fuel the mode register reports as active at that moment. Off and relay-test periods aren't attributed to either fuel. Both are lifetime cumulative totals (`state_class: total_increasing`) - wrap them in a Home Assistant [Utility Meter](https://www.home-assistant.io/integrations/utility_meter/) helper (daily cycle) to get daily energy per fuel, or add them to the Energy Dashboard's "Individual devices" section directly for lifetime tracking. Like the Last Firewood Fire sensor, these are created purely based on whether the required registers exist for your specific device - not a hardcoded device-type list.

### Changed
- `convert_modbusinfo.py` and `add_entity_ids_from_json.py` now share one entity_id-generation module (`modbusinfoConverter/entity_id_generation.py`) instead of two independently-maintained copies of the same logic, so the two tools can no longer drift into different naming schemes
- Config flow equipment-count ranges (min/max per equipment type) are now defined once in `EQUIPMENT_RANGES` and shared between the initial setup schema and the options-flow schema, instead of being duplicated across both

### Removed
- Deleted `register_manager.py` and `modular_register_manager.py` (unused synchronous duplicates of `AsyncModularRegisterManager`) and `complete_modular_setup.py` (a stale one-off migration script referencing a `kwb_config.json` that no longer existed) - all three were confirmed dead code, imported by nothing
- Deleted `icon_utils.get_device_icon()`, `get_category_icon()`, and `extract_equipment_info()`, and the now-unreferenced `DEVICE_TYPE_ICONS` constant they were the only consumer of - none were called anywhere
- Deleted `_invoke_with_unit_kwarg()` from `modbus_client.py` (superseded by `_invoke_read`/`_invoke_write`, and never actually called by anything)
- Deleted several other unused constants from `const.py` (`SYSTEM_REGISTER_MAPPING`, `ENTITY_CATEGORIES`, `MODBUS_FUNCTION_CODES`, `ERROR_CONNECTION`, `ERROR_INVALID_DATA`, `ERROR_TIMEOUT`, `ERROR_CONFIG`, `DATA_TYPES`) and the dead imports of them in `modbus_client.py` and `async_modular_register_manager.py`
- Deleted the unused module-level `STEP_DEVICE_DATA_SCHEMA` in `config_flow.py`, superseded by a dynamically-built schema in `async_step_device()`

## [0.4.2] - 2026-02-06

### Changed
- **Last Firewood Fire sensor**: Now uses boiler status register (8212 - "Status Stückholz") instead of operating mode register (8244) for more accurate firewood fire detection
- Enhanced firewood detection with comprehensive boiler status values (Anheizen, Zünden, Heizen, Feuerhaltung, etc.)
- Updated sensor attributes: `operating_mode` → `boiler_status`, `betriebsmodus` → `kesselstatus`

### Fixed
- **Invalid entity IDs**: Entity IDs containing double underscores (`__`) or trailing underscores (e.g., from register names with parentheses or special characters like `%`) are now properly sanitized, fixing "Invalid entity ID" errors that prevented equipment entities (heating circuits, buffer storage, etc.) from loading
- **Timezone-naive datetime error**: Last Firewood Fire sensor now uses timezone-aware UTC timestamps, fixing `ValueError: missing timezone information` for `SensorDeviceClass.TIMESTAMP` entities

## [0.4.1] - 2026-02-01

### Added
- New `KWBBaseEntity` base class for consistent entity ID and name generation across all platforms
- Centralized `is_boolean_value_table()` method in `KWBDataConverter` for better code organization

### Changed
- Refactored entity platforms (sensor, switch, number, select) to use shared `KWBBaseEntity` base class
- Reduced code duplication across entity platform files (~250 lines removed)
- Improved exception handling in initial data refresh

## [0.4.0] - 2026-01-18

### Breaking Changes

#### Entity ID Changes for Equipment Registers

**This release includes breaking changes that will affect entity IDs for heating circuits, buffer storage, and related equipment.**

Equipment index prefixes have been standardized to German across all language configurations:

| Equipment Type | Old (EN) | New (All Languages) |
|----------------|----------|---------------------|
| Heating Circuits | `HC 1.1` | `HK 1.1` |
| Buffer Storage | `BUF 0` | `PUF 0` |
| DHW Storage | `DHWC 1` | `BWS 1` |
| Secondary Heat | `SHS 1` | `ZWQ 1` |
| Circulation | `CIR 0` | `ZIR 0` |
| Boiler Sequence | `BS 1` | `KFS 1` |
| Heat Meters | `HM 0` | `WMZ 0` |

**Impact**: Entity IDs for equipment-related sensors will change. For example:
- Old: `sensor.easyfire_heating_circuit_1_1_forward_flow_temp`
- New: `sensor.easyfire_heizkreis_1_1_forward_flow_temp`

**Migration**: After updating, you will need to update any automations, scripts, dashboards, or other configurations that reference the old entity IDs.

**Reason for change**: KWB's internal system uses German identifiers. Standardizing on German prefixes ensures:
1. Consistent entity IDs regardless of selected language
2. Entity IDs remain stable when switching languages
3. Better alignment with KWB's source data (ModbusInfo files)

#### Why German Prefixes?

KWB is an Austrian company, and their Modbus register definitions use German naming internally. The `parameter` field in register definitions (e.g., `HK.i_vorlauf_temperatur.value`) is German regardless of the language selected. Using German equipment prefixes (HK, PUF, BWS, etc.) provides:

- **Stability**: Entity IDs don't change when switching between German and English
- **Consistency**: Matches KWB's internal register naming convention
- **Predictability**: Users can expect the same entity IDs across all installations

Note: The **display names** (entity names shown in the UI) are still localized based on your language selection. Only the **entity IDs** use German prefixes.

### Added
- "Last Firewood Fire" computed sensor for Combifire/Multifire/CF devices with firewood (Stückholz) support
- Language-aware sensor naming for computed sensors

### Fixed
- Equipment registers not loading when using English language configuration (Issue #5)
- Duplicate unique ID errors for equipment registers

## [0.3.5] - 2026-01-09

### Changed
- Updated register loading to use modbus_registers.json
- Added boolean value table check for switch entities

## [0.3.4] - 2026-01-08

### Added
- Modbus registers and value tables for version 21.4.0

### Fixed
- Missing handling for signed integers
- Corrected reading 32-bit registers with non-empty unit
- Binary sensor fixes

## [0.3.0] - 2026-01-07

### Added
- Multi-version support (v21.4.0, v22.7.1, v24.7.1, v25.7.1)
- Multi-language support (German, English)
- Automatic version detection via Modbus register 8192
- Version and language manager components
- Configuration files for version 24.7.1 (DE/EN)

### Changed
- Renamed "Kesselstatus" to "Pelletkesselstatus" for consistency

## [0.2.0] - 2026-01-05

### Added
- Equipment-based configuration (heating circuits, buffer storage, etc.)
- Support for KWB Easyfire, Multifire, Combifire, Pelletfire+, CF1, CF1.5, CF2, EasyAir Plus
- UserLevel and ExpertLevel access control
- ModbusInfo Converter tool for generating configuration from KWB Excel files

## [0.1.0] - 2026-01-01

### Added
- Initial release
- Modbus TCP support for KWB heating systems
- Basic sensor and control entities
- UI-based configuration via Config Flow
