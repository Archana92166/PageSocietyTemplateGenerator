"""Public service API for paper-standard lookup and custom sizes."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from pathlib import Path

from app.models.paper import CustomPaperSize, PaperSize, PaperStandard
from app.standards.definitions import load_paper_standards
from app.standards.exceptions import (
    DuplicatePaperSizeError,
    PaperSizeNotFoundError,
    PaperStandardNotFoundError,
    StandardDefinitionsError,
)


class PaperStandardsService:
    """Provide validated lookup and custom-registration for paper dimensions."""

    def __init__(self, standards: Iterable[PaperStandard]) -> None:
        """Initialize the service with validated built-in paper standards.

        Raises:
            StandardDefinitionsError: If standards or paper-size names conflict.
        """
        self._logger = logging.getLogger(__name__)
        self._standards = self._index_standards(standards)
        self._custom_sizes: dict[str, CustomPaperSize] = {}
        self._size_index = self._index_sizes(self._standards.values())

    @classmethod
    def from_default_definitions(cls) -> "PaperStandardsService":
        """Create a service from the project's bundled paper definitions."""
        project_root = Path(__file__).resolve().parents[2]
        definitions_path = project_root / "config" / "paper_standards.json"
        return cls(load_paper_standards(definitions_path))

    def get_standard(self, name: str) -> PaperStandard:
        """Return the paper standard identified by name.

        Raises:
            PaperStandardNotFoundError: If no matching standard exists.
        """
        key = self._key_for(name, "Paper standard name")
        try:
            return self._standards[key]
        except KeyError as error:
            raise PaperStandardNotFoundError(
                f"Paper standard '{name}' was not found."
            ) from error

    def get_size(self, name: str) -> PaperSize:
        """Return a paper size by its globally unique name.

        Raises:
            PaperSizeNotFoundError: If no matching size exists.
        """
        key = self._key_for(name, "Paper size name")
        try:
            return self._size_index[key]
        except KeyError as error:
            raise PaperSizeNotFoundError(
                f"Paper size '{name}' was not found."
            ) from error

    def list_standards(self) -> tuple[PaperStandard, ...]:
        """Return all built-in standards in definition-file order."""
        return tuple(self._standards.values())

    def list_sizes(self, standard_name: str) -> tuple[PaperSize, ...]:
        """Return all sizes belonging to the named paper standard."""
        standard = self.get_standard(standard_name)
        if standard.name.casefold() != "custom":
            return standard.sizes
        return tuple(self._custom_sizes.values())

    def register_custom_size(
        self,
        name: str,
        width_mm: float,
        height_mm: float,
    ) -> CustomPaperSize:
        """Register and return a custom size expressed in millimetres.

        Raises:
            ValueError: If the name or dimensions are invalid.
            DuplicatePaperSizeError: If the size name is already in use.
        """
        size = CustomPaperSize(name=name, width_mm=width_mm, height_mm=height_mm)
        key = self._key_for(size.name, "Paper size name")
        if key in self._size_index:
            raise DuplicatePaperSizeError(
                f"Paper size '{size.name}' is already registered."
            )

        self._custom_sizes[key] = size
        self._size_index[key] = size
        self._logger.info("Registered custom paper size '%s'", size.name)
        return size

    @staticmethod
    def _key_for(value: str, field_name: str) -> str:
        """Create a normalized lookup key after validating a lookup value."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string.")
        return value.strip().casefold()

    @staticmethod
    def _index_standards(
        standards: Iterable[PaperStandard],
    ) -> dict[str, PaperStandard]:
        """Index standards and reject duplicate standard names."""
        indexed_standards: dict[str, PaperStandard] = {}
        for standard in standards:
            key = standard.name.casefold()
            if key in indexed_standards:
                raise StandardDefinitionsError(
                    f"Duplicate paper standard '{standard.name}'."
                )
            indexed_standards[key] = standard
        return indexed_standards

    @staticmethod
    def _index_sizes(
        standards: Iterable[PaperStandard],
    ) -> dict[str, PaperSize]:
        """Index sizes and reject duplicate globally-addressable names."""
        indexed_sizes: dict[str, PaperSize] = {}
        for standard in standards:
            for size in standard.sizes:
                key = size.name.casefold()
                if key in indexed_sizes:
                    raise StandardDefinitionsError(
                        f"Duplicate paper size '{size.name}'."
                    )
                indexed_sizes[key] = size
        return indexed_sizes
