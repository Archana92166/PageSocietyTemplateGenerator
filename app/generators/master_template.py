"""Fixed master-template generation with spine-only geometry updates."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from math import isfinite
from pathlib import Path

from app.generators.definitions import load_master_templates
from app.generators.exceptions import (
    InvalidTemplateError,
    NegativeSpineWidthError,
    TemplateDefinitionsError,
    TemplateNotFoundError,
)
from app.models.template import (
    CoverLayout,
    Guide,
    MasterTemplate,
    Point,
    Rectangle,
)


class MasterTemplateService:
    """Load and provide fixed master template definitions."""

    def __init__(self, templates: Iterable[MasterTemplate]) -> None:
        """Initialize the service with uniquely named master templates."""
        self._templates: dict[str, MasterTemplate] = {}
        for template in templates:
            if not isinstance(template, MasterTemplate):
                raise TemplateDefinitionsError(
                    "Master template entries must be MasterTemplate instances."
                )
            key = template.name.casefold()
            if key in self._templates:
                raise TemplateDefinitionsError(
                    f"Duplicate master template '{template.name}'."
                )
            self._templates[key] = template

    @classmethod
    def from_default_definitions(cls) -> "MasterTemplateService":
        """Create a service using the project's bundled template definitions."""
        project_root = Path(__file__).resolve().parents[2]
        definitions_path = project_root / "config" / "master_templates.json"
        return cls(load_master_templates(definitions_path))

    def get_template(self, size: str) -> MasterTemplate:
        """Return the fixed master template named by the requested book size.

        Raises:
            TemplateNotFoundError: If the size is unsupported.
        """
        if not isinstance(size, str) or not size.strip():
            raise TemplateNotFoundError("Template size must be a non-empty string.")
        try:
            return self._templates[size.strip().casefold()]
        except KeyError as error:
            raise TemplateNotFoundError(
                f"Master template '{size}' was not found."
            ) from error

    def list_templates(self) -> tuple[MasterTemplate, ...]:
        """Return all configured master templates in definition-file order."""
        return tuple(self._templates.values())


class MasterTemplateEngine:
    """Generate complete cover layouts by changing only a template's spine width."""

    def __init__(self) -> None:
        """Initialize the engine and its diagnostic logger."""
        self._logger = logging.getLogger(__name__)

    def generate_layout(
        self,
        template: MasterTemplate,
        spine_width_mm: float,
    ) -> CoverLayout:
        """Return full geometry for a fixed template at the requested spine width.

        All fixed dimensions are read from the supplied template. The spine width is
        the only value accepted as dynamic input.

        Raises:
            InvalidTemplateError: If the template is not valid.
            NegativeSpineWidthError: If the spine width is negative or non-finite.
        """
        if not isinstance(template, MasterTemplate):
            raise InvalidTemplateError("Template must be a MasterTemplate instance.")
        spine_width = self._validated_spine_width(spine_width_mm)
        geometry = template.geometry
        back_cover = Rectangle(0, 0, geometry.trim_width_mm, geometry.trim_height_mm)
        spine = Rectangle(
            geometry.trim_width_mm,
            0,
            spine_width,
            geometry.trim_height_mm,
        )
        front_cover = Rectangle(
            geometry.trim_width_mm + spine_width,
            0,
            geometry.trim_width_mm,
            geometry.trim_height_mm,
        )
        trim_box = Rectangle(
            0,
            0,
            back_cover.width_mm + spine.width_mm + front_cover.width_mm,
            geometry.trim_height_mm,
        )
        bleed_box = Rectangle(
            -geometry.bleed_mm,
            -geometry.bleed_mm,
            trim_box.width_mm + (2 * geometry.bleed_mm),
            trim_box.height_mm + (2 * geometry.bleed_mm),
        )
        safe_areas = self._safe_areas(back_cover, front_cover, geometry.safe_area_mm)
        barcode_area = Rectangle(
            back_cover.x_mm + back_cover.width_mm - geometry.barcode_right_margin_mm
            - geometry.barcode_width_mm,
            back_cover.y_mm + back_cover.height_mm - geometry.barcode_bottom_margin_mm
            - geometry.barcode_height_mm,
            geometry.barcode_width_mm,
            geometry.barcode_height_mm,
        )
        layout = CoverLayout(
            template=template,
            spine_width_mm=spine_width,
            bleed_box=bleed_box,
            trim_box=trim_box,
            safe_areas=safe_areas,
            back_cover=back_cover,
            spine=spine,
            front_cover=front_cover,
            barcode_reserved_area=barcode_area,
            guides=self._guides(back_cover, spine, front_cover, bleed_box),
        )
        self._logger.info(
            "Generated '%s' master layout with %.3f mm spine",
            template.name,
            spine_width,
        )
        return layout

    def update_spine_width(
        self,
        layout: CoverLayout,
        spine_width_mm: float,
    ) -> CoverLayout:
        """Return the same master template layout with only its spine width updated."""
        if not isinstance(layout, CoverLayout):
            raise InvalidTemplateError("Layout must be a CoverLayout instance.")
        return self.generate_layout(layout.template, spine_width_mm)

    @staticmethod
    def _validated_spine_width(spine_width_mm: float) -> float:
        """Validate and normalize the one dynamic master-template value."""
        if isinstance(spine_width_mm, bool) or not isinstance(
            spine_width_mm,
            (int, float),
        ):
            raise NegativeSpineWidthError("Spine width must be a numeric value.")
        if not isfinite(spine_width_mm) or spine_width_mm < 0:
            raise NegativeSpineWidthError(
                "Spine width must be a finite value greater than or equal to zero."
            )
        return float(spine_width_mm)

    @staticmethod
    def _safe_areas(
        back_cover: Rectangle,
        front_cover: Rectangle,
        safe_area_mm: float,
    ) -> tuple[Rectangle, Rectangle]:
        """Return fixed inset safe areas for the back and front cover regions."""
        inset_width = back_cover.width_mm - (2 * safe_area_mm)
        inset_height = back_cover.height_mm - (2 * safe_area_mm)
        if inset_width <= 0 or inset_height <= 0:
            raise InvalidTemplateError("Template safe area does not fit its trim box.")
        return (
            Rectangle(
                back_cover.x_mm + safe_area_mm,
                back_cover.y_mm + safe_area_mm,
                inset_width,
                inset_height,
            ),
            Rectangle(
                front_cover.x_mm + safe_area_mm,
                front_cover.y_mm + safe_area_mm,
                inset_width,
                inset_height,
            ),
        )

    @staticmethod
    def _guides(
        back_cover: Rectangle,
        spine: Rectangle,
        front_cover: Rectangle,
        bleed_box: Rectangle,
    ) -> tuple[Guide, ...]:
        """Return fixed structural guides anchored to the generated regions."""
        top = bleed_box.y_mm
        bottom = bleed_box.y_mm + bleed_box.height_mm
        return (
            Guide(
                "Back cover / spine",
                Point(back_cover.x_mm + back_cover.width_mm, top),
                Point(back_cover.x_mm + back_cover.width_mm, bottom),
            ),
            Guide(
                "Spine / front cover",
                Point(spine.x_mm + spine.width_mm, top),
                Point(spine.x_mm + spine.width_mm, bottom),
            ),
            Guide(
                "Left trim edge",
                Point(back_cover.x_mm, top),
                Point(back_cover.x_mm, bottom),
            ),
            Guide(
                "Right trim edge",
                Point(front_cover.x_mm + front_cover.width_mm, top),
                Point(front_cover.x_mm + front_cover.width_mm, bottom),
            ),
        )
