"""Input validation workflow for requesting a master template preview layout."""

from __future__ import annotations

import logging

from app.generators.exceptions import (
    InvalidPageCountError,
    MissingPrinterProfileError,
    UnsupportedBindingError,
)
from app.generators.master_template import MasterTemplateEngine, MasterTemplateService
from app.models.template import CoverLayout
from app.printer_profiles.exceptions import PrinterProfileNotFoundError
from app.printer_profiles.service import PrinterProfilesService


class MasterTemplateWorkflow:
    """Validate preview inputs and delegate fixed geometry generation to the engine."""

    def __init__(
        self,
        templates: MasterTemplateService,
        engine: MasterTemplateEngine,
        printer_profiles: PrinterProfilesService,
    ) -> None:
        """Initialize the workflow with its explicit service dependencies."""
        self._templates = templates
        self._engine = engine
        self._printer_profiles = printer_profiles
        self._logger = logging.getLogger(__name__)

    def create_layout(
        self,
        book_size: str,
        printer_profile_name: str,
        binding: str,
        page_count: int,
        spine_width_mm: float,
    ) -> CoverLayout:
        """Validate testing inputs and return a layout for an injected spine width.

        The profile and page count are validated here for the future calculation
        module. This workflow deliberately does not calculate spine width.

        Raises:
            MissingPrinterProfileError: If the selected profile does not exist.
            UnsupportedBindingError: If the binding is unsupported by the profile.
            InvalidPageCountError: If page count is not a positive integer.
        """
        self._validate_page_count(page_count)
        try:
            profile = self._printer_profiles.get_profile(printer_profile_name)
        except PrinterProfileNotFoundError as error:
            raise MissingPrinterProfileError(
                f"Printer profile '{printer_profile_name}' was not found."
            ) from error
        if not isinstance(binding, str) or not binding.strip():
            raise UnsupportedBindingError("Binding must be a non-empty string.")
        if binding.casefold() not in {
            supported_binding.casefold()
            for supported_binding in profile.supported_bindings
        }:
            raise UnsupportedBindingError(
                f"Binding '{binding}' is not supported by '{profile.name}'."
            )
        template = self._templates.get_template(book_size)
        layout = self._engine.generate_layout(template, spine_width_mm)
        self._logger.info(
            "Prepared preview layout for %s with profile %s and %s pages",
            book_size,
            profile.name,
            page_count,
        )
        return layout

    @staticmethod
    def _validate_page_count(page_count: int) -> None:
        """Validate a positive non-boolean page count."""
        if isinstance(page_count, bool) or not isinstance(page_count, int):
            raise InvalidPageCountError("Page count must be a positive integer.")
        if page_count <= 0:
            raise InvalidPageCountError("Page count must be greater than zero.")
