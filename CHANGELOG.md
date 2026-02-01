# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
