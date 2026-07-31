## KWB Heating Integration v0.5.1

This release focuses on reliability, access-level handling, and better visibility into the underlying KWB Modbus registers.

### Highlights

- Expert Level now exposes the additional writable number, select, and switch entities as intended.
- Access-level changes made in the options flow are applied immediately after reload.
- Read-only registers are reliably represented as sensors.
- Duplicate logical registers are filtered before Home Assistant creates entities.
- Sensors, numbers, selects, and switches now expose consistent register metadata and raw values as state attributes.
- Missing German and English Yes/No value tables were added across the supported firmware configurations.
- Home Assistant diagnostics and a comprehensive German v25.7.1 Modbus register reference were added.

### Internal changes

- Removed obsolete register and language manager implementations.
- Streamlined the asynchronous coordinator, Modbus client, and config flow.
- Kept runtime dependencies within tested major-version ranges.

### Upgrade notes

No configuration migration is required. After updating, reload the KWB Heating integration or restart Home Assistant so platform entities are rebuilt with the corrected access-level filtering.

**Full Changelog**: [0.5.0...0.5.1](https://github.com/cgfm/kwb-heating-integration/compare/0.5.0...0.5.1)
