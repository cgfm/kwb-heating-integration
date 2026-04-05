"""Language manager for KWB heating systems."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import aiofiles

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

        # 3. Fall back to default language if it's supported
        if self.default_language in supported_languages:
            _LOGGER.debug("Using default language: %s", self.default_language)
            return self.default_language
            
        # 4. Fall back to English if it's supported
        if "en" in supported_languages:
            _LOGGER.debug("Falling back to English as default is not available.")
            return "en"

        # 5. Use first supported language as an absolute last resort
        if supported_languages:
            _LOGGER.debug("Using first supported language as fallback: %s", supported_languages[0])
            return supported_languages[0]

        return "en"


