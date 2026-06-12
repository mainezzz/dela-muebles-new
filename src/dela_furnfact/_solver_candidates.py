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

from dela_furnfact._solver_common import CandidateRejection

class _SolverCandidatesMixin:

    def _generate_candidates(self, request: ShelfRequest) -> tuple[list[LayoutCandidate], list[CandidateRejection]]:
        profile = get_profile(request.content_type)
        candidates: list[LayoutCandidate] = []
        rejections: list[CandidateRejection] = []

        for columns in candidate_columns(request):
            for rows in candidate_rows(request):
                candidate, rejection = self._build_candidate(request=request, columns=columns, rows=rows)
                if rejection is not None:
                    rejections.append(rejection)
                    continue
                if candidate is None:
                    continue
                if candidate.section_width_mm <= 0:
                    continue

                section_capacity = max(floor(candidate.section_width_mm / profile.width_per_item_mm), 1)
                if section_capacity * columns <= 0:
                    continue

                candidates.append(candidate)

        return candidates, rejections

    def _build_candidate(
        self,
        request: ShelfRequest,
        columns: int,
        rows: int,
    ) -> tuple[LayoutCandidate | None, CandidateRejection | None]:
        profile = get_profile(request.content_type)
        requested = expanded_openings(request)

        if rows < len(requested):
            return None, CandidateRejection(
                code="SOL_001",
                message="Las filas del candidato no alcanzan el número de huecos requeridos.",
                columns=columns,
                rows=rows,
            )

        divider_count = max(columns - 1, 0)
        usable_width_mm = request.width_mm - (2 * request.board_thickness_mm) - divider_count * request.board_thickness_mm
        if usable_width_mm <= 0:
            return None, CandidateRejection(
                code="SOL_002",
                message="El ancho interior útil es insuficiente para cualquier sección.",
                columns=columns,
                rows=rows,
            )

        section_width_mm = usable_width_mm / columns
        if any(item.min_clear_width_mm > section_width_mm for item in requested):
            widest = max(item.min_clear_width_mm for item in requested)
            return None, CandidateRejection(
                code="SOL_003",
                message=(
                    f"Algún hueco requiere {widest:.1f} mm de anchura útil, "
                    f"pero la sección solo ofrece {section_width_mm:.1f} mm."
                ),
                columns=columns,
                rows=rows,
            )

        internal_height_mm = request.height_mm - (2 * request.board_thickness_mm)
        usable_height_mm = internal_height_mm - max(rows - 1, 0) * request.board_thickness_mm
        if usable_height_mm <= 0:
            return None, CandidateRejection(
                code="SOL_004",
                message="La altura interior útil es insuficiente para este número de filas.",
                columns=columns,
                rows=rows,
            )

        auto_fill_count = rows - len(requested)
        if auto_fill_count < 0:
            return None, CandidateRejection(
                code="SOL_005",
                message="El candidato no tiene filas suficientes para los huecos pedidos.",
                columns=columns,
                rows=rows,
            )
        if auto_fill_count > 0 and not request.allow_auto_fill:
            return None, CandidateRejection(
                code="SOL_006",
                message="Este candidato necesita auto-fill y el request lo prohíbe.",
                columns=columns,
                rows=rows,
            )

        base_items = list(requested)
        source_items = ["requested"] * len(requested)
        for _ in range(auto_fill_count):
            base_items.append(default_auto_opening(profile))
            source_items.append("auto")

        visual_distribution = self._effective_visual_distribution(request)
        base_items, source_items = self._arrange_items(
            base_items=base_items,
            source_items=source_items,
            visual_distribution=visual_distribution,
        )

        heights_mm, resolution_note = self._resolve_heights(
            request=request,
            rows=rows,
            usable_height_mm=usable_height_mm,
            base_items=base_items,
        )

        if heights_mm is None:
            return None, CandidateRejection(
                code="SOL_007",
                message=resolution_note or "No se pudieron resolver las alturas para este candidato.",
                columns=columns,
                rows=rows,
            )

        section_capacity = max(floor(section_width_mm / profile.width_per_item_mm), 1)
        estimated_capacity = section_capacity * columns * rows
        score = self._score_candidate(
            request=request,
            columns=columns,
            rows=rows,
            section_width_mm=section_width_mm,
            heights_mm=heights_mm,
            estimated_capacity=estimated_capacity,
            requested_count=len(requested),
            base_items=base_items,
        )

        labels = [item.label for item in base_items]

        return (
            LayoutCandidate(
                columns=columns,
                rows=rows,
                opening_heights_mm=tuple(heights_mm),
                section_width_mm=section_width_mm,
                estimated_capacity=estimated_capacity,
                score=score,
                opening_labels=tuple(labels),
                opening_sources=tuple(source_items),
                distribution=self._effective_distribution(request),
                visual_distribution=visual_distribution,
            ),
            None,
        )
