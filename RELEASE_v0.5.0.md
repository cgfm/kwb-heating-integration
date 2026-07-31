## KWB Heating Integration v0.5.0

> **This release contains breaking changes. Please read carefully before updating.**

---

### Breaking Changes

#### Stable, Language-Independent Entity IDs

Entity IDs are now generated from stable, language-independent data. This means entity IDs **will change** after updating if you are coming from v0.4.x.

**Impact**: Any automations, scripts, dashboards, or ha-floorplan configurations referencing old entity IDs must be updated.

**Benefit**: Entity IDs are now **permanent** — they will no longer change when you switch between German and English, or when display names are updated in future releases.

---

### New Features

#### Modbus RTU / Serial Support
KWB heating systems that do not expose Modbus TCP (port 502) can now be connected via a USB/RS485 adapter. Serial connections are fully supported alongside the existing TCP mode and can be configured during setup.

#### ha-floorplan Integration
An SVG boiler graphic is now included for use with [ha-floorplan](https://ha-floorplan.github.io/), including dark mode support.

#### Firmware v25.7.1 Support
Added Modbus register definitions for firmware version 25.7.1.

---

### Bug Fixes

- **Duplicate entities**: Fixed a bug that created entities with `_2` suffixes when changing the language setting, causing duplicates in Home Assistant.
- **Config flow error**: Fixed a `NameError` in `config_flow.py` that prevented adding new devices in some cases.
- **Language auto-detection**: Fixed incorrect fallback to German instead of English when no language could be detected.
- **Icon assignment**: Icons are now matched against the stable `entity_id` instead of the translated name, so icons are correctly assigned regardless of language.
- **Access level reload**: Changing the access level in the integration options now triggers a full reload, ensuring expert-level entities are loaded or removed correctly.
- **Register manager**: Fixed handling of language-specific prefixes in configuration files.
- **`system_ein_aus_t` value table**: Added missing value table across all supported firmware versions (de/en) to prevent errors on certain boiler states.

---

### Upgrade Notes

1. After updating, navigate to **Settings → Devices & Services → KWB Heating** and reload the integration.
2. Home Assistant will report missing entities — this is expected due to the entity ID changes.
3. Update your dashboards, automations, and scripts to use the new entity IDs.
4. New entity IDs follow the pattern: `sensor.<device_name>_<register_parameter>` and will remain stable going forward.

---

**Full Changelog**: [v0.4.2...v0.5.0](https://github.com/cgfm/KWB-Heating/compare/v0.4.2...v0.5.0)
