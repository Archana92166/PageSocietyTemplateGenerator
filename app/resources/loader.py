"""Resource-path discovery for packaged application assets."""

from __future__ import annotations

import logging
from pathlib import Path


class ResourceLoader:
    """Resolve resources relative to the application's resource directory."""

    def __init__(self, resource_directory: Path) -> None:
        """Initialize the loader with an existing resource directory."""
        self._resource_directory = resource_directory.resolve()
        self._logger = logging.getLogger(__name__)

    def path_for(self, relative_path: str | Path) -> Path:
        """Return a verified resource path contained by the resource directory.

        Raises:
            FileNotFoundError: If the resource does not exist.
            ValueError: If the requested path leaves the resource directory.
        """
        resource_path = (self._resource_directory / relative_path).resolve()
        if self._resource_directory not in resource_path.parents:
            raise ValueError("Resource path must remain inside the resource directory.")
        if not resource_path.is_file():
            self._logger.warning("Resource was not found: %s", resource_path)
            raise FileNotFoundError(resource_path)
        return resource_path
