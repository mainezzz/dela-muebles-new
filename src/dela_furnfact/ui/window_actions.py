from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WindowActionState:
    generate_text: str
    status_text: str
    carpentry_visible: bool


class WindowActionsController:
    def build(self, *, generated: bool) -> WindowActionState:
        if generated:
            return WindowActionState(
                generate_text="Regenerar proyecto",
                status_text="Proyecto generado",
                carpentry_visible=True,
            )
        return WindowActionState(
            generate_text="Generar proyecto",
            status_text="Sin generar",
            carpentry_visible=False,
        )
