"""Exceptions raised by the printer profile engine."""


class PrinterProfilesError(Exception):
    """Base exception for printer profile engine failures."""


class ProfileDefinitionsError(PrinterProfilesError):
    """Raised when profile configuration files are unavailable or invalid."""


class PrinterProfileNotFoundError(PrinterProfilesError):
    """Raised when a requested printer profile does not exist."""


class DuplicatePrinterProfileError(PrinterProfilesError):
    """Raised when a printer profile name is already registered."""


class InvalidPrinterProfileError(PrinterProfilesError):
    """Raised when a profile conflicts with the configured validation rules."""


class ProfileRemovalError(PrinterProfilesError):
    """Raised when a profile cannot be removed from the active service."""
