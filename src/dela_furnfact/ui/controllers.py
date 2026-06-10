from __future__ import annotations

from dataclasses import dataclass

from dela_furnfact.application import FurnFactApplicationService
from dela_furnfact.models import ContentType, VisualDistribution
from dela_furnfact.ui.state import ProjectFormState


@dataclass(frozen=True)
class DemoPayload:
    content_type: ContentType
    width_mm: int
    height_mm: int
    depth_mm: int
    board_thickness_mm: int
    visual_distribution: VisualDistribution
    opening_quantities: dict[str, int]

    def to_form_state(self, *, name: str = "Proyecto DELA") -> ProjectFormState:
        return ProjectFormState.from_values(
            content_type=self.content_type,
            overall_width_mm=self.width_mm,
            overall_height_mm=self.height_mm,
            overall_depth_mm=self.depth_mm,
            board_thickness_mm=self.board_thickness_mm,
            visual_distribution=self.visual_distribution,
            opening_quantities=self.opening_quantities,
            name=name,
        )


class ProjectController:
    def __init__(self, app_service: FurnFactApplicationService | None = None) -> None:
        self.app_service = app_service or FurnFactApplicationService()

    def dvd_demo(self) -> DemoPayload:
        return DemoPayload(
            content_type=ContentType.DVD,
            width_mm=2036,
            height_mm=2000,
            depth_mm=200,
            board_thickness_mm=18,
            visual_distribution=VisualDistribution.TOP_BOTTOM_LARGE,
            opening_quantities={"dvd": 6, "boxset": 2},
        )

    def books_44_demo(self) -> DemoPayload:
        return DemoPayload(
            content_type=ContentType.BOOKS,
            width_mm=1636,
            height_mm=2000,
            depth_mm=300,
            board_thickness_mm=18,
            visual_distribution=VisualDistribution.MIXED,
            opening_quantities={"books_small": 4, "books_large": 4},
        )

    def books_53_demo(self) -> DemoPayload:
        return DemoPayload(
            content_type=ContentType.BOOKS,
            width_mm=1636,
            height_mm=2000,
            depth_mm=300,
            board_thickness_mm=18,
            visual_distribution=VisualDistribution.CENTER_LARGE,
            opening_quantities={"books_small": 5, "books_large": 3},
        )

    def generate(self, form_state: ProjectFormState):
        return self.app_service.generate(form_state.to_request())
