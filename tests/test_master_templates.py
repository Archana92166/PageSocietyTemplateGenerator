"""Unit tests for fixed master template generation and preview rendering."""

from __future__ import annotations

import os

import pytest

from app.generators import (
    InvalidPageCountError,
    InvalidTemplateError,
    MasterTemplateEngine,
    MasterTemplateService,
    MasterTemplateWorkflow,
    MissingPrinterProfileError,
    NegativeSpineWidthError,
    TemplateNotFoundError,
    UnsupportedBindingError,
)
from app.printer_profiles import PrinterProfilesService


@pytest.fixture
def templates() -> MasterTemplateService:
    """Return the bundled fixed master template definitions."""
    return MasterTemplateService.from_default_definitions()


@pytest.fixture
def engine() -> MasterTemplateEngine:
    """Return a fresh spine-only master template engine."""
    return MasterTemplateEngine()


@pytest.fixture
def workflow(
    templates: MasterTemplateService,
    engine: MasterTemplateEngine,
) -> MasterTemplateWorkflow:
    """Return an input-validation workflow backed by bundled services."""
    return MasterTemplateWorkflow(
        templates,
        engine,
        PrinterProfilesService.from_default_definitions(),
    )


def test_loads_supported_master_templates(templates: MasterTemplateService) -> None:
    """Every requested master template is loaded from the definition file."""
    names = {template.name for template in templates.list_templates()}

    assert {"A3", "A4", "A5", "A5 Slim", "A6", "A7", "A8"} <= names


def test_generates_complete_fixed_geometry(
    templates: MasterTemplateService,
    engine: MasterTemplateEngine,
) -> None:
    """A layout contains all required regions using fixed template dimensions."""
    layout = engine.generate_layout(templates.get_template("A5"), 12.5)

    assert layout.back_cover.width_mm == 148
    assert layout.front_cover.width_mm == 148
    assert layout.trim_box.height_mm == 210
    assert layout.spine.width_mm == 12.5
    assert layout.trim_box.width_mm == 308.5
    assert len(layout.safe_areas) == 2
    assert layout.barcode_reserved_area.width_mm == 50.8
    assert len(layout.guides) == 4


def test_spine_update_preserves_fixed_template_regions(
    templates: MasterTemplateService,
    engine: MasterTemplateEngine,
) -> None:
    """Only the spine width changes when regenerating the same master template."""
    original = engine.generate_layout(templates.get_template("A6"), 4)
    updated = engine.update_spine_width(original, 18)

    assert updated.spine.width_mm == 18
    assert updated.back_cover == original.back_cover
    assert updated.front_cover.width_mm == original.front_cover.width_mm
    assert updated.front_cover.height_mm == original.front_cover.height_mm
    assert updated.barcode_reserved_area == original.barcode_reserved_area
    assert updated.template == original.template


def test_preview_displays_engine_geometry(
    templates: MasterTemplateService,
    engine: MasterTemplateEngine,
) -> None:
    """The preview stores and renders only a supplied complete layout."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    from app.ui.template_preview import TemplatePreviewWidget

    application = QApplication.instance() or QApplication([])
    initial = engine.generate_layout(templates.get_template("A7"), 3)
    updated = engine.update_spine_width(initial, 7)
    preview = TemplatePreviewWidget(initial)
    preview.resize(800, 600)
    preview.set_layout(updated)
    preview.zoom_in()
    preview.zoom_out()
    preview.reset_zoom()
    preview.show()
    application.processEvents()

    assert application is not None
    assert preview.layout is updated
    assert preview.layout.guides == updated.guides
    preview.close()


def test_rejects_invalid_template_and_spine_width(
    engine: MasterTemplateEngine,
    templates: MasterTemplateService,
) -> None:
    """Invalid template references and negative dynamic widths fail clearly."""
    with pytest.raises(InvalidTemplateError):
        engine.generate_layout(object(), 5)  # type: ignore[arg-type]
    with pytest.raises(NegativeSpineWidthError):
        engine.generate_layout(templates.get_template("A5"), -1)
    with pytest.raises(TemplateNotFoundError):
        templates.get_template("B5")


def test_workflow_validates_profile_binding_and_page_count(
    workflow: MasterTemplateWorkflow,
) -> None:
    """Testing inputs are checked without introducing a spine calculation rule."""
    with pytest.raises(MissingPrinterProfileError):
        workflow.create_layout("A5", "Missing Profile", "Paperback", 100, 5)
    with pytest.raises(UnsupportedBindingError):
        workflow.create_layout("A5", "Amazon KDP", "Wire-O", 100, 5)
    with pytest.raises(InvalidPageCountError):
        workflow.create_layout("A5", "Generic Printer", "Paperback", 0, 5)
