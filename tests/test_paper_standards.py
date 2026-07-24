"""Unit tests for the data-driven paper standards engine."""

from __future__ import annotations

import pytest

from app.standards import (
    DuplicatePaperSizeError,
    PaperSizeNotFoundError,
    PaperStandardNotFoundError,
    PaperStandardsService,
)


@pytest.fixture
def paper_standards() -> PaperStandardsService:
    """Return a service backed by the bundled definitions."""
    return PaperStandardsService.from_default_definitions()


def test_loads_bundled_standards(paper_standards: PaperStandardsService) -> None:
    """Bundled definitions expose every required paper-standard category."""
    names = {standard.name for standard in paper_standards.list_standards()}

    assert {
        "ISO A",
        "ISO B",
        "ISO C",
        "US",
        "Square",
        "Signature/Folio",
        "Custom",
    } <= names


def test_retrieves_paper_size_by_name(paper_standards: PaperStandardsService) -> None:
    """A globally unique size name resolves to its millimetre dimensions."""
    size = paper_standards.get_size("A5")

    assert size.standard_name == "ISO A"
    assert size.width_mm == 148.0
    assert size.height_mm == 210.0


def test_lists_standard_sizes(paper_standards: PaperStandardsService) -> None:
    """A standard lookup returns its configured sizes in stored order."""
    sizes = paper_standards.list_sizes("ISO A")

    assert sizes[0].name == "A0"
    assert sizes[-1].name == "A10"


def test_registers_custom_size(paper_standards: PaperStandardsService) -> None:
    """A custom paper size is retrievable and appears under Custom."""
    custom_size = paper_standards.register_custom_size("Novel Trim", 127, 203.2)

    assert custom_size.is_custom is True
    assert paper_standards.get_size("Novel Trim") == custom_size
    assert paper_standards.list_sizes("Custom") == (custom_size,)


@pytest.mark.parametrize(
    ("name", "width_mm", "height_mm"),
    [("", 100, 200), ("Invalid!", 100, 200), ("Valid", 0, 200), ("Valid", 100, -1)],
)
def test_rejects_invalid_custom_size_input(
    paper_standards: PaperStandardsService,
    name: str,
    width_mm: float,
    height_mm: float,
) -> None:
    """Custom sizes require valid names and positive dimensions."""
    with pytest.raises(ValueError):
        paper_standards.register_custom_size(name, width_mm, height_mm)


def test_rejects_duplicate_custom_size(paper_standards: PaperStandardsService) -> None:
    """Custom names remain unique without regard to case or surrounding space."""
    paper_standards.register_custom_size("My Trim", 100, 200)

    with pytest.raises(DuplicatePaperSizeError):
        paper_standards.register_custom_size(" my trim ", 110, 210)


def test_reports_unknown_standard_and_size(
    paper_standards: PaperStandardsService,
) -> None:
    """Unknown names raise the engine's focused lookup exceptions."""
    with pytest.raises(PaperStandardNotFoundError):
        paper_standards.get_standard("Unknown")
    with pytest.raises(PaperSizeNotFoundError):
        paper_standards.get_size("Unknown")
