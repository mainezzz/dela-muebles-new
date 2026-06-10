from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from dela_furnfact.catalog import default_opening_request
from dela_furnfact.models import ContentType, RemainingDistribution, ShelfRequest, VisualDistribution


@dataclass(frozen=True)
class GenerationStatus:
    generated: bool
    button_text: str
    status_text: str


def status_for_generation(generated: bool) -> GenerationStatus:
    if generated:
        return GenerationStatus(
            generated=True,
            button_text="Regenerar proyecto",
            status_text="Proyecto generado",
        )
    return GenerationStatus(
        generated=False,
        button_text="Generar proyecto",
        status_text="Sin generar",
    )


@dataclass
class ProjectFormState:
    content_type: ContentType
    overall_width_mm: int
    overall_height_mm: int
    overall_depth_mm: int
    board_thickness_mm: int = 18
    visual_distribution: VisualDistribution = VisualDistribution.MIXED
    remaining_distribution: RemainingDistribution = RemainingDistribution.AUTO
    opening_quantities: dict[str, int] | None = None
    name: str = "Proyecto DELA"

    @classmethod
    def from_values(
        cls,
        *,
        content_type: ContentType,
        overall_width_mm: int,
        overall_height_mm: int,
        overall_depth_mm: int,
        board_thickness_mm: int = 18,
        visual_distribution: VisualDistribution = VisualDistribution.MIXED,
        remaining_distribution: RemainingDistribution = RemainingDistribution.AUTO,
        opening_quantities: Mapping[str, int] | None = None,
        name: str = "Proyecto DELA",
    ) -> "ProjectFormState":
        return cls(
            content_type=content_type,
            overall_width_mm=overall_width_mm,
            overall_height_mm=overall_height_mm,
            overall_depth_mm=overall_depth_mm,
            board_thickness_mm=board_thickness_mm,
            visual_distribution=visual_distribution,
            remaining_distribution=remaining_distribution,
            opening_quantities=dict(opening_quantities or {}),
            name=name,
        )

    def to_request(self) -> ShelfRequest:
        requested_openings = []
        for type_id, quantity in (self.opening_quantities or {}).items():
            if quantity > 0:
                requested_openings.append(default_opening_request(type_id, quantity))
        return ShelfRequest(
            name=self.name,
            width_mm=float(self.overall_width_mm),
            height_mm=float(self.overall_height_mm),
            depth_mm=float(self.overall_depth_mm),
            board_thickness_mm=float(self.board_thickness_mm),
            content_type=self.content_type,
            visual_distribution=self.visual_distribution,
            remaining_distribution=self.remaining_distribution,
            requested_openings=requested_openings,
        )
