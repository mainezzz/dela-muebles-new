"""Modelos de dominio del configurador."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from math import floor
from typing import Iterable


class ContentType(StrEnum):
    """Tipos de contenido soportados."""

    BOOKS = "books"
    DVD = "dvd"


class LayoutMode(StrEnum):
    """Estrategias generales del solver."""

    AUTO = "auto"
    BALANCED = "balanced"
    DENSE = "dense"


class RemainingDistribution(StrEnum):
    """Cómo repartir altura sobrante entre huecos."""

    AUTO = "auto"
    UNIFORM = "uniform"
    TOP_BOTTOM_LARGE = "top_bottom_large"
    LARGEST_OPENINGS = "largest_openings"
    NONE = "none"


class VisualDistribution(StrEnum):
    """Preferencia visual de colocación de tipos de hueco."""

    AUTO = "auto"
    MIXED = "mixed"
    TOP_BOTTOM_LARGE = "top_bottom_large"
    CENTER_LARGE = "center_large"
    COMPACT = "compact"


@dataclass(frozen=True)
class OpeningRequest:
    """Hueco pedido por el usuario."""

    label: str
    count: int
    min_clear_height_mm: float
    preferred_clear_height_mm: float | None = None
    max_clear_height_mm: float | None = None
    min_clear_width_mm: float = 0.0
    priority: int = 3
    fixed_height: bool = False

    def expanded(self) -> list["OpeningRequest"]:
        """Expande una petición repetida en peticiones unitarias."""

        return [
            OpeningRequest(
                label=self.label,
                count=1,
                min_clear_height_mm=self.min_clear_height_mm,
                preferred_clear_height_mm=self.preferred_clear_height_mm,
                max_clear_height_mm=self.max_clear_height_mm,
                min_clear_width_mm=self.min_clear_width_mm,
                priority=self.priority,
                fixed_height=self.fixed_height,
            )
            for _ in range(self.count)
        ]

    @property
    def target_height_mm(self) -> float:
        """Altura objetivo del hueco."""

        return self.preferred_clear_height_mm or self.min_clear_height_mm

    @property
    def effective_max_clear_height_mm(self) -> float | None:
        """Límite superior efectivo del hueco."""

        if self.fixed_height:
            return self.target_height_mm
        return self.max_clear_height_mm


@dataclass(frozen=True)
class ShelfRequest:
    """Entrada única del motor."""

    name: str
    width_mm: float
    height_mm: float
    depth_mm: float
    board_thickness_mm: float = 18.0
    back_panel_thickness_mm: float = 5.0
    content_type: ContentType = ContentType.BOOKS
    content_quantity: int = 0
    layout_mode: LayoutMode = LayoutMode.AUTO
    remaining_distribution: RemainingDistribution = RemainingDistribution.AUTO
    visual_distribution: VisualDistribution = VisualDistribution.AUTO
    has_back_panel: bool = True
    split_back_panel: bool = True
    has_center_divider: bool = True
    kerf_mm: float = 3.0
    units: str = "mm"
    fixed_columns: int | None = None
    fixed_rows: int | None = None
    allow_auto_fill: bool = True
    requested_openings: list[OpeningRequest] = field(default_factory=list)


@dataclass(frozen=True)
class ValidationIssue:
    """Resultado de validación."""

    code: str
    message: str
    level: str = "error"


@dataclass(frozen=True)
class StorageProfile:
    """Parámetros por tipo de contenido."""

    content_type: ContentType
    label: str
    min_clear_height_mm: float
    ideal_clear_height_mm: float
    min_depth_mm: float
    ideal_depth_mm: float
    width_per_item_mm: float
    preferred_columns: tuple[int, ...]
    preferred_rows: tuple[int, ...]
    max_section_width_mm: float
    default_opening_label: str


@dataclass(frozen=True)
class OpeningPlan:
    """Hueco ya resuelto por el solver."""

    index: int
    label: str
    clear_height_mm: float
    clear_width_mm: float
    clear_depth_mm: float
    estimated_capacity: int
    source: str = "auto"


@dataclass(frozen=True)
class LayoutCandidate:
    """Candidato abstracto del solver."""

    columns: int
    rows: int
    opening_heights_mm: tuple[float, ...]
    section_width_mm: float
    estimated_capacity: int
    score: float
    opening_labels: tuple[str, ...]
    opening_sources: tuple[str, ...]
    distribution: RemainingDistribution
    visual_distribution: VisualDistribution = VisualDistribution.AUTO


@dataclass(frozen=True)
class ShelfPlan:
    """Solución final elegida."""

    name: str
    content_type: ContentType
    columns: int
    rows: int
    outer_width_mm: float
    outer_height_mm: float
    outer_depth_mm: float
    internal_width_mm: float
    internal_height_mm: float
    clear_section_width_mm: float
    clear_section_depth_mm: float
    board_thickness_mm: float
    back_panel_thickness_mm: float
    kerf_mm: float
    estimated_capacity: int
    openings: tuple[OpeningPlan, ...]
    has_back_panel: bool
    split_back_panel: bool
    warnings: tuple[str, ...] = field(default_factory=tuple)
    visual_distribution: VisualDistribution = VisualDistribution.AUTO

    @property
    def clear_row_height_mm(self) -> float:
        """Altura útil media."""

        if not self.openings:
            return 0.0
        return sum(opening.clear_height_mm for opening in self.openings) / len(self.openings)

    @property
    def divider_count(self) -> int:
        """Número de divisores verticales."""

        return max(self.columns - 1, 0)

    @property
    def horizontal_shelf_count(self) -> int:
        """Número de baldas interiores."""

        return max(self.rows - 1, 0) * self.columns


@dataclass(frozen=True)
class ManufacturingPart:
    """Pieza agrupada de fabricación."""

    key: str
    label: str
    width_mm: float
    height_mm: float
    thickness_mm: float
    quantity: int
    material: str
    semantic: str

    @property
    def area_mm2(self) -> float:
        """Área total agregada."""

        return self.width_mm * self.height_mm * self.quantity


@dataclass(frozen=True)
class CutPlacement:
    """Colocación de una pieza en un tablero."""

    part_key: str
    label: str
    x_mm: float
    y_mm: float
    width_mm: float
    height_mm: float
    rotated: bool
    board_index: int


@dataclass(frozen=True)
class StockBoard:
    """Tablero base."""

    material: str
    width_mm: float
    height_mm: float
    thickness_mm: float

    @property
    def area_mm2(self) -> float:
        return self.width_mm * self.height_mm


@dataclass(frozen=True)
class BoardLayout:
    """Layout de corte para un tablero concreto."""

    board: StockBoard
    board_index: int
    placements: tuple[CutPlacement, ...] = field(default_factory=tuple)

    @property
    def used_area_mm2(self) -> float:
        return sum(item.width_mm * item.height_mm for item in self.placements)

    @property
    def utilization_ratio(self) -> float:
        if self.board.area_mm2 == 0:
            return 0.0
        return self.used_area_mm2 / self.board.area_mm2


@dataclass(frozen=True)
class ManufacturingPlan:
    """Resultado completo de fabricación."""

    parts: tuple[ManufacturingPart, ...]
    board_layouts: tuple[BoardLayout, ...]
    kerf_mm: float

    def total_part_count(self) -> int:
        return sum(part.quantity for part in self.parts)

    def find_parts(self, semantic: str) -> list[ManufacturingPart]:
        return [part for part in self.parts if part.semantic == semantic]


@dataclass(frozen=True)
class ProjectBundle:
    """Bundle completo listo para exportar."""

    request: ShelfRequest
    plan: ShelfPlan
    manufacturing: ManufacturingPlan

    def summary_lines(self) -> list[str]:
        lines = [
            f"Proyecto: {self.request.name}",
            f"Contenido: {self.request.content_type.value}",
            f"Columnas x filas: {self.plan.columns} x {self.plan.rows}",
            f"Ancho útil por sección: {self.plan.clear_section_width_mm:.1f} mm",
            f"Altura útil media: {self.plan.clear_row_height_mm:.1f} mm",
            f"Capacidad estimada: {self.plan.estimated_capacity}",
            f"Piezas: {self.manufacturing.total_part_count()}",
            f"Tableros: {len(self.manufacturing.board_layouts)}",
        ]
        if self.plan.warnings:
            lines.append("Warnings:")
            lines.extend(f"- {warning}" for warning in self.plan.warnings)
        return lines
