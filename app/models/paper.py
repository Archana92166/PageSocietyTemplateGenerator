"""Immutable data models for paper standards and dimensions."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
import re


_PAPER_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 /_-]*$")


def _validated_name(value: str, field_name: str) -> str:
    """Return a normalized paper-related name after validating it."""
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string.")

    normalized_value = value.strip()
    if not normalized_value or not _PAPER_NAME_PATTERN.fullmatch(normalized_value):
        raise ValueError(
            f"{field_name} must start with a letter or number and may contain "
            "letters, numbers, spaces, '/', '_' and '-'."
        )
    return normalized_value


def _validated_dimension(value: float, field_name: str) -> float:
    """Return a valid positive finite millimetre dimension."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a number in millimetres.")
    if not isfinite(value) or value <= 0:
        raise ValueError(f"{field_name} must be greater than zero.")
    return float(value)


@dataclass(frozen=True, slots=True)
class PaperSize:
    """A named paper size expressed in millimetres."""

    name: str
    width_mm: float
    height_mm: float
    standard_name: str
    is_custom: bool = False

    def __post_init__(self) -> None:
        """Validate and normalize this paper-size record."""
        object.__setattr__(self, "name", _validated_name(self.name, "Paper size name"))
        object.__setattr__(
            self,
            "standard_name",
            _validated_name(self.standard_name, "Paper standard name"),
        )
        object.__setattr__(
            self,
            "width_mm",
            _validated_dimension(self.width_mm, "Paper width"),
        )
        object.__setattr__(
            self,
            "height_mm",
            _validated_dimension(self.height_mm, "Paper height"),
        )


@dataclass(frozen=True, slots=True)
class CustomPaperSize(PaperSize):
    """A user-registered paper size held in the Custom standard."""

    standard_name: str = field(default="Custom", init=False)
    is_custom: bool = field(default=True, init=False)


@dataclass(frozen=True, slots=True)
class PaperStandard:
    """A named collection of paper sizes."""

    name: str
    sizes: tuple[PaperSize, ...]

    def __post_init__(self) -> None:
        """Validate the standard name and ensure all sizes belong to it."""
        normalized_name = _validated_name(self.name, "Paper standard name")
        object.__setattr__(self, "name", normalized_name)
        if not isinstance(self.sizes, tuple):
            raise ValueError("Paper standard sizes must be an immutable tuple.")
        if any(size.standard_name != normalized_name for size in self.sizes):
            raise ValueError("Each paper size must belong to its paper standard.")
