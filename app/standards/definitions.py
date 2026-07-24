"""Loading of data-driven paper-standard definitions."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from app.models.paper import PaperSize, PaperStandard
from app.standards.exceptions import StandardDefinitionsError


def load_paper_standards(definitions_path: Path) -> tuple[PaperStandard, ...]:
    """Load paper standards from a JSON definitions file.

    Args:
        definitions_path: Path to the JSON file containing paper definitions.

    Raises:
        StandardDefinitionsError: If the file cannot be read or is invalid.
    """
    try:
        with definitions_path.open(encoding="utf-8") as file_handle:
            data = json.load(file_handle)
    except FileNotFoundError as error:
        raise StandardDefinitionsError(
            f"Paper definitions file was not found: {definitions_path}"
        ) from error
    except (json.JSONDecodeError, OSError) as error:
        raise StandardDefinitionsError(
            f"Paper definitions file could not be loaded: {error}"
        ) from error

    if not isinstance(data, Mapping) or not isinstance(data.get("standards"), list):
        raise StandardDefinitionsError(
            "Paper definitions must contain a 'standards' list."
        )

    try:
        return tuple(_build_standard(item) for item in data["standards"])
    except (KeyError, TypeError, ValueError) as error:
        raise StandardDefinitionsError(
            f"Paper definitions are invalid: {error}"
        ) from error


def _build_standard(data: object) -> PaperStandard:
    """Build a validated standard model from a definition object."""
    if not isinstance(data, Mapping):
        raise ValueError("Each paper standard definition must be an object.")

    name = data["name"]
    sizes = data["sizes"]
    if not isinstance(name, str) or not isinstance(sizes, list):
        raise ValueError("Each paper standard requires a name and a sizes list.")

    paper_sizes = tuple(_build_size(name, size) for size in sizes)
    return PaperStandard(name=name, sizes=paper_sizes)


def _build_size(standard_name: str, data: object) -> PaperSize:
    """Build a validated paper-size model from a definition object."""
    if not isinstance(data, Mapping):
        raise ValueError("Each paper size definition must be an object.")
    return PaperSize(
        name=data["name"],
        width_mm=data["width_mm"],
        height_mm=data["height_mm"],
        standard_name=standard_name,
    )
