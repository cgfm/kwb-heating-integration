"""Version manager for KWB heating systems."""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

_LOGGER = logging.getLogger(__name__)


class VersionManager:
    """Manages version detection and configuration path resolution for KWB heating systems."""

    def __init__(self, config_base_path: Path | None = None):
        """Initialize the version manager.

        Args:
            config_base_path: Base path for configuration files.
                            Defaults to package config directory.
        """
        if config_base_path is None:
            config_base_path = Path(__file__).parent / "config"

        self.config_base_path = Path(config_base_path)
        self.version_mapping_path = self.config_base_path / "version_mapping.json"
        self.version_mapping: dict[str, Any] = {}
        self.fallback_strategy = "closest_match"
        self.default_version = "22.7.1"

        self._load_version_mapping()

    def _load_version_mapping(self) -> None:
        """Load version mapping from configuration file."""
        try:
            if self.version_mapping_path.exists():
                with open(self.version_mapping_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.version_mapping = config.get("supported_versions", {})

                    fallback_rules = config.get("fallback_rules", {})
                    self.fallback_strategy = fallback_rules.get("strategy", "closest_match")
                    self.default_version = fallback_rules.get("default_version", "22.7.1")

                    _LOGGER.info(
                        "Loaded version mapping with %d supported versions",
                        len(self.version_mapping)
                    )
            else:
                _LOGGER.warning(
                    "Version mapping file not found at %s, using defaults",
                    self.version_mapping_path
                )
                self._create_default_mapping()
        except Exception as exc:
            _LOGGER.error("Failed to load version mapping: %s", exc)
            self._create_default_mapping()

    def _create_default_mapping(self) -> None:
        """Create default version mapping."""
        self.version_mapping = {
            "22.7.1": {
                "config_path": "versions/v22.7.1",
                "supported_languages": ["de", "en"],
                "register_layouts": {
                    "software_version": 8192,
                    "device_info_start": 8000
                }
            },
            "25.7.1": {
                "config_path": "versions/v25.7.1",
                "supported_languages": ["de", "en"],
                "register_layouts": {
                    "software_version": 8192,
                    "device_info_start": 8000
                }
            }
        }

    def parse_version(self, version_raw: int | str) -> str:
        """Parse raw version value into normalized version string.

        Args:
            version_raw: Raw version value from register (int) or version string

        Returns:
            Normalized version string (e.g., "22.7.1")
        """
        if isinstance(version_raw, int):
            # Assuming version format: major version is the integer value
            # For KWB systems, register 8192 contains major version (22, 25, etc.)
            # This is a simplified parsing - adjust based on actual format
            major = version_raw
            # Default to x.7.1 pattern observed in ModbusInfo files
            return f"{major}.7.1"

        if isinstance(version_raw, str):
            # Clean up version string (remove 'V' prefix, extra spaces, etc.)
            version_str = version_raw.strip().upper()
            version_str = version_str.replace('V', '').replace('v', '')

            # Try to extract version numbers
            match = re.match(r'(\d+)\.(\d+)\.(\d+)', version_str)
            if match:
                return f"{match.group(1)}.{match.group(2)}.{match.group(3)}"

        _LOGGER.warning("Could not parse version: %s", version_raw)
        return self.default_version

    def get_closest_version(self, target_version: str) -> str:
        """Find closest supported version to target version.

        Args:
            target_version: Target version string

        Returns:
            Closest supported version string
        """
        if target_version in self.version_mapping:
            return target_version

        supported_versions = list(self.version_mapping.keys())
        if not supported_versions:
            return self.default_version

        # Parse version numbers for comparison
        try:
            target_parts = [int(x) for x in target_version.split('.')]

            # Find closest version by comparing major, minor, patch
            closest_version = None
            min_distance = float('inf')

            for version in supported_versions:
                version_parts = [int(x) for x in version.split('.')]

                # Calculate distance (weighted: major > minor > patch)
                distance = (
                    abs(target_parts[0] - version_parts[0]) * 10000 +
                    abs(target_parts[1] - version_parts[1]) * 100 +
                    abs(target_parts[2] - version_parts[2])
                )

                if distance < min_distance:
                    min_distance = distance
                    closest_version = version

            return closest_version or self.default_version

        except (ValueError, IndexError) as exc:
            _LOGGER.warning("Error finding closest version for %s: %s", target_version, exc)
            return self.default_version

    def get_config_path(self, version: str, language: str) -> Path:
        """Get configuration path for version and language combination.

        Args:
            version: Version string (e.g., "22.7.1")
            language: Language code (e.g., "de", "en")

        Returns:
            Path to configuration directory
        """
        # Normalize version if needed
        if version not in self.version_mapping:
            version = self.get_closest_version(version)
            _LOGGER.info("Using closest version %s for requested version", version)

        version_info = self.version_mapping.get(version, {})
        config_path = version_info.get("config_path", f"versions/v{version}")

        # Check if language is supported
        supported_languages = version_info.get("supported_languages", ["de", "en"])
        if language not in supported_languages:
            _LOGGER.warning(
                "Language %s not supported for version %s, falling back to %s",
                language, version, supported_languages[0]
            )
            language = supported_languages[0]

        full_path = self.config_base_path / config_path / language
        return full_path

    def get_supported_versions(self) -> list[str]:
        """Get list of supported software versions.

        Returns:
            List of version strings
        """
        return list(self.version_mapping.keys())

    def get_supported_languages(self, version: str) -> list[str]:
        """Get list of supported languages for a version.

        Args:
            version: Version string

        Returns:
            List of language codes
        """
        if version not in self.version_mapping:
            version = self.get_closest_version(version)

        version_info = self.version_mapping.get(version, {})
        return version_info.get("supported_languages", ["de", "en"])

    def get_version_register_address(self, version: str | None = None) -> int:
        """Get register address for software version.

        Args:
            version: Optional version string. If None, uses default.

        Returns:
            Register address for software version
        """
        if version and version in self.version_mapping:
            return self.version_mapping[version]["register_layouts"]["software_version"]

        # Default register address for software version
        return 8192

    def validate_config_exists(self, version: str, language: str) -> bool:
        """Check if configuration exists for version and language.

        Args:
            version: Version string
            language: Language code

        Returns:
            True if configuration directory exists
        """
        config_path = self.get_config_path(version, language)
        return config_path.exists() and config_path.is_dir()

    async def detect_version(self, modbus_client) -> str:
        """Detect software version from device.

        Args:
            modbus_client: Instance of KWBModbusClient

        Returns:
            Detected version string
        """
        try:
            register_address = self.get_version_register_address()
            _LOGGER.debug("Reading version from register %d", register_address)

            # Read version register
            result = await modbus_client.read_input_registers(register_address, 1)

            if result and len(result) > 0:
                version_raw = result[0]
                version = self.parse_version(version_raw)
                _LOGGER.info("Detected software version: %s (raw: %d)", version, version_raw)
                return version
            else:
                _LOGGER.warning("Could not read version register, using default")
                return self.default_version

        except Exception as exc:
            _LOGGER.error("Error detecting version: %s", exc)
            return self.default_version

    def get_version_info(self, version: str) -> dict[str, Any]:
        """Get detailed information about a version.

        Args:
            version: Version string

        Returns:
            Dictionary with version information
        """
        if version not in self.version_mapping:
            version = self.get_closest_version(version)

        return self.version_mapping.get(version, {})
