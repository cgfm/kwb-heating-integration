"""Language manager for KWB heating systems."""
from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

import aiofiles

from .version_manager import VersionManager

_LOGGER = logging.getLogger(__name__)


class LanguageManager:
    """Manages language detection and resolution for KWB heating systems."""

    def __init__(self, config_base_path: Path | None = None):
        """Initialize the language manager.

        Args:
            config_base_path: Base path for configuration files.
        """
        if config_base_path is None:
            config_base_path = Path(__file__).parent / "config"

        self.config_base_path = Path(config_base_path)
        self.language_config_path = self.config_base_path / "language_config.json"
        self.language_config: dict[str, Any] = {}
        self.default_language = "en"
        self.use_ha_locale = True
        self.language_mapping: dict[str, str] = {}
        self._initialized = False

        # Create default config immediately (no I/O)
        self._create_default_config()

    async def async_initialize(self) -> None:
        """Async initialization - load config file without blocking."""
        if self._initialized:
            return

        await self._async_load_language_config()
        self._initialized = True

    async def _async_load_language_config(self) -> None:
        """Load language configuration from file asynchronously."""
        try:
            if self.language_config_path.exists():
                async with aiofiles.open(self.language_config_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    self.language_config = json.loads(content)

                language_detection = self.language_config.get("language_detection", {})
                self.use_ha_locale = language_detection.get("use_ha_locale", True)
                self.default_language = language_detection.get("fallback_language", "en")
                self.language_mapping = self.language_config.get("language_mapping", {})

                _LOGGER.info("Loaded language configuration")
            else:
                _LOGGER.debug(
                    "Language config file not found at %s, using defaults",
                    self.language_config_path
                )
        except Exception as exc:
            _LOGGER.error("Failed to load language configuration: %s", exc)

    def _create_default_config(self) -> None:
        """Create default language configuration."""
        self.use_ha_locale = True
        self.default_language = "en"
        self.language_mapping = {
            "de": "de",
            "de-DE": "de",
            "de-AT": "de",
            "de-CH": "de",
            "en": "en",
            "en-US": "en",
            "en-GB": "en",
        }

    def normalize_language(self, language: str) -> str:
        """Normalize language code to supported format.

        Args:
            language: Language code (e.g., "de-DE", "en", etc.)

        Returns:
            Normalized language code ("de" or "en")
        """
        if not language:
            return self.default_language

        language = language.lower().strip()

        # Check direct mapping
        if language in self.language_mapping:
            return self.language_mapping[language]

        # Try to extract base language (e.g., "de" from "de-DE")
        base_language = language.split('-')[0]
        if base_language in self.language_mapping:
            return self.language_mapping[base_language]

        _LOGGER.warning("Language %s not supported, using default %s", language, self.default_language)
        return self.default_language

    def resolve_language(
        self,
        user_preference: str | None = None,
        ha_locale: str | None = None,
        supported_languages: list[str] | None = None
    ) -> str:
        """Resolve language based on preferences and availability.

        Args:
            user_preference: User's explicit language preference
            ha_locale: Home Assistant locale setting
            supported_languages: List of supported languages for the version

        Returns:
            Resolved language code
        """
        if supported_languages is None:
            supported_languages = ["de", "en"]

        # 1. Check user preference
        if user_preference and user_preference != "auto":
            normalized = self.normalize_language(user_preference)
            if normalized in supported_languages:
                _LOGGER.debug("Using user preference language: %s", normalized)
                return normalized

        # 2. Check Home Assistant locale if enabled
        if self.use_ha_locale and ha_locale:
            normalized = self.normalize_language(ha_locale)
            if normalized in supported_languages:
                _LOGGER.debug("Using Home Assistant locale language: %s", normalized)
                return normalized

        # 3. Fall back to default language
        if self.default_language in supported_languages:
            _LOGGER.debug("Using default language: %s", self.default_language)
            return self.default_language

        # 4. Use first supported language as last resort
        if supported_languages:
            _LOGGER.debug("Using first supported language: %s", supported_languages[0])
            return supported_languages[0]

        return "en"


class LanguageAwareConfigLoader:
    """Loads configuration files based on version and language."""

    def __init__(
        self,
        version_manager: VersionManager,
        language_manager: LanguageManager
    ):
        """Initialize the config loader.

        Args:
            version_manager: Instance of VersionManager
            language_manager: Instance of LanguageManager
        """
        self.version_manager = version_manager
        self.language_manager = language_manager

    def _read_file_sync(self, file_path: Path) -> str:
        """Read file synchronously for executor."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    async def load_config(
        self,
        config_type: str,
        version: str,
        language: str
    ) -> dict[str, Any]:
        """Load version and language specific configuration.

        Args:
            config_type: Type of config to load (e.g., "universal_registers", "value_tables")
            version: Software version
            language: Language code

        Returns:
            Configuration dictionary
        """
        try:
            # Get config path for version and language
            config_path = self.version_manager.get_config_path(version, language)

            # Map config type to filename
            config_files = {
                "universal_registers": "modbus_registers.json",
                "value_tables": "value_tables.json",
                "alarm_codes": "alarm_codes.json",
                "devices": "devices",
                "equipment": "equipment",
            }

            if config_type not in config_files:
                _LOGGER.error("Unknown config type: %s", config_type)
                return {}

            config_file = config_files[config_type]

            # Handle directory-based configs (devices, equipment)
            if config_type in ["devices", "equipment"]:
                return await self._load_directory_config(config_path / config_file)

            # Handle single file configs
            file_path = config_path / config_file
            if not file_path.exists():
                _LOGGER.warning("Config file not found: %s", file_path)
                return {}

            # Read file asynchronously
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(None, self._read_file_sync, file_path)
            config_data = json.loads(content)

            _LOGGER.debug("Loaded %s config from %s", config_type, file_path)
            return config_data

        except Exception as exc:
            _LOGGER.error("Error loading config %s: %s", config_type, exc)
            return {}

    async def _load_directory_config(self, directory_path: Path) -> dict[str, Any]:
        """Load all JSON files from a directory.

        Args:
            directory_path: Path to directory containing JSON files

        Returns:
            Dictionary with filename (without .json) as keys
        """
        try:
            if not directory_path.exists() or not directory_path.is_dir():
                _LOGGER.warning("Config directory not found: %s", directory_path)
                return {}

            config_data = {}
            json_files = list(directory_path.glob("*.json"))

            for file_path in json_files:
                try:
                    loop = asyncio.get_event_loop()
                    content = await loop.run_in_executor(None, self._read_file_sync, file_path)
                    data = json.loads(content)

                    # Use filename without extension as key
                    key = file_path.stem
                    config_data[key] = data

                    _LOGGER.debug("Loaded config file: %s", file_path)
                except Exception as exc:
                    _LOGGER.error("Error loading file %s: %s", file_path, exc)
                    continue

            return config_data

        except Exception as exc:
            _LOGGER.error("Error loading directory config from %s: %s", directory_path, exc)
            return {}

    def get_available_languages(self, version: str) -> list[str]:
        """Get supported languages for a specific version.

        Args:
            version: Software version

        Returns:
            List of language codes
        """
        return self.version_manager.get_supported_languages(version)

    async def validate_config_availability(
        self,
        version: str,
        language: str
    ) -> bool:
        """Check if configuration is available for version and language.

        Args:
            version: Software version
            language: Language code

        Returns:
            True if configuration exists
        """
        return self.version_manager.validate_config_exists(version, language)

    async def load_all_configs(
        self,
        version: str,
        language: str
    ) -> dict[str, Any]:
        """Load all configuration files for version and language.

        Args:
            version: Software version
            language: Language code

        Returns:
            Dictionary with all configuration data
        """
        all_configs = {}

        # Load all config types
        config_types = [
            "universal_registers",
            "value_tables",
            "alarm_codes",
            "devices",
            "equipment",
        ]

        for config_type in config_types:
            all_configs[config_type] = await self.load_config(config_type, version, language)

        return all_configs
