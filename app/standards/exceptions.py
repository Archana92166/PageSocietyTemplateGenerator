"""Exceptions raised by the paper standards engine."""


class PaperStandardsError(Exception):
    """Base exception for paper standards engine failures."""


class StandardDefinitionsError(PaperStandardsError):
    """Raised when stored paper-standard definitions are invalid."""


class PaperStandardNotFoundError(PaperStandardsError):
    """Raised when a requested paper standard does not exist."""


class PaperSizeNotFoundError(PaperStandardsError):
    """Raised when a requested paper size does not exist."""


class DuplicatePaperSizeError(PaperStandardsError):
    """Raised when a custom paper size name is already registered."""
