## KWB Heating Integration v0.5.2

This release expands firmware and connection support, adds robust dual-fuel energy accounting for combination boilers, and fixes entity creation and register-selection issues found in real Home Assistant deployments.

### Highlights

- Added full KWB firmware v26.6.1 configuration, including refined stable EasyAir entity IDs.
- Added persistent pellet and log-wood energy totals for capable combination boilers, plus a disabled-by-default diagnostic total for energy that cannot be attributed safely.
- Added RTU-over-TCP support for ser2net and RS485-to-Ethernet gateways.
- Consolidated German and English firmware data into one canonical multilingual schema while keeping entity identities language-independent.
- Improved equipment/register discovery across firmware versions, including circulation, boiler sequence, DHW, heat meters, secondary buffers, and transfer stations.

### Home Assistant 2026.8 entity-ID fix

The new FuelSplit sensors now request stable English entity IDs correctly:

- `sensor.<device>_pellet_energy_total`
- `sensor.<device>_log_wood_energy_total`
- `sensor.<device>_fuel_energy_unattributed`

Home Assistant had previously ignored the integration's `_attr_entity_id` field and generated localized IDs containing area, device, and translated display names. Version 0.5.2 uses the supported `entity.entity_id` suggestion path.

Existing automatically generated FuelSplit beta IDs are migrated in place using their unchanged unique IDs. Registry metadata, device links, history relationships, and enable/disable choices are preserved. User-customized IDs are left unchanged, and target collisions are reported without overwriting another entity or silently creating an `_2` ID.

Last Firewood Fire used the same unsupported field for fresh installations. Its creation path is corrected while its published entity ID and unique ID remain unchanged; no migration is performed for existing Last Firewood Fire entities.

### Additional fixes

- Corrected duplicate register IDs and retained runtime collisions with deterministic address-based fallbacks.
- Fixed circulation slot/prefix discovery and firmware-dependent equipment indexing.
- Fixed language changes so all localized runtime data is rebuilt on reload.
- Improved Last Firewood Fire discovery by checking the required register capability instead of a fixed model-name list.
- Fixed config-flow duplicate handling and PyModbus `unit`/`slave` keyword reuse.
- Kept FuelSplit accounting synchronized with poll-interval changes while preserving totals across source resets and long observation gaps.

### Upgrade notes

No config-entry migration or reconfiguration is required. Install the update and restart Home Assistant or reload the KWB Heating integration.

The FuelSplit registry migration is deliberately conservative: automatic beta IDs are corrected, customized or uncertain IDs remain untouched, and collisions are logged for manual resolution.

**Full Changelog**: [0.5.1...0.5.2](https://github.com/cgfm/kwb-heating-integration/compare/0.5.1...0.5.2)
