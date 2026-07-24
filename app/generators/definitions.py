"""Data-driven loading of fixed master template definitions."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from app.generators.exceptions import TemplateDefinitionsError
from app.models.template import MasterTemplate, TemplateGeometry


def load_master_templates(definitions_path: Path) -> tuple[MasterTemplate, ...]:
    """Load fixed master templates from a JSON definitions file.

    Raises:
        TemplateDefinitionsError: If the definition file cannot be loaded or parsed.
    """
    try:
        with definitions_path.open(encoding="utf-8") as file_handle:
            data = json.load(file_handle)
    except FileNotFoundError as error:
        raise TemplateDefinitionsError(
            f"Master template definitions were not found: {definitions_path}"
        ) from error
    except (json.JSONDecodeError, OSError) as error:
        raise TemplateDefinitionsError(
            f"Master template definitions could not be loaded: {error}"
        ) from error

    if not isinstance(data, Mapping) or not isinstance(data.get("templates"), list):
        raise TemplateDefinitionsError(
            "Master template definitions must contain a 'templates' list."
        )
    try:
        return tuple(_build_template(item) for item in data["templates"])
    except (KeyError, TypeError, ValueError) as error:
        raise TemplateDefinitionsError(
            f"Master template definitions are invalid: {error}"
        ) from error


def _build_template(data: object) -> MasterTemplate:
    """Build one validated master template from configuration data."""
    if not isinstance(data, Mapping):
        raise ValueError("Each master template definition must be an object.")
    geometry_data = data["geometry"]
    layer_structure = data["layer_structure"]
    metadata = data.get("metadata", {})
    if not isinstance(geometry_data, Mapping):
        raise ValueError("Template geometry must be an object.")
    if not isinstance(layer_structure, list):
        raise ValueError("Template layer structure must be a list.")
    if not isinstance(metadata, Mapping):
        raise ValueError("Template metadata must be an object.")
    return MasterTemplate(
        schema_version=data["schema_version"],
        name=data["name"],
        geometry=TemplateGeometry(**geometry_data),
        layer_structure=tuple(layer_structure),
        metadata=metadata,
    )
