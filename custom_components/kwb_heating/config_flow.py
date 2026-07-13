"""Config flow for KWB Heating integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_CONNECTION_TYPE,
    CONF_SLAVE_ID,
    CONF_ACCESS_LEVEL,
    CONF_UPDATE_INTERVAL,
    ACCESS_LEVELS,
    DEFAULT_PORT,
    DEFAULT_SLAVE_ID,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_ACCESS_LEVEL,
    CONF_DEVICE_TYPE,
    CONF_DEVICE_NAME,
    CONF_LANGUAGE,
    CONF_SERIAL_PORT,
    CONF_BAUDRATE,
    CONF_PARITY,
    CONF_STOPBITS,
    CONF_BYTESIZE,
    CONF_HEATING_CIRCUITS,
    CONF_BUFFER_STORAGE,
    CONF_DHW_STORAGE,
    CONF_SECONDARY_HEAT_SOURCES,
    CONF_CIRCULATION,
    CONF_SOLAR,
    CONF_BOILER_SEQUENCE,
    CONF_HEAT_METERS,
    CONF_TRANSFER_STATIONS,
    CONNECTION_TYPE_TCP,
    CONNECTION_TYPE_SERIAL,
    DEFAULT_BAUDRATE,
    DEFAULT_PARITY,
    DEFAULT_STOPBITS,
    DEFAULT_BYTESIZE,
)
from .modbus_client import KWBModbusClient

_LOGGER = logging.getLogger(__name__)

# Configuration constants  
# (Now imported from const.py)

# Device types from kwb_config.json
DEVICE_TYPES = {
    "KWB Easyfire": "KWB Easyfire",
    "KWB Multifire": "KWB Multifire",
    "KWB Pelletfire+": "KWB Pelletfire+",
    "KWB Combifire": "KWB Combifire",
    "KWB CF 2": "KWB CF 2",
    "KWB CF 1": "KWB CF 1",
    "KWB CF 1.5": "KWB CF 1.5",
    "KWB EasyAir Plus": "KWB EasyAir Plus",
}

# Language options
LANGUAGES = {
    "auto": "Automatic (use Home Assistant language)",
    "de": "Deutsch",
    "en": "English",
}

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_CONNECTION_TYPE, default=CONNECTION_TYPE_TCP): selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[CONNECTION_TYPE_TCP, CONNECTION_TYPE_SERIAL],
            translation_key="connection_type",
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    ),
})

STEP_TCP_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    vol.Optional(CONF_SLAVE_ID, default=DEFAULT_SLAVE_ID): vol.All(vol.Coerce(int), vol.Range(min=1, max=255)),
})

STEP_SERIAL_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_SERIAL_PORT): cv.string,
    vol.Optional(CONF_BAUDRATE, default=DEFAULT_BAUDRATE): vol.In([9600, 19200, 38400, 57600, 115200]),
    vol.Optional(CONF_PARITY, default=DEFAULT_PARITY): vol.In({"N": "None", "E": "Even", "O": "Odd"}),
    vol.Optional(CONF_STOPBITS, default=DEFAULT_STOPBITS): vol.In([1, 2]),
    vol.Optional(CONF_BYTESIZE, default=DEFAULT_BYTESIZE): vol.In([7, 8]),
    vol.Optional(CONF_SLAVE_ID, default=DEFAULT_SLAVE_ID): vol.All(vol.Coerce(int), vol.Range(min=1, max=255)),
})

# Maximum configurable count per equipment type, shared by the initial setup
# schema and the options-flow schema so the two can't silently drift apart.
EQUIPMENT_RANGES: dict[str, int] = {
    CONF_HEATING_CIRCUITS: 14,
    CONF_BUFFER_STORAGE: 15,
    CONF_DHW_STORAGE: 14,
    CONF_SECONDARY_HEAT_SOURCES: 14,
    CONF_CIRCULATION: 15,
    CONF_SOLAR: 14,
    CONF_BOILER_SEQUENCE: 8,
    CONF_HEAT_METERS: 36,
    CONF_TRANSFER_STATIONS: 14,
}

STEP_EQUIPMENT_DATA_SCHEMA = vol.Schema({
    vol.Optional(key, default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=max_count))
    for key, max_count in EQUIPMENT_RANGES.items()
})


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    connection_type = data.get(CONF_CONNECTION_TYPE, CONNECTION_TYPE_TCP)

    client = KWBModbusClient(
        connection_type=connection_type,
        host=data.get(CONF_HOST),
        port=data.get(CONF_PORT, DEFAULT_PORT),
        serial_port=data.get(CONF_SERIAL_PORT),
        baudrate=data.get(CONF_BAUDRATE, DEFAULT_BAUDRATE),
        parity=data.get(CONF_PARITY, DEFAULT_PARITY),
        stopbits=data.get(CONF_STOPBITS, DEFAULT_STOPBITS),
        bytesize=data.get(CONF_BYTESIZE, DEFAULT_BYTESIZE),
        slave_id=data.get(CONF_SLAVE_ID, DEFAULT_SLAVE_ID),
    )

    try:
        # Test connection by reading a basic register
        await client.connect()
        success = await client.test_connection()
        if not success:
            raise CannotConnect("Connection test failed")
        # Don't disconnect here - let the client handle cleanup automatically
    except Exception as exc:
        _LOGGER.error("Cannot connect to KWB heating system: %s", exc)
        raise CannotConnect from exc

    # Return info that you want to store in the config entry.
    if connection_type == CONNECTION_TYPE_SERIAL:
        title = f"KWB Heating ({data[CONF_SERIAL_PORT]})"
    else:
        title = f"KWB Heating ({data[CONF_HOST]})"
    return {
        "title": title,
        **data,
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for KWB Heating."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.data = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - connection type selection."""
        if user_input is not None:
            self.data[CONF_CONNECTION_TYPE] = user_input[CONF_CONNECTION_TYPE]
            if user_input[CONF_CONNECTION_TYPE] == CONNECTION_TYPE_SERIAL:
                return await self.async_step_serial()
            return await self.async_step_tcp()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
        )

    async def async_step_tcp(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle TCP connection settings."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self.data.update(user_input)

            # Set and check the unique ID *before* the try/except below - it
            # raises AbortFlow, which is itself an Exception subclass and
            # would otherwise be swallowed by the broad `except Exception`
            # into a generic "unknown" error instead of properly aborting.
            # Checking first also avoids testing the connection for a device
            # that's already configured.
            unique_id = f"{user_input[CONF_HOST]}_{user_input[CONF_SLAVE_ID]}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            try:
                await validate_input(self.hass, self.data)
                return await self.async_step_device()

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidHost:
                errors["host"] = "invalid_host"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="tcp",
            data_schema=STEP_TCP_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_serial(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle serial/RTU connection settings."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self.data.update(user_input)

            # See async_step_tcp for why this must happen before the try/except.
            unique_id = f"{user_input[CONF_SERIAL_PORT]}_{user_input[CONF_SLAVE_ID]}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            try:
                await validate_input(self.hass, self.data)
                return await self.async_step_device()

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="serial",
            data_schema=STEP_SERIAL_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle device type and access level selection."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            # Validate device name
            device_name = user_input.get(CONF_DEVICE_NAME, "").strip()
            if not device_name:
                errors[CONF_DEVICE_NAME] = "invalid_device_name"
            elif len(device_name) > 50:
                errors[CONF_DEVICE_NAME] = "device_name_too_long"
            else:
                self.data.update(user_input)
                # Move to equipment configuration step
                return await self.async_step_equipment()

        # Generate default device name suggestion based on device type
        suggested_name = ""
        if CONF_DEVICE_TYPE in self.data:
            device_type = self.data[CONF_DEVICE_TYPE]
            if device_type.startswith("KWB "):
                suggested_name = device_type[4:]  # Remove "KWB " prefix
            else:
                suggested_name = device_type

        # Create schema with default device name
        device_schema = vol.Schema({
            vol.Required(CONF_DEVICE_TYPE): vol.In(DEVICE_TYPES.keys()),
            vol.Required(CONF_DEVICE_NAME, default=suggested_name): cv.string,
            vol.Optional(CONF_ACCESS_LEVEL, default=DEFAULT_ACCESS_LEVEL): vol.In(ACCESS_LEVELS.keys()),
            vol.Optional(CONF_LANGUAGE, default="auto"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["auto", "de", "en"],
                    translation_key="language",
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.All(vol.Coerce(int), vol.Range(min=10, max=300)),
        })

        return self.async_show_form(
            step_id="device",
            data_schema=device_schema,
            errors=errors,
            description_placeholders={
                "device_types": ", ".join(DEVICE_TYPES.keys()),
                "access_levels": ", ".join(f"{k}: {v}" for k, v in ACCESS_LEVELS.items())
            }
        )

    async def async_step_equipment(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle equipment configuration."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            self.data.update(user_input)
            
            # Create the final config entry using the custom device name
            if self.data.get(CONF_CONNECTION_TYPE) == CONNECTION_TYPE_SERIAL:
                connection_label = self.data.get(CONF_SERIAL_PORT, "serial")
            else:
                connection_label = self.data.get(CONF_HOST, "unknown")
            title = f"{self.data[CONF_DEVICE_NAME]} ({connection_label})"
            
            return self.async_create_entry(
                title=title,
                data=self.data,
            )

        return self.async_show_form(
            step_id="equipment",
            data_schema=STEP_EQUIPMENT_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "device_type": self.data.get(CONF_DEVICE_TYPE, "Unknown")
            }
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for KWB Heating integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow without setting deprecated attribute."""
        # Do NOT assign to self.config_entry (deprecated in HA);
        # keep a private reference for backward-compat usage.
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        return await self.async_step_equipment()

    async def async_step_equipment(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle equipment configuration."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            # Validate device name if provided
            if CONF_DEVICE_NAME in user_input:
                device_name = user_input[CONF_DEVICE_NAME].strip()
                if not device_name:
                    errors[CONF_DEVICE_NAME] = "invalid_device_name"
                elif len(device_name) > 50:
                    errors[CONF_DEVICE_NAME] = "device_name_too_long"
            
            if not errors:
                try:
                    # Update config entry data if device name changed
                    if CONF_DEVICE_NAME in user_input and user_input[CONF_DEVICE_NAME] != self._config_entry.data.get(CONF_DEVICE_NAME):
                        # Update data with new device name
                        updated_data = {**self._config_entry.data, CONF_DEVICE_NAME: user_input[CONF_DEVICE_NAME]}
                        
                        # Update config entry with new data and title
                        if updated_data.get(CONF_CONNECTION_TYPE) == CONNECTION_TYPE_SERIAL:
                            conn_label = updated_data.get(CONF_SERIAL_PORT, "serial")
                        else:
                            conn_label = updated_data.get(CONF_HOST, "unknown")
                        self.hass.config_entries.async_update_entry(
                            self._config_entry,
                            data=updated_data,
                            title=f"{user_input[CONF_DEVICE_NAME]} ({conn_label})"
                        )
                    
                    # Create options entry with equipment settings (excluding device name from options)
                    options_data = {k: v for k, v in user_input.items() if k != CONF_DEVICE_NAME}
                    return self.async_create_entry(title="", data=options_data)
                except Exception as exc:
                    _LOGGER.error("Error updating equipment configuration: %s", exc)
                    errors["base"] = "unknown"

        # Get current values from config entry
        # Prefer framework-provided property if available, else our private copy
        entry = getattr(self, "config_entry", None) or self._config_entry
        current_equipment = entry.options
        
        def _current_default(key: str, fallback: Any) -> Any:
            return current_equipment.get(key, entry.data.get(key, fallback))

        # Create schema with current values as defaults. Equipment count
        # fields are built from EQUIPMENT_RANGES so their max values can't
        # drift from the initial-setup schema.
        equipment_schema = vol.Schema({
            vol.Optional(
                CONF_DEVICE_NAME,
                default=_current_default(CONF_DEVICE_NAME, "KWB Heating")
            ): cv.string,
            vol.Optional(
                CONF_LANGUAGE,
                default=_current_default(CONF_LANGUAGE, "auto")
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["auto", "de", "en"],
                    translation_key="language",
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            **{
                vol.Optional(key, default=_current_default(key, 0)): vol.All(
                    vol.Coerce(int), vol.Range(min=0, max=max_count)
                )
                for key, max_count in EQUIPMENT_RANGES.items()
            },
            vol.Optional(
                CONF_ACCESS_LEVEL,
                default=_current_default(CONF_ACCESS_LEVEL, DEFAULT_ACCESS_LEVEL)
            ): vol.In(ACCESS_LEVELS.keys()),
            vol.Optional(
                CONF_UPDATE_INTERVAL,
                default=_current_default(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
            ): vol.All(vol.Coerce(int), vol.Range(min=10, max=300)),
        })

        return self.async_show_form(
            step_id="equipment",
            data_schema=equipment_schema,
            errors=errors,
            description_placeholders={
                "device_type": entry.data.get(CONF_DEVICE_TYPE, "Unknown")
            }
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(HomeAssistantError):
    """Error to indicate there is an invalid hostname."""
