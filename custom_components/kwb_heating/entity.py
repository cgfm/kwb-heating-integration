"""Base entity for KWB Heating integration."""
from __future__ import annotations
import logging

from typing import TYPE_CHECKING, Any

from homeassistant.helpers.update_coordinator import CoordinatorEntity

if TYPE_CHECKING:
    from .coordinator import KWBDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

class KWBBaseEntity(CoordinatorEntity):
    """Base class for KWB heating system entities.

    Provides common functionality for all entity types including:
    - Entity name and unique ID generation
    - Device info assignment
    - Entity ID sanitization
    - Availability check
    """

    # Let HA handle device name prefixing automatically (issue #16)
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: "KWBDataUpdateCoordinator",
        register: dict[str, Any],
        platform: str,
    ) -> None:
        """Initialize the base entity.

        Args:
            coordinator: The data update coordinator
            register: Register configuration dictionary
            platform: Platform name (sensor, switch, select, number)
        """
        super().__init__(coordinator)
        self._register = register
        self._address = register["starting_address"]

        # Entity name is ONLY the entity-specific part (no device prefix).
        # With _attr_has_entity_name = True, HA prepends the device name automatically.
        self._attr_name = register["name"]

        # Use coordinator's centralized unique ID generation
        self._attr_unique_id = coordinator.generate_entity_unique_id(register)

        # Generate a stable entity ID that does not depend on the language.
        device_prefix = coordinator.sanitize_for_entity_id(coordinator.device_name_prefix)

        # The 'entity_id' field from the JSON config is the primary, language-independent identifier.
        register_entity_id = register.get("entity_id")

        if not register_entity_id:
            # Fallback for registers without a pre-defined 'entity_id' (e.g., universal registers).
            # The 'parameter' field is a stable, unique key from the manufacturer's specification.
            parameter = register.get("parameter")
            if parameter:
                # Sanitize the parameter to be a valid component for an entity_id.
                register_entity_id = coordinator.sanitize_for_entity_id(parameter)
            else:
                # As an absolute fallback, use the register address, which is guaranteed to be unique and stable.
                # This avoids using the translated 'name' field.
                _LOGGER.warning(
                    "Could not generate entity_id from 'entity_id' or 'parameter' for register at address %s. "
                    "Falling back to address-based ID. Please consider defining an 'entity_id' in the JSON config.",
                    self._address
                )
                register_entity_id = f"register_{self._address}"

        self.entity_id = f"{platform}.{device_prefix}_{register_entity_id}"

        # Set device info
        self._attr_device_info = coordinator.device_info

    @property
    def available(self) -> bool:
        """Return True if entity is available (issue #18 — centralized)."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self._address in self.coordinator.data
        )

    def _build_description(self) -> str | None:
        """Compose a human-readable description from register metadata.

        Combines the manufacturer parameter path and any associated value-table
        entries so the resulting attribute makes hard-to-read register names
        more understandable in the More-Info dialog.
        """
        parts: list[str] = []

        parameter = self._register.get("parameter")
        if parameter:
            parts.append(f"Parameter: {parameter}")

        table_name = self._register.get("unit_value_table", "")
        value_tables = getattr(self.coordinator.data_converter, "value_tables", {})
        if table_name and table_name in value_tables:
            table = value_tables[table_name]

            def _sort_key(item: tuple[str, str]) -> tuple[int, int | str]:
                key = item[0]
                try:
                    return (0, int(key))
                except (TypeError, ValueError):
                    return (1, str(key))

            entries = ", ".join(f"{k}={v}" for k, v in sorted(table.items(), key=_sort_key))
            parts.append(f"Values ({table_name}): {entries}")

        return " | ".join(parts) if parts else None

    def _build_static_attrs(self) -> dict[str, Any]:
        """Build the dict of static attributes shared across all platforms.

        Platforms merge dynamic data (raw_value, display_value, …) on top of
        this in their own extra_state_attributes implementation.
        """
        register = self._register
        attrs: dict[str, Any] = {
            "register_address": self._address,
            "register_type": register.get("type"),
            "data_type": register.get("data_type"),
        }

        description = self._build_description()
        if description:
            attrs["description"] = description

        if register.get("parameter"):
            attrs["parameter"] = register["parameter"]
        if register.get("access_level"):
            attrs["access_level"] = register["access_level"]
        if register.get("min") is not None:
            attrs["min_value"] = register["min"]
        if register.get("max") is not None:
            attrs["max_value"] = register["max"]

        return attrs
