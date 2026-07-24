"""Logging configuration for the application."""

from __future__ import annotations

import logging
from typing import Any


def configure_logging(logging_configuration: dict[str, Any]) -> None:
    """Configure the root logger once using application configuration values."""
    level_name = str(logging_configuration.get("level", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format=str(
            logging_configuration.get(
                "format", "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
            )
        ),
    )
