# KWB Heating Integration - Test Plan

## Bug Fix #1: Connection leak on config validation (`config_flow.py`)

**What was fixed:** `validate_input()` did not close the Modbus connection after testing, leaking a connection on every config flow attempt.

**Fix:** Added `finally: await client.disconnect()` block.

### Test Cases

| # | Test Case | Steps | Expected Result |
|---|-----------|-------|-----------------|
| 1.1 | Successful connection test closes client | 1. Mock `KWBModbusClient` with successful `connect()` and `test_connection()` returning `True`<br>2. Call `validate_input()` with valid TCP data<br>3. Assert `client.disconnect()` was called | `disconnect()` called exactly once |
| 1.2 | Failed connection test still closes client | 1. Mock `KWBModbusClient` where `test_connection()` returns `False`<br>2. Call `validate_input()`<br>3. Assert `disconnect()` was called despite `CannotConnect` being raised | `CannotConnect` raised AND `disconnect()` called |
| 1.3 | Exception during connect still closes client | 1. Mock `KWBModbusClient` where `connect()` raises `OSError`<br>2. Call `validate_input()`<br>3. Assert `disconnect()` was called | `CannotConnect` raised AND `disconnect()` called |
| 1.4 | Multiple config flow attempts don't accumulate connections | 1. Run `validate_input()` 3 times (mix of success/failure)<br>2. Verify no open connections remain | Each call results in exactly one `disconnect()` |

### Manual Verification
- In HA, go to Settings > Integrations > Add Integration > KWB Heating
- Enter wrong IP, submit -> verify no lingering connections in logs
- Enter correct IP, complete setup -> verify clean connection lifecycle in debug logs

---

## Bug Fix #2: Silent data corruption on value table lookup miss (`data_conversion.py`)

**What was fixed:** `_convert_to_value_table()` returned `0` as a fallback when a value was not found, potentially writing an incorrect value to the heating hardware.

**Fix:** Now raises `ValueError` with a descriptive message listing available values.

### Test Cases

| # | Test Case | Steps | Expected Result |
|---|-----------|-------|-----------------|
| 2.1 | Valid value table lookup works | 1. Create `KWBDataConverter` with a value table `{"0": "Off", "1": "On"}`<br>2. Call `_convert_to_value_table("On", "test_table")` | Returns `1` |
| 2.2 | Invalid value raises ValueError | 1. Create converter with table `{"0": "Off", "1": "On"}`<br>2. Call `_convert_to_value_table("Invalid", "test_table")` | Raises `ValueError` with message containing `"Invalid"` and available values |
| 2.3 | Unknown format fallback still works | 1. Call `_convert_to_value_table("Unknown (42)", "test_table")` | Returns `42` (extracted from unknown format) |
| 2.4 | Invalid unknown format raises ValueError | 1. Call `_convert_to_value_table("Unknown (abc)", "test_table")` | Raises `ValueError` |
| 2.5 | Empty value table raises ValueError | 1. Create converter with empty table `{}`<br>2. Call `_convert_to_value_table("anything", "empty_table")` | Raises `ValueError` |

### Manual Verification
- In HA, try writing an invalid select option via the Developer Tools > Services
- Verify an error is shown to the user instead of silently writing 0 to the boiler

---

## Bug Fix #3: Write access check ignored `expert_level` (`coordinator.py`)

**What was fixed:** `async_write_register()` only checked `register.get("user_level")` for write permission. Registers writable only at expert level were incorrectly rejected even when the configured access level was `ExpertLevel`.

**Fix:** Now checks `expert_level` or `user_level` depending on the configured access level.

### Test Cases

| # | Test Case | Steps | Expected Result |
|---|-----------|-------|-----------------|
| 3.1 | UserLevel can write user_level=readwrite register | 1. Set config `access_level = "UserLevel"`<br>2. Register has `user_level: "readwrite"`<br>3. Call `async_write_register(addr, value)` | Write succeeds |
| 3.2 | UserLevel cannot write expert-only register | 1. Set config `access_level = "UserLevel"`<br>2. Register has `user_level: "read"`, `expert_level: "readwrite"`<br>3. Call `async_write_register(addr, value)` | Write rejected, returns `False`, error logged |
| 3.3 | ExpertLevel can write expert_level=readwrite register | 1. Set config `access_level = "ExpertLevel"`<br>2. Register has `user_level: "read"`, `expert_level: "readwrite"`<br>3. Call `async_write_register(addr, value)` | Write succeeds |
| 3.4 | ExpertLevel cannot write read-only register | 1. Set config `access_level = "ExpertLevel"`<br>2. Register has `expert_level: "read"`<br>3. Call `async_write_register(addr, value)` | Write rejected, returns `False` |
| 3.5 | Non-existent register address returns False | 1. Call `async_write_register(99999, value)` with address not in `_registers` | Returns `False`, error logged |

### Manual Verification
- Configure integration with ExpertLevel access
- Verify that expert-only writable entities (numbers, selects, switches) show as controllable in HA
- Reconfigure to UserLevel -> verify those same entities become read-only

---

