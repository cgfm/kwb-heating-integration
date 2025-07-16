"""Config flow for KWB Heating integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
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
    CONF_HEATING_CIRCUITS,
    CONF_BUFFER_STORAGE,
    CONF_DHW_STORAGE,
    CONF_SECONDARY_HEAT_SOURCES,
    CONF_CIRCULATION,
    CONF_SOLAR,
    CONF_BOILER_SEQUENCE,
    CONF_HEAT_METERS,
    SYSTEM_REGISTER_MAPPING,
)
from .modbus_client import KWBModbusClient
from .register_manager import RegisterManager

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
}

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    vol.Optional(CONF_SLAVE_ID, default=DEFAULT_SLAVE_ID): vol.All(vol.Coerce(int), vol.Range(min=1, max=255)),
})

STEP_DEVICE_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_DEVICE_TYPE): vol.In(DEVICE_TYPES.keys()),
    vol.Optional(CONF_ACCESS_LEVEL, default=DEFAULT_ACCESS_LEVEL): vol.In(ACCESS_LEVELS.keys()),
    vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.All(vol.Coerce(int), vol.Range(min=10, max=300)),
})

STEP_EQUIPMENT_DATA_SCHEMA = vol.Schema({
    # Slider für Anzahl der Heizkreise (0 = deaktiviert, 1-16 = Anzahl)
    # 421 Register verfügbar, realistisch max. 16 Heizkreise
    vol.Optional(CONF_HEATING_CIRCUITS, default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=16)),
    
    # Slider für Anzahl der Pufferspeicher (0 = deaktiviert, 1-8 = Anzahl)  
    # 270 Register verfügbar, realistisch max. 8 Pufferspeicher
    vol.Optional(CONF_BUFFER_STORAGE, default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=8)),
    
    # Slider für Anzahl der Brauchwasserspeicher (0 = deaktiviert, 1-8 = Anzahl)
    # 168 Register verfügbar, realistisch max. 8 Brauchwasserspeicher
    vol.Optional(CONF_DHW_STORAGE, default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=8)),
    
    # Slider für Anzahl der Zweitwärmequellen (0 = deaktiviert, 1-4 = Anzahl)
    # 56 Register verfügbar, realistisch max. 4 Zweitwärmequellen
    vol.Optional(CONF_SECONDARY_HEAT_SOURCES, default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=4)),
    
    # Slider für Anzahl der Zirkulationen (0 = deaktiviert, 1-4 = Anzahl)
    # 60 Register verfügbar, realistisch max. 4 Zirkulationen
    vol.Optional(CONF_CIRCULATION, default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=4)),
    
    # Slider für Anzahl der Solar-Anlagen (0 = deaktiviert, 1-8 = Anzahl)
    # 392 Register verfügbar, realistisch max. 8 Solar-Anlagen
    vol.Optional(CONF_SOLAR, default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=8)),
    
    # Slider für Anzahl der Kesselfolgeschaltungen (0 = deaktiviert, 1-4 = Anzahl)
    # 45 Register verfügbar, realistisch max. 4 Kesselfolgeschaltungen
    vol.Optional(CONF_BOILER_SEQUENCE, default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=4)),
    
    # Slider für Anzahl der Wärmemengenzähler (0 = deaktiviert, 1-8 = Anzahl)
    # 216 Register verfügbar, realistisch max. 8 Wärmemengenzähler
    vol.Optional(CONF_HEAT_METERS, default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=8)),
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
            self.data.update(user_input)
            
            # Move to equipment configuration step
            return await self.async_step_equipment()

        return self.async_show_form(
            step_id="device",
            data_schema=STEP_DEVICE_DATA_SCHEMA,
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
            
            # Create the final config entry
            title = f"KWB {self.data[CONF_DEVICE_TYPE]} ({self.data[CONF_HOST]})"
            
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
        """Initialize options flow."""
        self.config_entry = config_entry

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
            # Validate input if needed
            try:
                # Update the config entry with new equipment settings
                new_data = {**self.config_entry.data, **user_input}
                
                # Create options with equipment settings
                return self.async_create_entry(title="", data=user_input)
            except Exception as exc:
                _LOGGER.error("Error updating equipment configuration: %s", exc)
                errors["base"] = "unknown"

        # Get current values from config entry
        current_equipment = self.config_entry.options
        
        # Create schema with current values as defaults
        equipment_schema = vol.Schema({
            vol.Optional(
                CONF_HEATING_CIRCUITS, 
                default=current_equipment.get(CONF_HEATING_CIRCUITS, 
                                             self.config_entry.data.get(CONF_HEATING_CIRCUITS, 0))
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=16)),
            vol.Optional(
                CONF_BUFFER_STORAGE, 
                default=current_equipment.get(CONF_BUFFER_STORAGE,
                                             self.config_entry.data.get(CONF_BUFFER_STORAGE, 0))
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=8)),
            vol.Optional(
                CONF_DHW_STORAGE, 
                default=current_equipment.get(CONF_DHW_STORAGE,
                                             self.config_entry.data.get(CONF_DHW_STORAGE, 0))
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=8)),
            vol.Optional(
                CONF_SECONDARY_HEAT_SOURCES, 
                default=current_equipment.get(CONF_SECONDARY_HEAT_SOURCES,
                                             self.config_entry.data.get(CONF_SECONDARY_HEAT_SOURCES, 0))
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=4)),
            vol.Optional(
                CONF_CIRCULATION, 
                default=current_equipment.get(CONF_CIRCULATION,
                                             self.config_entry.data.get(CONF_CIRCULATION, 0))
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=4)),
            vol.Optional(
                CONF_SOLAR, 
                default=current_equipment.get(CONF_SOLAR,
                                             self.config_entry.data.get(CONF_SOLAR, 0))
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=8)),
            vol.Optional(
                CONF_BOILER_SEQUENCE, 
                default=current_equipment.get(CONF_BOILER_SEQUENCE,
                                             self.config_entry.data.get(CONF_BOILER_SEQUENCE, 0))
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=4)),
            vol.Optional(
                CONF_HEAT_METERS, 
                default=current_equipment.get(CONF_HEAT_METERS,
                                             self.config_entry.data.get(CONF_HEAT_METERS, 0))
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=8)),
            vol.Optional(
                CONF_ACCESS_LEVEL,
                default=current_equipment.get(CONF_ACCESS_LEVEL,
                                             self.config_entry.data.get(CONF_ACCESS_LEVEL, DEFAULT_ACCESS_LEVEL))
            ): vol.In(ACCESS_LEVELS.keys()),
            vol.Optional(
                CONF_UPDATE_INTERVAL,
                default=current_equipment.get(CONF_UPDATE_INTERVAL,
                                             self.config_entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL))
            ): vol.All(vol.Coerce(int), vol.Range(min=10, max=300)),
        })

        return self.async_show_form(
            step_id="equipment",
            data_schema=equipment_schema,
            errors=errors,
            description_placeholders={
                "device_type": self.config_entry.data.get(CONF_DEVICE_TYPE, "Unknown")
            }
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(HomeAssistantError):
    """Error to indicate there is an invalid hostname."""
