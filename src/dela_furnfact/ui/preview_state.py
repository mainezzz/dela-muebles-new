from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PreviewUiMode(str, Enum):
    VISUAL = "visual"
    TECHNICAL = "technical"


@dataclass(frozen=True)
class PreviewBadge:
    text: str
    visible: bool = True


@dataclass(frozen=True)
class PreviewRowState:
    opening_type_id: str
    preview_label: str
    technical_label: str
    clear_height_mm: int
    quantity: int
    visual_badge: PreviewBadge
    show_visual_badge: bool
    show_technical_label: bool
    show_technical_height: bool


@dataclass(frozen=True)
class PreviewPanelState:
    mode: PreviewUiMode
    rows: tuple[PreviewRowState, ...]
    columns: int
    empty_message: str = ""

    @property
    def is_empty(self) -> bool:
        return not self.rows
