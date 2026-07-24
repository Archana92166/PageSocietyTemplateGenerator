"""Application composition root and lifecycle management."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QApplication, QMessageBox

from app.core.config import ConfigurationLoader
from app.core.errors import ConfigurationError
from app.core.logging_config import configure_logging
from app.generators import (
    MasterTemplateEngine,
    MasterTemplateService,
    MasterTemplateWorkflow,
)
from app.printer_profiles import PrinterProfilesService
from app.resources.loader import ResourceLoader
from app.ui.main_window import MainWindow


class Application:
    """Compose infrastructure and UI, then manage the Qt event loop."""

    def __init__(self) -> None:
        """Prepare application paths and deferred runtime dependencies."""
        self._project_root = Path(__file__).resolve().parents[2]
        self._configuration_path = self._project_root / "config" / "application.json"
        self._resource_directory = self._project_root / "app" / "resources"
        self._logger = logging.getLogger(__name__)

    def run(self) -> int:
        """Initialize the application shell and start the Qt event loop."""
        try:
            configuration = ConfigurationLoader(self._configuration_path).load()
        except ConfigurationError as error:
            logging.getLogger(__name__).exception("Application initialization failed")
            self._show_initialization_error(str(error))
            return 1

        configure_logging(self._logging_configuration(configuration))
        application_config = configuration["application"]
        window_config = configuration["window"]
        qt_application = QApplication.instance() or QApplication(sys.argv)
        qt_application.setApplicationName(str(application_config["name"]))
        qt_application.setOrganizationName(str(application_config["organization_name"]))

        resource_loader = ResourceLoader(self._resource_directory)
        templates = MasterTemplateService.from_default_definitions()
        printer_profiles = PrinterProfilesService.from_default_definitions()
        workflow = MasterTemplateWorkflow(
            templates,
            MasterTemplateEngine(),
            printer_profiles,
        )
        available_templates = templates.list_templates()
        available_profiles = printer_profiles.list_profiles()
        initial_template = available_templates[0]
        initial_profile = available_profiles[0]
        initial_layout = workflow.create_layout(
            initial_template.name,
            initial_profile.name,
            initial_profile.supported_bindings[0],
            page_count=1,
            spine_width_mm=0,
        )
        window = MainWindow(
            window_config,
            resource_loader,
            initial_layout,
            tuple(template.name for template in available_templates),
            available_profiles,
            workflow.create_layout,
        )
        window.show()
        self._logger.info("Application window displayed")
        return qt_application.exec()

    @staticmethod
    def _logging_configuration(configuration: dict[str, Any]) -> dict[str, Any]:
        """Extract optional logging configuration with a safe empty default."""
        logging_configuration = configuration.get("logging", {})
        return logging_configuration if isinstance(logging_configuration, dict) else {}

    @staticmethod
    def _show_initialization_error(message: str) -> None:
        """Show a user-facing initialization error when Qt is available."""
        application = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, "Application Initialization Error", message)
