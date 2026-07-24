"""Immutable data models for printer-specific configuration profiles."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from types import MappingProxyType
from typing import Mapping


def _required_text(value: str, field_name: str) -> str:
    """Return a normalized non-empty text field."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")
    return value.strip()


def _positive_dimension(value: float, field_name: str) -> float:
    """Return a valid positive finite dimension measured in millimetres."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a number in millimetres.")
    if not isfinite(value) or value <= 0:
        raise ValueError(f"{field_name} must be greater than zero.")
    return float(value)


def _text_values(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    """Return validated, non-empty unique text values in their supplied order."""
    if not isinstance(values, tuple) or not values:
        raise ValueError(f"{field_name} must contain at least one value.")

    normalized_values = tuple(_required_text(value, field_name) for value in values)
    if len({value.casefold() for value in normalized_values}) != len(normalized_values):
        raise ValueError(f"{field_name} must not contain duplicate values.")
    return normalized_values


@dataclass(frozen=True, slots=True)
class BleedSettings:
    """Bleed allowance required by a printer profile."""

    size_mm: float

    def __post_init__(self) -> None:
        """Validate the bleed allowance."""
        object.__setattr__(
            self,
            "size_mm",
            _positive_dimension(self.size_mm, "Bleed size"),
        )


@dataclass(frozen=True, slots=True)
class SafeAreaSettings:
    """Safe-area allowance required by a printer profile."""

    size_mm: float

    def __post_init__(self) -> None:
        """Validate the safe-area allowance."""
        object.__setattr__(
            self,
            "size_mm",
            _positive_dimension(self.size_mm, "Safe-area size"),
        )


@dataclass(frozen=True, slots=True)
class BarcodeSettings:
    """Barcode dimensions and placement supplied by a printer profile."""

    width_mm: float
    height_mm: float
    placement: str

    def __post_init__(self) -> None:
        """Validate barcode dimensions and its declared placement."""
        object.__setattr__(
            self,
            "width_mm",
            _positive_dimension(self.width_mm, "Barcode width"),
        )
        object.__setattr__(
            self,
            "height_mm",
            _positive_dimension(self.height_mm, "Barcode height"),
        )
        object.__setattr__(
            self,
            "placement",
            _required_text(self.placement, "Barcode placement"),
        )


@dataclass(frozen=True, slots=True)
class PrinterProfile:
    """A complete printer-specific settings profile without calculation logic."""

    schema_version: int
    name: str
    description: str
    supported_bindings: tuple[str, ...]
    bleed: BleedSettings
    safe_area: SafeAreaSettings
    spine_calculation_method: str
    barcode: BarcodeSettings
    supported_paper_standards: tuple[str, ...]
    supported_export_formats: tuple[str, ...]
    default_measurement_unit: str
    extensions: Mapping[str, object] = field(default_factory=dict)
    is_custom: bool = False

    def __post_init__(self) -> None:
        """Validate profile fields and preserve unrecognized extension data."""
        if (
            isinstance(self.schema_version, bool)
            or not isinstance(self.schema_version, int)
            or self.schema_version < 1
        ):
            raise ValueError("Profile schema version must be a positive integer.")
        if not isinstance(self.bleed, BleedSettings):
            raise ValueError("Profile bleed settings must be BleedSettings.")
        if not isinstance(self.safe_area, SafeAreaSettings):
            raise ValueError("Profile safe-area settings must be SafeAreaSettings.")
        if not isinstance(self.barcode, BarcodeSettings):
            raise ValueError("Profile barcode settings must be BarcodeSettings.")
        if not isinstance(self.is_custom, bool):
            raise ValueError("Profile custom flag must be a boolean.")
        object.__setattr__(self, "name", _required_text(self.name, "Printer name"))
        object.__setattr__(
            self,
            "description",
            _required_text(self.description, "Printer description"),
        )
        object.__setattr__(
            self,
            "supported_bindings",
            _text_values(self.supported_bindings, "Supported bindings"),
        )
        object.__setattr__(
            self,
            "spine_calculation_method",
            _required_text(self.spine_calculation_method, "Spine calculation method"),
        )
        object.__setattr__(
            self,
            "supported_paper_standards",
            _text_values(
                self.supported_paper_standards,
                "Supported paper standards",
            ),
        )
        object.__setattr__(
            self,
            "supported_export_formats",
            _text_values(self.supported_export_formats, "Supported export formats"),
        )
        object.__setattr__(
            self,
            "default_measurement_unit",
            _required_text(self.default_measurement_unit, "Default measurement unit"),
        )
        if not isinstance(self.extensions, Mapping):
            raise ValueError("Profile extensions must be a mapping.")
        object.__setattr__(
            self,
            "extensions",
            MappingProxyType(dict(self.extensions)),
        )
