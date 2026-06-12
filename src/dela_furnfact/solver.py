from __future__ import annotations
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

from dela_furnfact._solver_candidates import _SolverCandidatesMixin

from dela_furnfact._solver_common import CandidateRejection

from dela_furnfact._solver_distribution import _SolverDistributionMixin

from dela_furnfact._solver_scoring import _SolverScoringMixin

class ShelfPlanner(_SolverCandidatesMixin, _SolverDistributionMixin, _SolverScoringMixin):

    def solve(self, request: ShelfRequest) -> ShelfPlan:
        profile = get_profile(request.content_type)
        candidates, rejections = self._generate_candidates(request)
        if not candidates:
            raise ValueError(self._build_failure_message(request, rejections))

        best = max(candidates, key=lambda item: item.score)

        clear_depth_mm = request.depth_mm - (request.back_panel_thickness_mm if request.has_back_panel else 0.0)
        openings = tuple(
            OpeningPlan(
                index=index + 1,
                label=best.opening_labels[index],
                clear_height_mm=height,
                clear_width_mm=best.section_width_mm,
                clear_depth_mm=clear_depth_mm,
                estimated_capacity=max(floor(best.section_width_mm / profile.width_per_item_mm), 1) * best.columns,
                source=best.opening_sources[index],
            )
            for index, height in enumerate(best.opening_heights_mm)
        )

        warnings: list[str] = []
        if request.depth_mm < profile.ideal_depth_mm:
            warnings.append("El fondo está por debajo del ideal del perfil seleccionado.")

        if best.section_width_mm > profile.max_section_width_mm:
            warnings.append(
                "La luz horizontal es alta para el contenido y puede requerir un tablero más rígido."
            )

        if best.estimated_capacity < request.content_quantity:
            warnings.append(
                "La capacidad estimada queda por debajo de la cantidad solicitada."
            )

        if any(item.fixed_height for item in expanded_openings(request)):
            warnings.append(
                "El solver ha respetado huecos fijos; esto puede limitar alternativas de distribución."
            )

        usable_internal_width_mm = request.width_mm - (2 * request.board_thickness_mm)
        internal_height_mm = request.height_mm - (2 * request.board_thickness_mm)

        return ShelfPlan(
            name=request.name,
            content_type=request.content_type,
            columns=best.columns,
            rows=best.rows,
            outer_width_mm=request.width_mm,
            outer_height_mm=request.height_mm,
            outer_depth_mm=request.depth_mm,
            internal_width_mm=usable_internal_width_mm,
            internal_height_mm=internal_height_mm,
            clear_section_width_mm=best.section_width_mm,
            clear_section_depth_mm=clear_depth_mm,
            board_thickness_mm=request.board_thickness_mm,
            back_panel_thickness_mm=request.back_panel_thickness_mm,
            kerf_mm=request.kerf_mm,
            estimated_capacity=best.estimated_capacity,
            openings=openings,
            has_back_panel=request.has_back_panel,
            split_back_panel=request.split_back_panel,
            warnings=tuple(warnings),
            visual_distribution=self._effective_visual_distribution(request),
        )

__all__ = ["CandidateRejection", "ShelfPlanner"]
