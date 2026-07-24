"""Main window that presents master template layouts and preview controls."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDockWidget,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QMainWindow,
    QSpinBox,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.generators.exceptions import MasterTemplateError
from app.models.printer_profile import PrinterProfile
from app.models.template import CoverLayout
from app.resources.loader import ResourceLoader
from app.ui.template_preview import TemplatePreviewWidget, create_preview_actions


LayoutRequest = Callable[[str, str, str, int, float], CoverLayout]


class MainWindow(QMainWindow):
    """Present master template controls and a geometry-driven live preview."""

    def __init__(
        self,
        window_configuration: Mapping[str, Any],
        resource_loader: ResourceLoader,
        initial_layout: CoverLayout,
        templates: tuple[str, ...],
        printer_profiles: tuple[PrinterProfile, ...],
        layout_request: LayoutRequest,
    ) -> None:
        """Create the window from presentation data and an injected layout request."""
        super().__init__()
        self._resource_loader = resource_loader
        self._layout_request = layout_request
        self._printer_profiles = {profile.name: profile for profile in printer_profiles}
        self._configure_window(window_configuration)
        self._create_preview_area(initial_layout)
        self._create_toolbar()
        self._create_properties_panel()
        self.setStatusBar(QStatusBar(self))
        self._show_layout_details(initial_layout)
        self._create_navigation_panel(templates)
        self.statusBar().showMessage("Ready")

    def _configure_window(self, configuration: Mapping[str, Any]) -> None:
        """Apply window properties supplied by configuration."""
        self.setWindowTitle(str(configuration["title"]))
        self.resize(int(configuration["width"]), int(configuration["height"]))

    def _create_toolbar(self) -> None:
        """Add view-only preview controls to the primary toolbar."""
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setObjectName("mainToolbar")
        toolbar.setMovable(False)
        toolbar.addActions(create_preview_actions(self._preview))
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

    def _create_navigation_panel(self, templates: tuple[str, ...]) -> None:
        """Add testing inputs for requesting master template layouts."""
        dock = QDockWidget("Navigation", self)
        dock.setObjectName("navigationPanel")
        dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        panel = QWidget(dock)
        form = QFormLayout(panel)

        self._template_selector = QComboBox(panel)
        self._template_selector.addItems(templates)
        self._profile_selector = QComboBox(panel)
        self._profile_selector.addItems(tuple(self._printer_profiles))
        self._binding_selector = QComboBox(panel)
        self._page_count = QSpinBox(panel)
        self._page_count.setMinimum(1)
        self._page_count.setMaximum(2_147_483_647)
        self._page_count.setValue(1)
        self._spine_width = QDoubleSpinBox(panel)
        self._spine_width.setMinimum(0)
        self._spine_width.setMaximum(10_000)
        self._spine_width.setDecimals(3)
        self._spine_width.setSuffix(" mm")

        form.addRow("Book Size", self._template_selector)
        form.addRow("Printer Profile", self._profile_selector)
        form.addRow("Binding", self._binding_selector)
        form.addRow("Page Count", self._page_count)
        form.addRow("Spine Width", self._spine_width)
        dock.setWidget(panel)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)

        self._profile_selector.currentTextChanged.connect(self._update_binding_options)
        self._template_selector.currentTextChanged.connect(self._request_layout)
        self._binding_selector.currentTextChanged.connect(self._request_layout)
        self._page_count.valueChanged.connect(self._request_layout)
        self._spine_width.valueChanged.connect(self._request_layout)
        self._update_binding_options(self._profile_selector.currentText())

    def _create_properties_panel(self) -> None:
        """Add a read-only summary of the supplied generated geometry."""
        dock = QDockWidget("Properties", self)
        dock.setObjectName("propertiesPanel")
        dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        panel = QWidget(dock)
        layout = QVBoxLayout(panel)
        self._properties_label = QLabel(panel)
        self._properties_label.setWordWrap(True)
        self._properties_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout.addWidget(self._properties_label)
        layout.addStretch()
        dock.setWidget(panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

    def _create_preview_area(self, initial_layout: CoverLayout) -> None:
        """Replace the placeholder with a geometry-only template preview."""
        self._preview = TemplatePreviewWidget(initial_layout, self)
        self.setCentralWidget(self._preview)

    def _update_binding_options(self, profile_name: str) -> None:
        """Present the bindings declared by the selected profile configuration."""
        profile = self._printer_profiles.get(profile_name)
        if profile is None:
            return
        blocker = QSignalBlocker(self._binding_selector)
        self._binding_selector.clear()
        self._binding_selector.addItems(profile.supported_bindings)
        del blocker
        self._request_layout()

    def _request_layout(self, *args: object) -> None:
        """Request presentational geometry from the injected application workflow."""
        del args
        try:
            layout = self._layout_request(
                self._template_selector.currentText(),
                self._profile_selector.currentText(),
                self._binding_selector.currentText(),
                self._page_count.value(),
                self._spine_width.value(),
            )
        except MasterTemplateError as error:
            self.statusBar().showMessage(str(error), 5_000)
            return
        self._preview.set_layout(layout)
        self._show_layout_details(layout)
        self.statusBar().showMessage("Preview updated")

    def _show_layout_details(self, layout: CoverLayout) -> None:
        """Display dimensions already supplied by the generated layout."""
        template_geometry = layout.template.geometry
        self._properties_label.setText(
            "\n".join(
                (
                    f"Template: {layout.template.name}",
                    f"Trim: {template_geometry.trim_width_mm:.1f} × "
                    f"{template_geometry.trim_height_mm:.1f} mm",
                    f"Spine: {layout.spine_width_mm:.1f} mm",
                    f"Bleed: {template_geometry.bleed_mm:.1f} mm",
                    f"Safe Area: {template_geometry.safe_area_mm:.1f} mm",
                    f"Total Width: {layout.trim_box.width_mm:.1f} mm",
                    f"Total Height: {layout.trim_box.height_mm:.1f} mm",
                )
            )
        )