## Bug Fix #4: Update errors silently swallowed (`coordinator.py`)

**What was fixed:** `_async_update_data()` caught all exceptions and returned `{}` with a warning log. This prevented HA's `DataUpdateCoordinator` from tracking failures (entities stayed "available" even when communication was broken).

**Fix:** Now raises `UpdateFailed`, which HA uses to mark entities as unavailable and track failure counts.

### Test Cases

| # | Test Case | Steps | Expected Result |
|---|-----------|-------|-----------------|
| 4.1 | Successful update returns data | 1. Mock successful Modbus reads<br>2. Call `_async_update_data()` | Returns dict with processed register data |
| 4.2 | Connection error raises UpdateFailed | 1. Mock `modbus_client.read_batch_registers()` raising `ConnectionError`<br>2. Call `_async_update_data()` | Raises `UpdateFailed` |
| 4.3 | Timeout raises UpdateFailed | 1. Mock read raising `asyncio.TimeoutError`<br>2. Call `_async_update_data()` | Raises `UpdateFailed` |
| 4.4 | Generic exception raises UpdateFailed | 1. Mock read raising `RuntimeError`<br>2. Call `_async_update_data()` | Raises `UpdateFailed` with original exception chained |
| 4.5 | HA marks entities unavailable after UpdateFailed | 1. Simulate 2+ consecutive `UpdateFailed` raises<br>2. Check `coordinator.last_update_success` | `last_update_success` is `False`, entity states show "unavailable" |
| 4.6 | Recovery after transient failure | 1. Raise `UpdateFailed` on first call<br>2. Return valid data on second call<br>3. Check entity states | Entities become "available" again |

### Manual Verification
- Disconnect the KWB heating system from the network
- Verify entities show as "unavailable" in HA within one update cycle
- Reconnect -> verify entities recover automatically

---

## Bug Fix #5: OptionsFlowHandler used deprecated `self._config_entry` (`config_flow.py`)

**What was fixed:** Old code stored `config_entry` as `self._config_entry` with a workaround for a deprecated HA attribute, then used a fallback chain with `getattr()`.

**Fix:** Uses `self.config_entry` directly (modern HA pattern, `OptionsFlowHandler()` with no arguments).

### Test Cases

| # | Test Case | Steps | Expected Result |
|---|-----------|-------|-----------------|
| 5.1 | Options flow opens correctly | 1. Set up a config entry<br>2. Call `async_get_options_flow(config_entry)`<br>3. Call `async_step_init()` on the handler | Form shown with current equipment values |
| 5.2 | Options flow reads current config | 1. Create config entry with `heating_circuits=2, buffer_storage=1`<br>2. Open options flow<br>3. Verify form defaults | Form defaults match stored config values |
| 5.3 | Options flow saves changes | 1. Open options flow<br>2. Submit with `heating_circuits=3`<br>3. Check `entry.options` | Options updated with new value |
| 5.4 | Device name update persists | 1. Open options flow<br>2. Change device name to "My Boiler"<br>3. Check `entry.data` and `entry.title` | Both data and title updated with new name |
| 5.5 | No deprecation warnings in logs | 1. Complete a full options flow<br>2. Check HA logs for deprecation warnings | No deprecation warnings related to `config_entry` |

### Manual Verification
- Go to Settings > Integrations > KWB Heating > Configure
- Change equipment counts and device name
- Verify changes persist after HA restart

---

## Bug Fix #6: Connection not closed on unload (`__init__.py`)

**What was fixed:** `async_unload_entry()` only popped the coordinator from `hass.data` without disconnecting the Modbus TCP/RTU connection.

**Fix:** Now calls `await coordinator.modbus_client.disconnect()` before cleanup.

### Test Cases

| # | Test Case | Steps | Expected Result |
|---|-----------|-------|-----------------|
| 6.1 | Unload disconnects Modbus client | 1. Set up integration (coordinator stored in `hass.data`)<br>2. Call `async_unload_entry()`<br>3. Assert `modbus_client.disconnect()` was called | `disconnect()` called, returns `True` |
| 6.2 | Unload cleans up hass.data | 1. Set up integration<br>2. Call `async_unload_entry()`<br>3. Check `hass.data[DOMAIN]` | Entry ID no longer in `hass.data[DOMAIN]` |
| 6.3 | Failed platform unload skips disconnect | 1. Mock `async_unload_platforms()` returning `False`<br>2. Call `async_unload_entry()` | `disconnect()` NOT called, coordinator remains in `hass.data`, returns `False` |
| 6.4 | Reload performs clean disconnect + reconnect | 1. Call `async_reload_entry()`<br>2. Verify disconnect then reconnect sequence | `disconnect()` called during unload, new connection established during setup |
| 6.5 | Integration removal cleans up connection | 1. Remove integration via HA UI<br>2. Verify no orphaned Modbus connections | `disconnect()` called, no open sockets/serial ports remain |

### Manual Verification
- Go to Settings > Integrations > KWB Heating
- Click "..." > Reload -> check debug logs for disconnect/reconnect
- Remove integration entirely -> verify no lingering connections in netstat/logs
