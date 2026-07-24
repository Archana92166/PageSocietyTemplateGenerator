"""JSON-backed application configuration loading."""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from app.core.errors import ConfigurationError


class ConfigurationLoader:
    """Load and validate the application's JSON configuration file."""

    def __init__(self, configuration_path: Path) -> None:
        """Initialize the loader with the path to a JSON configuration file."""
        self._configuration_path = configuration_path
        self._logger = logging.getLogger(__name__)

    def load(self) -> dict[str, Any]:
        """Return the validated configuration data.

        Raises:
            ConfigurationError: If the configuration is unavailable or invalid.
        """
        try:
            with self._configuration_path.open(encoding="utf-8") as file_handle:
                configuration = json.load(file_handle)
        except FileNotFoundError as error:
            message = f"Configuration file was not found: {self._configuration_path}"
            self._logger.error(message)
            raise ConfigurationError(message) from error
        except json.JSONDecodeError as error:
            message = f"Configuration file contains invalid JSON: {error}"
            self._logger.error(message)
            raise ConfigurationError(message) from error
        except OSError as error:
            message = f"Configuration file could not be read: {error}"
            self._logger.error(message)
            raise ConfigurationError(message) from error

        self._validate(configuration)
        self._logger.info("Loaded application configuration from %s", self._configuration_path)
        return configuration

    def _validate(self, configuration: object) -> None:
        """Validate the small configuration contract needed by the application shell."""
        if not isinstance(configuration, Mapping):
            raise ConfigurationError("Configuration root must be a JSON object.")

        application = configuration.get("application")
        window = configuration.get("window")
        if not isinstance(application, Mapping) or not isinstance(window, Mapping):
            raise ConfigurationError(
                "Configuration must contain 'application' and 'window' objects."
            )

        required_application_keys = ("name", "organization_name")
        required_window_keys = ("title", "width", "height")
        if any(not isinstance(application.get(key), str) for key in required_application_keys):
            raise ConfigurationError("Application configuration values must be strings.")
        if any(not isinstance(window.get(key), (int, float)) for key in ("width", "height")):
            raise ConfigurationError("Window dimensions must be numeric.")
        if not isinstance(window.get("title"), str):
            raise ConfigurationError("Window title must be a string.")
