"""Dynamic loading of JSON printer-profile definitions and validation rules."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from app.models.printer_profile import (
    BarcodeSettings,
    BleedSettings,
    PrinterProfile,
    SafeAreaSettings,
)
from app.printer_profiles.exceptions import ProfileDefinitionsError


def load_printer_profiles(profile_directory: Path) -> tuple[PrinterProfile, ...]:
    """Load every JSON printer profile found in a configuration directory.

    Raises:
        ProfileDefinitionsError: If no profiles are present or a file is invalid.
    """
    if not profile_directory.is_dir():
        raise ProfileDefinitionsError(
            f"Printer profile directory was not found: {profile_directory}"
        )

    paths = sorted(profile_directory.glob("*.json"))
    if not paths:
        raise ProfileDefinitionsError(
            f"No printer profile files were found in: {profile_directory}"
        )
    return tuple(_load_profile(path) for path in paths)


def load_validation_rules(rules_path: Path) -> dict[str, frozenset[str]]:
    """Load configuration-driven sets of supported profile values.

    Raises:
        ProfileDefinitionsError: If the rules file is unavailable or invalid.
    """
    data = _load_json(rules_path)
    if not isinstance(data, Mapping):
        raise ProfileDefinitionsError("Printer profile rules must be a JSON object.")

    rules: dict[str, frozenset[str]] = {}
    for rule_name, values in data.items():
        if not isinstance(rule_name, str) or not isinstance(values, list):
            raise ProfileDefinitionsError("Each profile rule must contain a list.")
        if not all(isinstance(value, str) and value.strip() for value in values):
            raise ProfileDefinitionsError(
                "Profile rules must contain non-empty strings."
            )
        rules[rule_name] = frozenset(value.casefold() for value in values)
    return rules


def _load_profile(path: Path) -> PrinterProfile:
    """Build one validated profile model from a JSON definition file."""
    data = _load_json(path)
    if not isinstance(data, Mapping):
        raise ProfileDefinitionsError(f"Profile '{path.name}' must be a JSON object.")

    try:
        return PrinterProfile(
            schema_version=data["schema_version"],
            name=data["name"],
            description=data["description"],
            supported_bindings=_text_list_value(data, "supported_bindings"),
            bleed=BleedSettings(**_mapping_value(data, "bleed")),
            safe_area=SafeAreaSettings(**_mapping_value(data, "safe_area")),
            spine_calculation_method=data["spine_calculation_method"],
            barcode=BarcodeSettings(**_mapping_value(data, "barcode")),
            supported_paper_standards=_text_list_value(
                data,
                "supported_paper_standards",
            ),
            supported_export_formats=_text_list_value(
                data,
                "supported_export_formats",
            ),
            default_measurement_unit=data["default_measurement_unit"],
            extensions=_mapping_value(data, "extensions", required=False),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ProfileDefinitionsError(
            f"Profile '{path.name}' is invalid: {error}"
        ) from error


def _load_json(path: Path) -> object:
    """Read and decode one JSON configuration file."""
    try:
        with path.open(encoding="utf-8") as file_handle:
            return json.load(file_handle)
    except FileNotFoundError as error:
        raise ProfileDefinitionsError(
            f"Configuration file was not found: {path}"
        ) from error
    except (json.JSONDecodeError, OSError) as error:
        raise ProfileDefinitionsError(
            f"Configuration file could not be loaded: {path}: {error}"
        ) from error


def _mapping_value(
    data: Mapping[str, object],
    key: str,
    *,
    required: bool = True,
) -> Mapping[str, object]:
    """Return a required object value, or a safe empty mapping when optional."""
    value = data.get(key, {} if not required else None)
    if not isinstance(value, Mapping):
        raise ValueError(f"'{key}' must be an object.")
    return value


def _text_list_value(
    data: Mapping[str, object],
    key: str,
) -> tuple[str, ...]:
    """Return a required list of text values from a profile definition."""
    value = data.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"'{key}' must be a list of strings.")
    return tuple(value)
