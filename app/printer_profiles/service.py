"""Public service API for printer-profile lookup and registration."""

from __future__ import annotations

from dataclasses import replace
import logging
from collections.abc import Iterable, Mapping
from pathlib import Path

from app.models.printer_profile import PrinterProfile
from app.printer_profiles.definitions import (
    load_printer_profiles,
    load_validation_rules,
)
from app.printer_profiles.exceptions import (
    DuplicatePrinterProfileError,
    InvalidPrinterProfileError,
    PrinterProfileNotFoundError,
    ProfileDefinitionsError,
    ProfileRemovalError,
)
from app.standards.service import PaperStandardsService
from app.standards.exceptions import PaperStandardNotFoundError


class PrinterProfilesService:
    """Provide validated lookup and runtime registration of printer profiles."""

    def __init__(
        self,
        profiles: Iterable[PrinterProfile],
        validation_rules: Mapping[str, frozenset[str]],
        paper_standards: PaperStandardsService,
    ) -> None:
        """Initialize the service with profiles, rules, and paper standards.

        Raises:
            InvalidPrinterProfileError: If a supplied profile fails validation.
            ProfileDefinitionsError: If profile names or validation rules conflict.
        """
        self._logger = logging.getLogger(__name__)
        self._validation_rules = self._validate_rules(validation_rules)
        self._paper_standards = paper_standards
        self._profiles: dict[str, PrinterProfile] = {}
        self._custom_profiles: dict[str, PrinterProfile] = {}
        for profile in profiles:
            self._add_profile(profile, is_custom=False)

    @classmethod
    def from_default_definitions(cls) -> "PrinterProfilesService":
        """Create a service by dynamically loading bundled JSON definitions."""
        project_root = Path(__file__).resolve().parents[2]
        profiles_path = project_root / "config" / "printer_profiles"
        rules_path = project_root / "config" / "printer_profile_rules.json"
        return cls(
            profiles=load_printer_profiles(profiles_path),
            validation_rules=load_validation_rules(rules_path),
            paper_standards=PaperStandardsService.from_default_definitions(),
        )

    def list_profiles(self) -> tuple[PrinterProfile, ...]:
        """Return all built-in and custom profiles in registration order."""
        return tuple(self._profiles.values())

    def get_profile(self, name: str) -> PrinterProfile:
        """Return the profile identified by name.

        Raises:
            PrinterProfileNotFoundError: If no matching profile exists.
        """
        key = self._profile_key(name)
        try:
            return self._profiles[key]
        except KeyError as error:
            raise PrinterProfileNotFoundError(
                f"Printer profile '{name}' was not found."
            ) from error

    def register_profile(self, profile: PrinterProfile) -> PrinterProfile:
        """Validate, register, and return a custom printer profile.

        Raises:
            DuplicatePrinterProfileError: If the profile name is already used.
            InvalidPrinterProfileError: If the profile does not satisfy the rules.
        """
        custom_profile = replace(profile, is_custom=True)
        self._add_profile(custom_profile, is_custom=True)
        self._logger.info("Registered custom printer profile '%s'", profile.name)
        return custom_profile

    def remove_custom_profile(self, name: str) -> PrinterProfile:
        """Remove and return a registered custom profile.

        Raises:
            ProfileRemovalError: If the profile is built-in or not custom.
        """
        key = self._profile_key(name)
        try:
            profile = self._custom_profiles.pop(key)
        except KeyError as error:
            raise ProfileRemovalError(
                f"Custom printer profile '{name}' cannot be removed."
            ) from error
        del self._profiles[key]
        self._logger.info("Removed custom printer profile '%s'", profile.name)
        return profile

    def validate_profile(self, profile: PrinterProfile) -> None:
        """Validate a profile against configured rules and paper standards.

        Raises:
            InvalidPrinterProfileError: If any profile field is unsupported.
        """
        if not isinstance(profile, PrinterProfile):
            raise InvalidPrinterProfileError(
                "Profile must be a PrinterProfile instance."
            )
        self._validate_values(
            profile.supported_bindings,
            "bindings",
            "supported bindings",
        )
        self._validate_values(
            profile.supported_export_formats,
            "export_formats",
            "supported export formats",
        )
        self._validate_values(
            (profile.default_measurement_unit,),
            "measurement_units",
            "default measurement unit",
        )
        self._validate_values(
            (profile.barcode.placement,),
            "barcode_placements",
            "barcode placement",
        )
        self._validate_values(
            (profile.spine_calculation_method,),
            "spine_calculation_methods",
            "spine calculation method",
        )
        for standard_name in profile.supported_paper_standards:
            try:
                self._paper_standards.get_standard(standard_name)
            except (PaperStandardNotFoundError, ValueError) as error:
                raise InvalidPrinterProfileError(
                    f"Profile '{profile.name}' contains unsupported paper standard "
                    f"'{standard_name}'."
                ) from error

    def _add_profile(self, profile: PrinterProfile, *, is_custom: bool) -> None:
        """Validate and index one profile while preserving registration order."""
        if not isinstance(profile, PrinterProfile):
            raise InvalidPrinterProfileError(
                "Profile must be a PrinterProfile instance."
            )
        key = self._profile_key(profile.name)
        if key in self._profiles:
            raise DuplicatePrinterProfileError(
                f"Printer profile '{profile.name}' is already registered."
            )
        self.validate_profile(profile)
        self._profiles[key] = profile
        if is_custom:
            self._custom_profiles[key] = profile

    def _validate_values(
        self,
        values: tuple[str, ...],
        rule_name: str,
        field_name: str,
    ) -> None:
        """Ensure values appear in the dynamically loaded validation rule set."""
        allowed_values = self._validation_rules[rule_name]
        invalid_values = [
            value for value in values if value.casefold() not in allowed_values
        ]
        if invalid_values:
            values_text = ", ".join(f"'{value}'" for value in invalid_values)
            raise InvalidPrinterProfileError(
                f"Profile has invalid {field_name}: {values_text}."
            )

    @staticmethod
    def _profile_key(name: str) -> str:
        """Return a validated case-insensitive profile lookup key."""
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Printer profile name must be a non-empty string.")
        return name.strip().casefold()

    @staticmethod
    def _validate_rules(
        rules: Mapping[str, frozenset[str]],
    ) -> dict[str, frozenset[str]]:
        """Validate the rule contract required to assess every profile field."""
        required_rules = {
            "bindings",
            "export_formats",
            "measurement_units",
            "barcode_placements",
            "spine_calculation_methods",
        }
        missing_rules = required_rules.difference(rules)
        if missing_rules:
            names = ", ".join(sorted(missing_rules))
            raise ProfileDefinitionsError(
                f"Printer profile validation rules are missing: {names}."
            )
        return dict(rules)
