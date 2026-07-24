"""Immutable geometry models for fixed master cover templates."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from types import MappingProxyType
from typing import Mapping


def _finite_number(value: float, field_name: str) -> float:
    """Return a finite numeric coordinate or dimension value."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be numeric.")
    if not isfinite(value):
        raise ValueError(f"{field_name} must be finite.")
    return float(value)


def _positive_number(value: float, field_name: str) -> float:
    """Return a positive finite dimension value."""
    normalized_value = _finite_number(value, field_name)
    if normalized_value <= 0:
        raise ValueError(f"{field_name} must be greater than zero.")
    return normalized_value


def _nonnegative_number(value: float, field_name: str) -> float:
    """Return a non-negative finite coordinate span value."""
    normalized_value = _finite_number(value, field_name)
    if normalized_value < 0:
        raise ValueError(f"{field_name} must not be negative.")
    return normalized_value


def _required_text(value: str, field_name: str) -> str:
    """Return a normalized non-empty text value."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")
    return value.strip()


@dataclass(frozen=True, slots=True)
class Point:
    """A two-dimensional millimetre coordinate."""

    x_mm: float
    y_mm: float

    def __post_init__(self) -> None:
        """Validate coordinate values."""
        object.__setattr__(self, "x_mm", _finite_number(self.x_mm, "Point x"))
        object.__setattr__(self, "y_mm", _finite_number(self.y_mm, "Point y"))


@dataclass(frozen=True, slots=True)
class Rectangle:
    """An axis-aligned rectangle expressed in millimetres."""

    x_mm: float
    y_mm: float
    width_mm: float
    height_mm: float

    def __post_init__(self) -> None:
        """Validate rectangle coordinates and dimensions."""
        object.__setattr__(self, "x_mm", _finite_number(self.x_mm, "Rectangle x"))
        object.__setattr__(self, "y_mm", _finite_number(self.y_mm, "Rectangle y"))
        object.__setattr__(
            self,
            "width_mm",
            _nonnegative_number(self.width_mm, "Rectangle width"),
        )
        object.__setattr__(
            self,
            "height_mm",
            _nonnegative_number(self.height_mm, "Rectangle height"),
        )


@dataclass(frozen=True, slots=True)
class Guide:
    """A named non-rendering line included in a master template layout."""

    name: str
    start: Point
    end: Point

    def __post_init__(self) -> None:
        """Validate the guide's name and endpoints."""
        object.__setattr__(self, "name", _required_text(self.name, "Guide name"))
        if not isinstance(self.start, Point) or not isinstance(self.end, Point):
            raise ValueError("Guide endpoints must be Point instances.")


@dataclass(frozen=True, slots=True)
class TemplateGeometry:
    """Fixed physical dimensions that define one master cover template."""

    trim_width_mm: float
    trim_height_mm: float
    bleed_mm: float
    safe_area_mm: float
    barcode_width_mm: float
    barcode_height_mm: float
    barcode_right_margin_mm: float
    barcode_bottom_margin_mm: float

    def __post_init__(self) -> None:
        """Validate all fixed template dimensions."""
        for field_name in self.__dataclass_fields__:
            value = getattr(self, field_name)
            object.__setattr__(
                self,
                field_name,
                _positive_number(value, field_name.replace("_", " ")),
            )
        if self.barcode_width_mm > self.trim_width_mm:
            raise ValueError("Barcode width must fit within the trim width.")
        if self.barcode_height_mm > self.trim_height_mm:
            raise ValueError("Barcode height must fit within the trim height.")


@dataclass(frozen=True, slots=True)
class MasterTemplate:
    """A fixed cover-template definition whose spine width is supplied at runtime."""

    schema_version: int
    name: str
    geometry: TemplateGeometry
    layer_structure: tuple[str, ...]
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate the master template and preserve extension metadata."""
        if (
            isinstance(self.schema_version, bool)
            or not isinstance(self.schema_version, int)
            or self.schema_version < 1
        ):
            raise ValueError("Template schema version must be a positive integer.")
        object.__setattr__(self, "name", _required_text(self.name, "Template name"))
        if not isinstance(self.geometry, TemplateGeometry):
            raise ValueError("Template geometry must be a TemplateGeometry instance.")
        if not isinstance(self.layer_structure, tuple) or not self.layer_structure:
            raise ValueError(
                "Template layer structure must contain at least one layer."
            )
        layers = tuple(
            _required_text(layer, "Template layer name")
            for layer in self.layer_structure
        )
        if len({layer.casefold() for layer in layers}) != len(layers):
            raise ValueError("Template layer structure must not contain duplicates.")
        object.__setattr__(self, "layer_structure", layers)
        if not isinstance(self.metadata, Mapping):
            raise ValueError("Template metadata must be a mapping.")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True, slots=True)
class CoverLayout:
    """Complete generated cover geometry for one fixed template and spine width."""

    template: MasterTemplate
    spine_width_mm: float
    bleed_box: Rectangle
    trim_box: Rectangle
    safe_areas: tuple[Rectangle, ...]
    back_cover: Rectangle
    spine: Rectangle
    front_cover: Rectangle
    barcode_reserved_area: Rectangle
    guides: tuple[Guide, ...]

    def __post_init__(self) -> None:
        """Validate generated layout components."""
        if not isinstance(self.template, MasterTemplate):
            raise ValueError("Layout template must be a MasterTemplate instance.")
        if self.spine_width_mm < 0 or not isfinite(self.spine_width_mm):
            raise ValueError("Layout spine width must be a finite non-negative value.")
        object.__setattr__(self, "spine_width_mm", float(self.spine_width_mm))
        rectangle_fields = (
            "bleed_box",
            "trim_box",
            "back_cover",
            "spine",
            "front_cover",
            "barcode_reserved_area",
        )
        if any(
            not isinstance(getattr(self, field_name), Rectangle)
            for field_name in rectangle_fields
        ):
            raise ValueError("Layout regions must be Rectangle instances.")
        if not isinstance(self.safe_areas, tuple) or not self.safe_areas:
            raise ValueError("Layout must contain safe-area rectangles.")
        if not all(isinstance(area, Rectangle) for area in self.safe_areas):
            raise ValueError("Layout safe areas must be Rectangle instances.")
        if not isinstance(self.guides, tuple) or not all(
            isinstance(guide, Guide) for guide in self.guides
        ):
            raise ValueError("Layout guides must be Guide instances.")
