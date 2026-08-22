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

from .const import CONF_LANGUAGE, DOMAIN, PLATFORMS, EQUIPMENT_KEYS
from .coordinator import KWBDataUpdateCoordinator
from .fuel_split import (
    FuelSplitTracker,
    STORAGE_VERSION as FUEL_SPLIT_STORAGE_VERSION,
    fuel_split_storage_key,
    get_fuel_split_register_addresses,
)
from .fuel_split_entity_ids import async_migrate_fuel_split_entity_ids

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

    await coordinator.async_config_entry_first_refresh()

    await _async_setup_fuel_split_tracker(hass, entry, coordinator)

    if coordinator.fuel_split_tracker is not None:
        # Run before platforms are forwarded so an existing registry entry is
        # renamed before EntityPlatform resolves the unchanged unique ID.
        async_migrate_fuel_split_entity_ids(hass, entry, coordinator)
    
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Set up all platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Add listener for options updates
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    
    return True


async def _async_setup_fuel_split_tracker(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: KWBDataUpdateCoordinator,
) -> None:
    """Create the single persistent fuel-split tracker when capable."""
    if coordinator.fuel_split_tracker is not None:
        _LOGGER.debug("Fuel-split tracker already exists for this config entry")
        return
    addresses = get_fuel_split_register_addresses(coordinator.registers)
    if addresses is None:
        _LOGGER.debug(
            "Combined heat total or operating mode is absent; fuel split disabled"
        )
        return

    # Imported lazily so module-level config/update tests do not require the
    # complete Home Assistant storage runtime.
    from homeassistant.helpers.storage import Store

    total_address, mode_address = addresses
    expected_interval = coordinator.update_interval.total_seconds()
    tracker = FuelSplitTracker(
        coordinator,
        Store(
            hass,
            FUEL_SPLIT_STORAGE_VERSION,
            fuel_split_storage_key(entry.entry_id),
        ),
        total_address,
        mode_address,
        expected_interval,
    )
    coordinator.fuel_split_tracker = tracker
    await tracker.async_initialize()
    _LOGGER.info(
        "Fuel-split tracking enabled using total address %s and mode address %s",
        total_address,
        mode_address,
    )


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    _LOGGER.info("Updating KWB Heating options")
    
    coordinator: KWBDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Check for changes that require a full integration reload
    old_config = coordinator.config.copy()
    new_config = {**entry.data, **entry.options}
    
    # Check if any equipment counts have changed
    equipment_changed = any(
        old_config.get(key) != new_config.get(key)
        for key in EQUIPMENT_KEYS
    )
    
    # Check if the access level has changed
    access_level_changed = old_config.get("access_level") != new_config.get("access_level")

    # Localized names, indexes, value tables, and alarms are constructed during
    # setup. Rebuild them together instead of mutating live entities piecemeal.
    language_changed = old_config.get(CONF_LANGUAGE, "auto") != new_config.get(
        CONF_LANGUAGE, "auto"
    )
    
    # A full reload is needed for structural changes and presentation language.
    if equipment_changed or access_level_changed or language_changed:
        if equipment_changed:
            _LOGGER.info("Equipment configuration changed, reloading integration.")
        if access_level_changed:
            _LOGGER.info("Access level changed, reloading integration.")
        if language_changed:
            _LOGGER.info("Language changed, reloading integration.")
            
        await hass.config_entries.async_reload(entry.entry_id)
    else:
        # For other minor changes, just update the coordinator and refresh
        _LOGGER.info("Performing a soft update for non-structural changes.")
        await coordinator.async_update_config(entry.data, entry.options)
        await coordinator.async_request_refresh()


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading KWB Heating integration")
    
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        tracker = coordinator.fuel_split_tracker
        if tracker is not None:
            await tracker.async_shutdown()
            coordinator.fuel_split_tracker = None
        await coordinator.modbus_client.disconnect()
    
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        # No migration needed from version 1
        pass

    _LOGGER.info("Migration to version %s successful", config_entry.version)

    return True
