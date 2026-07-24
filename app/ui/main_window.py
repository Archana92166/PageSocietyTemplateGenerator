"""Main application window and empty presentation shell."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDockWidget,
    QFrame,
    QLabel,
    QMainWindow,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.resources.loader import ResourceLoader


class MainWindow(QMainWindow):
    """Present the empty, extensible application workspace."""

    def __init__(
        self,
        window_configuration: Mapping[str, Any],
        resource_loader: ResourceLoader,
    ) -> None:
        """Create the main window from presentation configuration."""
        super().__init__()
        self._resource_loader = resource_loader
        self._configure_window(window_configuration)
        self._create_toolbar()
        self._create_navigation_panel()
        self._create_preview_area()
        self._create_properties_panel()
        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Ready")

    def _configure_window(self, configuration: Mapping[str, Any]) -> None:
        """Apply window properties supplied by configuration."""
        self.setWindowTitle(str(configuration["title"]))
        self.resize(int(configuration["width"]), int(configuration["height"]))

    def _create_toolbar(self) -> None:
        """Add the reserved primary toolbar area."""
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setObjectName("mainToolbar")
        toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

    def _create_navigation_panel(self) -> None:
        """Add the empty left navigation panel."""
        self._add_dock("Navigation", Qt.DockWidgetArea.LeftDockWidgetArea, "navigationPanel")

    def _create_properties_panel(self) -> None:
        """Add the empty right properties panel."""
        self._add_dock("Properties", Qt.DockWidgetArea.RightDockWidgetArea, "propertiesPanel")

    def _add_dock(self, title: str, area: Qt.DockWidgetArea, object_name: str) -> None:
        """Create a consistently styled empty dock panel."""
        dock = QDockWidget(title, self)
        dock.setObjectName(object_name)
        dock.setAllowedAreas(area)
        dock.setWidget(self._placeholder_widget(title))
        self.addDockWidget(area, dock)

    def _create_preview_area(self) -> None:
        """Add the central reserved live-preview area."""
        self.setCentralWidget(self._placeholder_widget("Live Preview"))

    @staticmethod
    def _placeholder_widget(label_text: str) -> QWidget:
        """Return a neutral presentation placeholder for an unimplemented area."""
        widget = QFrame()
        widget.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(widget)
        label = QLabel(label_text, widget)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        return widget
