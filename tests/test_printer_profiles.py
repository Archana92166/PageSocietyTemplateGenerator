"""Unit tests for the data-driven printer profile engine."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import pytest

from app.models import BarcodeSettings, PrinterProfile
from app.printer_profiles import (
    DuplicatePrinterProfileError,
    InvalidPrinterProfileError,
    PrinterProfileNotFoundError,
    PrinterProfilesService,
    ProfileDefinitionsError,
    ProfileRemovalError,
)
from app.printer_profiles.definitions import load_printer_profiles


@pytest.fixture
def printer_profiles() -> PrinterProfilesService:
    """Return a service backed by bundled profile definitions."""
    return PrinterProfilesService.from_default_definitions()


def test_loads_bundled_profiles(printer_profiles: PrinterProfilesService) -> None:
    """The service dynamically loads every required bundled profile."""
    names = {profile.name for profile in printer_profiles.list_profiles()}

    assert {"Amazon KDP", "IngramSpark", "Lulu", "Generic Printer"} <= names


def test_retrieves_profile(printer_profiles: PrinterProfilesService) -> None:
    """A profile lookup returns its declared configuration data."""
    profile = printer_profiles.get_profile("Amazon KDP")

    assert profile.bleed.size_mm == 3.175
    assert profile.default_measurement_unit == "inches"


def test_lists_profiles(printer_profiles: PrinterProfilesService) -> None:
    """Profile listing retains the dynamically discovered profile set."""
    profiles = printer_profiles.list_profiles()

    assert len(profiles) == 4
    assert all(not profile.is_custom for profile in profiles)


def test_registers_and_removes_custom_profile(
    printer_profiles: PrinterProfilesService,
) -> None:
    """A validated profile can be added and later removed as custom data."""
    base_profile = printer_profiles.get_profile("Generic Printer")
    custom_profile = replace(base_profile, name="My Printer")

    registered_profile = printer_profiles.register_profile(custom_profile)

    assert registered_profile.is_custom is True
    assert printer_profiles.get_profile("My Printer") == registered_profile
    assert printer_profiles.remove_custom_profile("My Printer") == registered_profile
    with pytest.raises(PrinterProfileNotFoundError):
        printer_profiles.get_profile("My Printer")


def test_rejects_duplicate_profile_name(
    printer_profiles: PrinterProfilesService,
) -> None:
    """Profile names are unique without regard to case or surrounding spaces."""
    duplicate = replace(
        printer_profiles.get_profile("Generic Printer"),
        name=" generic printer ",
    )

    with pytest.raises(DuplicatePrinterProfileError):
        printer_profiles.register_profile(duplicate)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("supported_bindings", ("Unknown Binding",)),
        ("default_measurement_unit", "yards"),
        ("supported_paper_standards", ("Unknown Standard",)),
    ],
)
def test_rejects_invalid_profile_values(
    printer_profiles: PrinterProfilesService,
    field_name: str,
    value: object,
) -> None:
    """Configured rules reject unsupported bindings, units, and standards."""
    invalid_profile = replace(
        printer_profiles.get_profile("Generic Printer"),
        name="Invalid Profile",
        **{field_name: value},
    )

    with pytest.raises(InvalidPrinterProfileError):
        printer_profiles.validate_profile(invalid_profile)


def test_rejects_invalid_profile_configuration(tmp_path: Path) -> None:
    """The JSON loader reports a meaningful error for malformed profile data."""
    invalid_profile = {
        "schema_version": 1,
        "name": "Broken Profile",
        "description": "Invalid because barcode is absent.",
    }
    profile_path = tmp_path / "broken.json"
    profile_path.write_text(json.dumps(invalid_profile), encoding="utf-8")

    with pytest.raises(ProfileDefinitionsError):
        load_printer_profiles(tmp_path)


def test_rejects_non_positive_barcode_dimension() -> None:
    """Profile dimensions must always be positive millimetre values."""
    with pytest.raises(ValueError):
        BarcodeSettings(
            width_mm=0,
            height_mm=30.48,
            placement="back_cover_bottom_right",
        )


def test_does_not_remove_built_in_profile(
    printer_profiles: PrinterProfilesService,
) -> None:
    """Built-in configuration remains immutable within the running service."""
    with pytest.raises(ProfileRemovalError):
        printer_profiles.remove_custom_profile("Amazon KDP")
