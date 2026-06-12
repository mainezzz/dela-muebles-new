from __future__ import annotations
from dataclasses import dataclass
from math import floor
from dela_furnfact.models import (
    LayoutCandidate,
    LayoutMode,
    OpeningPlan,
    OpeningRequest,
    RemainingDistribution,
    ShelfPlan,
    ShelfRequest,
    VisualDistribution,
)
from dela_furnfact.profiles import candidate_columns, candidate_rows, default_auto_opening, expanded_openings, get_profile

class _SolverScoringMixin:

    def _score_candidate(
        self,
        request: ShelfRequest,
        columns: int,
        rows: int,
        section_width_mm: float,
        heights_mm: list[float],
        estimated_capacity: int,
        requested_count: int,
        base_items: list[OpeningRequest],
    ) -> float:
        profile = get_profile(request.content_type)

        score = 0.0
        score += estimated_capacity * 0.15

        if request.content_quantity > 0:
            coverage = min(estimated_capacity / request.content_quantity, 1.25)
            score += coverage * 150.0

        if columns in profile.preferred_columns:
            score += 40.0

        if rows in profile.preferred_rows:
            score += 35.0

        if request.fixed_columns is not None and columns == request.fixed_columns:
            score += 50.0

        if request.fixed_rows is not None and rows == request.fixed_rows:
            score += 50.0

        width_penalty = max(section_width_mm - profile.max_section_width_mm, 0.0) * 0.12
        score -= width_penalty

        if heights_mm:
            mean_height = sum(heights_mm) / len(heights_mm)
            variation = sum(abs(value - mean_height) for value in heights_mm) / len(heights_mm)
            if request.layout_mode is LayoutMode.BALANCED:
                score -= variation * 0.12
            elif request.layout_mode is LayoutMode.DENSE:
                score -= variation * 0.04

        auto_rows = rows - requested_count
        if auto_rows >= 0:
            score -= auto_rows * 2.5

        if request.layout_mode is LayoutMode.DENSE:
            score += rows * 6.0
        elif request.layout_mode is LayoutMode.BALANCED:
            score += columns * 3.0

        score -= self._priority_mismatch_penalty(base_items, heights_mm)
        return score

    def _priority_mismatch_penalty(self, base_items: list[OpeningRequest], heights_mm: list[float]) -> float:
        penalty = 0.0
        for item, actual_height in zip(base_items, heights_mm, strict=True):
            preferred = item.target_height_mm
            if actual_height >= preferred:
                continue
            gap = preferred - actual_height
            importance = max(6 - item.priority, 1)
            penalty += gap * importance * 0.35
            if item.fixed_height and abs(actual_height - preferred) > 0.01:
                penalty += 500.0
        return penalty

    def _build_failure_message(
        self,
        request: ShelfRequest,
        rejections: list[CandidateRejection],
    ) -> str:
        if not rejections:
            return "No se pudo generar ninguna distribución válida."

        ranked = sorted(rejections, key=lambda item: (item.rows, item.columns, item.code))
        best = ranked[0]
        return (
            "No se pudo generar ninguna distribución válida. "
            f"Mejor intento ({best.columns} columnas x {best.rows} filas): {best.message}"
        )
