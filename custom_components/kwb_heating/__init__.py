"""
KWB Heating Integration for Home Assistant.

This custom component provides integration with KWB heating systems
via Modbus TCP/RTU communication.
"""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import DOMAIN, PLATFORMS
from .coordinator import KWBDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the KWB Heating component."""
    _LOGGER.debug("Setting up KWB Heating component")
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up KWB Heating from a config entry."""
    _LOGGER.info("Setting up KWB Heating integration")
    
    coordinator = KWBDataUpdateCoordinator(hass, entry)
    
    # Try initial refresh, but don't fail setup if connection fails
    try:
        await coordinator.async_config_entry_first_refresh()
        _LOGGER.info("Initial data refresh successful")
    except (UpdateFailed, ConfigEntryNotReady, ConnectionError, TimeoutError, OSError) as exc:
        _LOGGER.warning("Initial data refresh failed, will retry: %s", exc)
        # Continue with setup anyway - coordinator will retry periodically
    
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Set up all platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Add listener for options updates
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    
    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    _LOGGER.info("Updating KWB Heating options")
    
    # Get coordinator
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Check if equipment configuration changed (requires entity reload)
    old_config = coordinator.config.copy()
    new_config = {**entry.data, **entry.options}
    
    equipment_keys = [
        "heating_circuits", "buffer_storage", "dhw_storage", 
        "secondary_heat_sources", "circulation", "solar",
        "boiler_sequence", "heat_meters"
    ]
    
    equipment_changed = any(
        old_config.get(key, 0) != new_config.get(key, 0)
        for key in equipment_keys
    )
    
    if equipment_changed:
        _LOGGER.info("Equipment configuration changed, reloading integration")
        # Reload the entire integration to recreate entities
        await hass.config_entries.async_reload(entry.entry_id)
    else:
        # Only update coordinator configuration for non-equipment changes
        await coordinator.async_update_config(entry.data, entry.options)
        await coordinator.async_request_refresh()


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading KWB Heating integration")
    
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
