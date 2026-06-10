
"""Transformaciones de dominio -> preview.

Fase 1 de v13:
- concentra la traducción entre `ProjectBundle` y el widget de preview
- evita que `ShelfPreviewWidget` tenga que interpretar directamente el dominio
"""

from __future__ import annotations

from dela_furnfact.models import ProjectBundle
from dela_furnfact.ui.viewmodels import PreviewRowViewModel, PreviewViewModel


class PreviewMapper:
    """Mapea un bundle a una estructura estable para dibujar preview."""

    @staticmethod
    def from_bundle(
        bundle: ProjectBundle,
        *,
        selected_label: str | None = None,
    ) -> PreviewViewModel:
        normalized_selected = selected_label.strip().lower() if selected_label else None
        row_items = []
        for index, opening in enumerate(bundle.plan.openings):
            highlighted = normalized_selected is not None and opening.label.strip().lower() == normalized_selected
            row_items.append(
                PreviewRowViewModel.from_plan(
                    index,
                    opening,
                    highlighted=highlighted,
                )
            )
        return PreviewViewModel(
            columns=bundle.plan.columns,
            rows=bundle.plan.rows,
            outer_width_mm=bundle.plan.outer_width_mm,
            outer_height_mm=bundle.plan.outer_height_mm,
            board_thickness_mm=bundle.plan.board_thickness_mm,
            row_items=tuple(row_items),
        )


def map_plan_to_preview(plan):
    """Compat helper for tests and decoupled preview state.

    The legacy preview widget consumes a PreviewViewModel built from a full
    ProjectBundle. Architectural phases 7–8 also need a direct `ShelfPlan`
    -> `PreviewViewModel` mapping for lightweight tests and state controllers.
    """
    row_items = []
    for index, opening in enumerate(plan.openings):
        row_items.append(
            PreviewRowViewModel.from_plan(
                index,
                opening,
                highlighted=False,
            )
        )
    return PreviewViewModel(
        columns=plan.columns,
        rows=plan.rows,
        outer_width_mm=plan.outer_width_mm,
        outer_height_mm=plan.outer_height_mm,
        board_thickness_mm=plan.board_thickness_mm,
        row_items=tuple(row_items),
    )
