from __future__ import annotations

from dataclasses import dataclass

from dela_furnfact.ui.preview_mapper import PreviewViewModel
from dela_furnfact.ui.preview_state import PreviewBadge, PreviewPanelState, PreviewRowState, PreviewUiMode


@dataclass(frozen=True)
class PreviewHeaderState:
    title: str
    subtitle: str
    mode_label: str


class PreviewController:
    def empty_state(self, *, mode: PreviewUiMode) -> PreviewPanelState:
        message = (
            "Genera un proyecto para ver una propuesta."
            if mode is PreviewUiMode.VISUAL
            else "Genera un proyecto para ver la vista técnica."
        )
        return PreviewPanelState(mode=mode, rows=tuple(), columns=0, empty_message=message)

    def from_view_model(
        self,
        preview_vm: PreviewViewModel | None,
        *,
        mode: PreviewUiMode,
    ) -> PreviewPanelState:
        if preview_vm is None:
            return self.empty_state(mode=mode)

        rows = []
        for row in preview_vm.row_items:
            rows.append(
                PreviewRowState(
                    opening_type_id=row.source_label,
                    preview_label=row.short_label,
                    technical_label=row.display_label,
                    clear_height_mm=int(round(row.clear_height_mm)),
                    quantity=1,
                    visual_badge=PreviewBadge(text=row.short_label),
                    show_visual_badge=mode is PreviewUiMode.VISUAL,
                    show_technical_label=mode is PreviewUiMode.TECHNICAL,
                    show_technical_height=mode is PreviewUiMode.TECHNICAL,
                )
            )
        return PreviewPanelState(mode=mode, rows=tuple(rows), columns=preview_vm.columns)
