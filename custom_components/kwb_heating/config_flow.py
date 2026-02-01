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
    CONF_HEATING_CIRCUITS,
    CONF_BUFFER_STORAGE,
    CONF_DHW_STORAGE,
    CONF_SECONDARY_HEAT_SOURCES,
    CONF_CIRCULATION,
    CONF_SOLAR,
    CONF_BOILER_SEQUENCE,
    CONF_HEAT_METERS,
    CONF_TRANSFER_STATIONS,
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
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    vol.Optional(CONF_SLAVE_ID, default=DEFAULT_SLAVE_ID): vol.All(vol.Coerce(int), vol.Range(min=1, max=255)),
})

STEP_DEVICE_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_DEVICE_TYPE): vol.In(DEVICE_TYPES.keys()),
    vol.Required(CONF_DEVICE_NAME): cv.string,
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

STEP_EQUIPMENT_DATA_SCHEMA = vol.Schema({
    # Slider für Anzahl der Heizkreise (0 = deaktiviert, 1-14 = Anzahl)
    # 421 Register verfügbar, realistisch max. 14 Heizkreise
    vol.Optional(CONF_HEATING_CIRCUITS, default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=14)),

    # Slider für Anzahl der Pufferspeicher (0 = deaktiviert, 1-15 = Anzahl)
    # 270 Register verfügbar, realistisch max. 15 Pufferspeicher
    vol.Optional(CONF_BUFFER_STORAGE, default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=15)),

    # Slider für Anzahl der Brauchwasserspeicher (0 = deaktiviert, 1-14 = Anzahl)
    # 168 Register verfügbar, realistisch max. 14 Brauchwasserspeicher
    vol.Optional(CONF_DHW_STORAGE, default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=14)),
    
    # Slider für Anzahl der Zweitwärmequellen (0 = deaktiviert, 1-14 = Anzahl)
    # 56 Register verfügbar, realistisch max. 14 Zweitwärmequellen
    vol.Optional(CONF_SECONDARY_HEAT_SOURCES, default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=14)),

    # Slider für Anzahl der Zirkulationen (0 = deaktiviert, 1-15 = Anzahl)
    # 60 Register verfügbar, realistisch max. 15 Zirkulationen
    vol.Optional(CONF_CIRCULATION, default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=15)),

    # Slider für Anzahl der Solar-Anlagen (0 = deaktiviert, 1-14 = Anzahl)
    # 392 Register verfügbar, realistisch max. 14 Solar-Anlagen
    vol.Optional(CONF_SOLAR, default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=14)),

    # Slider für Anzahl der Kesselfolgeschaltungen (0 = deaktiviert, 1-8 = Anzahl)
    # 45 Register verfügbar, realistisch max. 8 Kesselfolgeschaltungen
    vol.Optional(CONF_BOILER_SEQUENCE, default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=8)),

    # Slider für Anzahl der Wärmemengenzähler (0 = deaktiviert, 1-36 = Anzahl)
    # 216 Register verfügbar, realistisch max. 36 Wärmemengenzähler
    vol.Optional(CONF_HEAT_METERS, default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=36)),

    # Slider für Anzahl der Übergabestationen (0 = deaktiviert, 1-14 = Anzahl)
    # Transfer stations configuration
    vol.Optional(CONF_TRANSFER_STATIONS, default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=14)),
})


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    
    client = KWBModbusClient(
        host=data[CONF_HOST],
        port=data[CONF_PORT],
        slave_id=data[CONF_SLAVE_ID]
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
    return {
        "title": f"KWB Heating ({data[CONF_HOST]})",
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
        """Handle the initial step - connection settings."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                self.data.update(user_input)
                
                # Create unique_id from host and slave_id
                unique_id = f"{user_input[CONF_HOST]}_{user_input[CONF_SLAVE_ID]}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                
                # Move to device selection step
                return await self.async_step_device()
                
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidHost:
                errors["host"] = "invalid_host"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "access_levels": ", ".join(f"{k}: {v}" for k, v in ACCESS_LEVELS.items())
            }
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
            title = f"{self.data[CONF_DEVICE_NAME]} ({self.data[CONF_HOST]})"
            
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
                        self.hass.config_entries.async_update_entry(
                            self._config_entry,
                            data=updated_data,
                            title=f"{user_input[CONF_DEVICE_NAME]} ({updated_data[CONF_HOST]})"
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
        
        # Create schema with current values as defaults
        equipment_schema = vol.Schema({
            vol.Optional(
                CONF_DEVICE_NAME,
                default=current_equipment.get(CONF_DEVICE_NAME,
                                             entry.data.get(CONF_DEVICE_NAME, "KWB Heating"))
            ): cv.string,
            vol.Optional(
                CONF_LANGUAGE,
                default=current_equipment.get(CONF_LANGUAGE,
                                             entry.data.get(CONF_LANGUAGE, "auto"))
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["auto", "de", "en"],
                    translation_key="language",
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(
                CONF_HEATING_CIRCUITS,
                default=current_equipment.get(CONF_HEATING_CIRCUITS,
                                             entry.data.get(CONF_HEATING_CIRCUITS, 0))
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=14)),
            vol.Optional(
                CONF_BUFFER_STORAGE, 
                default=current_equipment.get(CONF_BUFFER_STORAGE,
                                             entry.data.get(CONF_BUFFER_STORAGE, 0))
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=15)),
            vol.Optional(
                CONF_DHW_STORAGE, 
                default=current_equipment.get(CONF_DHW_STORAGE,
                                             entry.data.get(CONF_DHW_STORAGE, 0))
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=14)),
            vol.Optional(
                CONF_SECONDARY_HEAT_SOURCES, 
                default=current_equipment.get(CONF_SECONDARY_HEAT_SOURCES,
                                             entry.data.get(CONF_SECONDARY_HEAT_SOURCES, 0))
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=14)),
            vol.Optional(
                CONF_CIRCULATION, 
                default=current_equipment.get(CONF_CIRCULATION,
                                             entry.data.get(CONF_CIRCULATION, 0))
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=15)),
            vol.Optional(
                CONF_SOLAR, 
                default=current_equipment.get(CONF_SOLAR,
                                             entry.data.get(CONF_SOLAR, 0))
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=14)),
            vol.Optional(
                CONF_BOILER_SEQUENCE, 
                default=current_equipment.get(CONF_BOILER_SEQUENCE,
                                             entry.data.get(CONF_BOILER_SEQUENCE, 0))
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=8)),
            vol.Optional(
                CONF_HEAT_METERS,
                default=current_equipment.get(CONF_HEAT_METERS,
                                             entry.data.get(CONF_HEAT_METERS, 0))
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=36)),
            vol.Optional(
                CONF_TRANSFER_STATIONS,
                default=current_equipment.get(CONF_TRANSFER_STATIONS,
                                             entry.data.get(CONF_TRANSFER_STATIONS, 0))
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=14)),
            vol.Optional(
                CONF_ACCESS_LEVEL,
                default=current_equipment.get(CONF_ACCESS_LEVEL,
                                             entry.data.get(CONF_ACCESS_LEVEL, DEFAULT_ACCESS_LEVEL))
            ): vol.In(ACCESS_LEVELS.keys()),
            vol.Optional(
                CONF_UPDATE_INTERVAL,
                default=current_equipment.get(CONF_UPDATE_INTERVAL,
                                             entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL))
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
