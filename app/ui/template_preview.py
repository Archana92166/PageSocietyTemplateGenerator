"""Qt renderer for master-template geometry supplied by the generator engine."""

from __future__ import annotations

from collections.abc import Callable
from math import isfinite

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import (
    QAction,
    QColor,
    QFont,
    QPaintEvent,
    QPainter,
    QPen,
    QResizeEvent,
)
from PySide6.QtWidgets import QWidget

from app.models.template import CoverLayout, Guide, Rectangle


class TemplatePreviewWidget(QWidget):
    """Render a supplied cover layout without performing template calculations."""

    def __init__(self, layout: CoverLayout, parent: QWidget | None = None) -> None:
        """Create a preview widget for the supplied complete layout geometry."""
        super().__init__(parent)
        self._layout = layout
        self._zoom_factor = 1.0
        self._fit_to_window = True
        self.setMinimumSize(360, 260)

    @property
    def layout(self) -> CoverLayout:
        """Return the geometry currently displayed by the preview."""
        return self._layout

    def set_layout(self, layout: CoverLayout) -> None:
        """Replace the rendered geometry and fit it into the available viewport."""
        if not isinstance(layout, CoverLayout):
            raise ValueError("Preview layout must be a CoverLayout instance.")
        self._layout = layout
        self._fit_to_window = True
        self.update()

    def fit_to_window(self) -> None:
        """Fit the supplied layout geometry into the preview viewport."""
        self._zoom_factor = 1.0
        self._fit_to_window = True
        self.update()

    def zoom_in(self) -> None:
        """Increase preview magnification by one stable increment."""
        self._zoom_factor *= 1.2
        self._fit_to_window = False
        self.update()

    def zoom_out(self) -> None:
        """Decrease preview magnification by one stable increment."""
        self._zoom_factor /= 1.2
        self._fit_to_window = False
        self.update()

    def reset_zoom(self) -> None:
        """Restore the preview's initial fit-to-window magnification."""
        self.fit_to_window()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        """Draw only the regions and guides present in the supplied layout."""
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#f4f4f4"))
        scale = self._scale_for_viewport()
        bleed_box = self._layout.bleed_box
        offset_x = (self.width() - (bleed_box.width_mm * scale)) / 2
        offset_y = (self.height() - (bleed_box.height_mm * scale)) / 2
        painter.translate(
            offset_x - (bleed_box.x_mm * scale),
            offset_y - (bleed_box.y_mm * scale),
        )
        painter.scale(scale, scale)
        self._draw_layout(painter)

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        """Refresh fitting previews when the available window space changes."""
        super().resizeEvent(event)
        if self._fit_to_window:
            self.update()

    def _scale_for_viewport(self) -> float:
        """Calculate a view-only transform for the existing bleed bounds."""
        bleed_box = self._layout.bleed_box
        horizontal_padding = 36
        vertical_padding = 36
        available_width = max(1, self.width() - horizontal_padding)
        available_height = max(1, self.height() - vertical_padding)
        fit_scale = min(
            available_width / bleed_box.width_mm,
            available_height / bleed_box.height_mm,
        )
        scale = fit_scale * self._zoom_factor
        return scale if isfinite(scale) and scale > 0 else 1.0

    def _draw_layout(self, painter: QPainter) -> None:
        """Draw all named regions and guide lines from the generated layout."""
        self._draw_region(painter, self._layout.bleed_box, "Bleed", "#fde2e2")
        self._draw_region(painter, self._layout.trim_box, "Trim", "#ffffff")
        for index, safe_area in enumerate(self._layout.safe_areas, start=1):
            self._draw_region(
                painter,
                safe_area,
                f"Safe Area {index}",
                "#e3f4e8",
            )
        self._draw_region(painter, self._layout.back_cover, "Back Cover", "#cfe8ff")
        self._draw_region(painter, self._layout.spine, "Spine", "#ffe5b4")
        self._draw_region(painter, self._layout.front_cover, "Front Cover", "#d8d3ff")
        self._draw_region(
            painter,
            self._layout.barcode_reserved_area,
            "Barcode Reserved Area",
            "#ffd2d2",
        )
        self._draw_guides(painter, self._layout.guides)

    @staticmethod
    def _draw_region(
        painter: QPainter,
        region: Rectangle,
        label: str,
        color: str,
    ) -> None:
        """Draw one supplied region and label its existing dimensions."""
        rectangle = QRectF(region.x_mm, region.y_mm, region.width_mm, region.height_mm)
        painter.setPen(QPen(QColor("#3f3f46"), 0))
        painter.setBrush(QColor(color))
        painter.drawRect(rectangle)
        if region.width_mm <= 0 or region.height_mm <= 0:
            return
        painter.save()
        painter.setPen(QPen(QColor("#18181b"), 0))
        font = QFont(painter.font())
        font.setPointSizeF(max(1.2, min(5.0, region.height_mm / 14)))
        painter.setFont(font)
        text = f"{label}\n{region.width_mm:.1f} × {region.height_mm:.1f} mm"
        painter.drawText(rectangle, Qt.AlignmentFlag.AlignCenter, text)
        painter.restore()

    @staticmethod
    def _draw_guides(painter: QPainter, guides: tuple[Guide, ...]) -> None:
        """Draw guide lines provided by the generated layout."""
        pen = QPen(QColor("#dc2626"), 0, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for guide in guides:
            painter.drawLine(
                guide.start.x_mm,
                guide.start.y_mm,
                guide.end.x_mm,
                guide.end.y_mm,
            )


def create_preview_actions(preview: TemplatePreviewWidget) -> tuple[QAction, ...]:
    """Create reusable zoom actions connected only to preview view operations."""
    actions: tuple[tuple[str, Callable[[], None]], ...] = (
        ("Fit to Window", preview.fit_to_window),
        ("Zoom In", preview.zoom_in),
        ("Zoom Out", preview.zoom_out),
        ("Reset Zoom", preview.reset_zoom),
    )
    return tuple(_action_for(text, callback, preview) for text, callback in actions)


def _action_for(
    text: str,
    callback: Callable[[], None],
    parent: QWidget,
) -> QAction:
    """Create one Qt action from a view callback."""
    action = QAction(text, parent)
    action.triggered.connect(callback)
    return action
