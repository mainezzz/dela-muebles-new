
"""View models ligeros para la GUI de DELA.

Fase 1 de v13:
- separan la representación de la GUI del modelo de dominio
- evitan que la ventana principal y la preview interpreten directamente
  el dominio en varios puntos distintos
"""

from __future__ import annotations

from dataclasses import dataclass

from dela_furnfact.models import OpeningPlan, OpeningRequest
from dela_furnfact.ui.presentation import display_opening_label, opening_kind


@dataclass(frozen=True)
class OpeningTypeViewModel:
    """Representación de un tipo de hueco para listas y paneles."""

    source_label: str
    display_label: str
    short_label: str
    kind: str
    count: int
    min_clear_height_mm: float
    preferred_clear_height_mm: float | None
    max_clear_height_mm: float | None
    fixed_height: bool
    summary: str

    @classmethod
    def from_request(cls, opening: OpeningRequest) -> "OpeningTypeViewModel":
        display_label = display_opening_label(opening.label)
        short_label = display_opening_label(opening.label, short=True)
        kind = opening_kind(opening.label)

        summary = (
            f"{display_label} · {opening.count} huecos · "
            f"base {opening.min_clear_height_mm:.0f} mm"
        )
        if (
            opening.preferred_clear_height_mm is not None
            and abs(opening.preferred_clear_height_mm - opening.min_clear_height_mm) > 0.1
        ):
            summary += f" · ideal {opening.preferred_clear_height_mm:.0f}"
        if (
            opening.max_clear_height_mm is not None
            and (
                opening.preferred_clear_height_mm is None
                or abs(opening.max_clear_height_mm - opening.preferred_clear_height_mm) > 0.1
            )
        ):
            summary += f" · hasta {opening.max_clear_height_mm:.0f}"
        if opening.fixed_height:
            summary += " · fijo"

        return cls(
            source_label=opening.label,
            display_label=display_label,
            short_label=short_label,
            kind=kind,
            count=opening.count,
            min_clear_height_mm=opening.min_clear_height_mm,
            preferred_clear_height_mm=opening.preferred_clear_height_mm,
            max_clear_height_mm=opening.max_clear_height_mm,
            fixed_height=opening.fixed_height,
            summary=summary,
        )


@dataclass(frozen=True)
class PreviewRowViewModel:
    """Fila dibujable en la preview."""

    index: int
    source_label: str
    display_label: str
    short_label: str
    kind: str
    clear_height_mm: float
    clear_width_mm: float
    highlighted: bool = False

    @classmethod
    def from_plan(
        cls,
        index: int,
        opening: OpeningPlan,
        *,
        highlighted: bool = False,
    ) -> "PreviewRowViewModel":
        return cls(
            index=index,
            source_label=opening.label,
            display_label=display_opening_label(opening.label),
            short_label=display_opening_label(opening.label, short=True),
            kind=opening_kind(opening.label),
            clear_height_mm=opening.clear_height_mm,
            clear_width_mm=opening.clear_width_mm,
            highlighted=highlighted,
        )


@dataclass(frozen=True)
class PreviewViewModel:
    """Estructura mínima que necesita el widget de preview."""

    columns: int
    rows: int
    outer_width_mm: float
    outer_height_mm: float
    board_thickness_mm: float
    row_items: tuple[PreviewRowViewModel, ...]
