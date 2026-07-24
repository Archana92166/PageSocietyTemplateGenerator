"""Exceptions raised by the master template engine."""


class MasterTemplateError(Exception):
    """Base exception for master template engine failures."""


class TemplateDefinitionsError(MasterTemplateError):
    """Raised when stored master template definitions are invalid."""


class TemplateNotFoundError(MasterTemplateError):
    """Raised when a requested master template is unavailable."""


class InvalidTemplateError(MasterTemplateError):
    """Raised when an invalid master template is supplied to the engine."""


class NegativeSpineWidthError(MasterTemplateError):
    """Raised when a requested spine width is negative or non-finite."""


class MissingPrinterProfileError(MasterTemplateError):
    """Raised when the selected printer profile is unavailable."""


class InvalidPageCountError(MasterTemplateError):
    """Raised when a page count is not a positive integer."""


class UnsupportedBindingError(MasterTemplateError):
    """Raised when a selected binding is unsupported by a printer profile."""
