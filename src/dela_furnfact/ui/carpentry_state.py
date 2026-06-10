from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CarpentryVisibilityState:
    enabled: bool
    reason: str = ""


@dataclass
class CarpentrySettingsState:
    kerf_mm: float = 3.0
    fixed_rows: int | None = None
    fixed_columns: int | None = None
    include_back_panel: bool = True
    include_center_divider: bool = True
    auto_recompute: bool = False
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CarpentrySummaryState:
    parts_count: int = 0
    board_count: int = 0
    estimated_yield_percent: float | None = None
    has_layout: bool = False
