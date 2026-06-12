"""Solver paramétrico de estanterías."""

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


@dataclass(frozen=True)
class CandidateRejection:
    """Motivo de descarte de un candidato del solver."""

    code: str
    message: str
    columns: int
    rows: int


class ShelfPlanner:
    """Calcula la mejor configuración geométrica para un request."""

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

    def _effective_distribution(self, request: ShelfRequest) -> RemainingDistribution:
        if request.remaining_distribution is not RemainingDistribution.AUTO:
            return request.remaining_distribution
        if request.layout_mode is LayoutMode.DENSE:
            return RemainingDistribution.TOP_BOTTOM_LARGE
        return RemainingDistribution.UNIFORM

    def _effective_visual_distribution(self, request: ShelfRequest) -> VisualDistribution:
        if request.visual_distribution is not VisualDistribution.AUTO:
            return request.visual_distribution

        effective_distribution = self._effective_distribution(request)
        if effective_distribution is RemainingDistribution.TOP_BOTTOM_LARGE:
            return VisualDistribution.TOP_BOTTOM_LARGE
        if effective_distribution is RemainingDistribution.LARGEST_OPENINGS:
            return VisualDistribution.CENTER_LARGE
        if request.layout_mode is LayoutMode.DENSE:
            return VisualDistribution.COMPACT
        return VisualDistribution.MIXED

    def _arrange_items(
        self,
        *,
        base_items: list[OpeningRequest],
        source_items: list[str],
        visual_distribution: VisualDistribution,
    ) -> tuple[list[OpeningRequest], list[str]]:
        if len(base_items) <= 1:
            return base_items, source_items

        indexed = list(enumerate(zip(base_items, source_items, strict=True)))
        if visual_distribution is VisualDistribution.MIXED:
            return base_items, source_items

        ranked = sorted(
            indexed,
            key=lambda item: (
                -(item[1][0].target_height_mm),
                item[1][0].priority,
                item[0],
            ),
        )

        if visual_distribution is VisualDistribution.TOP_BOTTOM_LARGE:
            positions = self._edge_positions(len(base_items))
        elif visual_distribution is VisualDistribution.CENTER_LARGE:
            positions = self._center_positions(len(base_items))
        elif visual_distribution is VisualDistribution.COMPACT:
            positions = list(range(len(base_items)))
        else:
            return base_items, source_items

        arranged_items: list[OpeningRequest | None] = [None] * len(base_items)
        arranged_sources: list[str | None] = [None] * len(base_items)

        for target_index, (_, (opening, source)) in zip(positions, ranked, strict=True):
            arranged_items[target_index] = opening
            arranged_sources[target_index] = source

        return (
            [item for item in arranged_items if item is not None],
            [item for item in arranged_sources if item is not None],
        )

    def _edge_positions(self, size: int) -> list[int]:
        positions: list[int] = []
        left = 0
        right = size - 1
        while left <= right:
            positions.append(left)
            if right != left:
                positions.append(right)
            left += 1
            right -= 1
        return positions

    def _center_positions(self, size: int) -> list[int]:
        if size <= 1:
            return [0]

        if size % 2 == 0:
            left = (size // 2) - 1
            right = size // 2
            positions = [left, right]
            offset = 1
            while left - offset >= 0 or right + offset < size:
                if left - offset >= 0:
                    positions.append(left - offset)
                if right + offset < size:
                    positions.append(right + offset)
                offset += 1
            return positions

        center = size // 2
        positions = [center]
        offset = 1
        while center - offset >= 0 or center + offset < size:
            if center - offset >= 0:
                positions.append(center - offset)
            if center + offset < size:
                positions.append(center + offset)
            offset += 1
        return positions

    def _resolve_heights(
        self,
        request: ShelfRequest,
        rows: int,
        usable_height_mm: float,
        base_items: list[OpeningRequest],
    ) -> tuple[list[float] | None, str | None]:
        if len(base_items) != rows:
            return None, "El número de huecos no coincide con el número de filas."

        min_heights = [item.min_clear_height_mm for item in base_items]
        heights = [self._bounded_target_height(item) for item in base_items]
        minimum_total = sum(min_heights)

        if minimum_total > usable_height_mm:
            return (
                None,
                (
                    f"Las alturas mínimas exigen {minimum_total:.1f} mm "
                    f"y solo hay {usable_height_mm:.1f} mm útiles."
                ),
            )

        fixed_total = sum(height for item, height in zip(base_items, heights, strict=True) if item.fixed_height)
        if fixed_total > usable_height_mm:
            return (
                None,
                (
                    f"Las alturas fijas exigen {fixed_total:.1f} mm "
                    f"y solo hay {usable_height_mm:.1f} mm útiles."
                ),
            )

        total = sum(heights)
        if total > usable_height_mm:
            deficit = total - usable_height_mm
            deficit, reductions = self._reduce_heights_by_priority(base_items, heights, deficit)
            if deficit > 0.01:
                flexible_at_min = sum(1 for item, current, minimum in zip(base_items, heights, min_heights, strict=True) if not item.fixed_height and abs(current - minimum) < 0.01)
                return (
                    None,
                    (
                        f"Faltan {deficit:.1f} mm incluso reduciendo huecos flexibles; "
                        f"{flexible_at_min} huecos ya han llegado a su mínimo."
                    ),
                )

        total = sum(heights)
        remaining = usable_height_mm - total
        distribution = self._effective_distribution(request)

        if remaining > 0.01 and distribution is not RemainingDistribution.NONE:
            self._increase_heights(base_items, heights, remaining, distribution)

        return heights, None

    def _bounded_target_height(self, item: OpeningRequest) -> float:
        target = item.target_height_mm
        if item.effective_max_clear_height_mm is not None:
            target = min(target, item.effective_max_clear_height_mm)
        return max(target, item.min_clear_height_mm)

    def _reduce_heights_by_priority(
        self,
        base_items: list[OpeningRequest],
        heights: list[float],
        deficit: float,
    ) -> tuple[float, list[float]]:
        priorities = sorted(set(item.priority for item in base_items), reverse=True)
        for priority in priorities:
            indices = [
                index
                for index, item in enumerate(base_items)
                if item.priority == priority and not item.fixed_height
            ]
            shrinkable = sum(heights[index] - base_items[index].min_clear_height_mm for index in indices)
            if shrinkable <= 0:
                continue
            take = min(shrinkable, deficit)
            if take <= 0:
                continue
            weights = [heights[index] - base_items[index].min_clear_height_mm for index in indices]
            total_weight = sum(weights)
            if total_weight <= 0:
                continue
            for index, weight in zip(indices, weights, strict=True):
                ratio = weight / total_weight
                delta = take * ratio
                floor_height = base_items[index].min_clear_height_mm
                heights[index] = max(floor_height, heights[index] - delta)
            deficit -= take
            if deficit <= 0.01:
                return 0.0, heights
        return deficit, heights

    def _increase_heights(
        self,
        base_items: list[OpeningRequest],
        heights: list[float],
        remaining: float,
        distribution: RemainingDistribution,
    ) -> None:
        capacity = [
            float("inf") if item.effective_max_clear_height_mm is None else max(item.effective_max_clear_height_mm - height, 0.0)
            for item, height in zip(base_items, heights, strict=True)
        ]
        eligible = [index for index, room in enumerate(capacity) if room > 0.01 or room == float("inf")]
        if not eligible:
            return

        if distribution is RemainingDistribution.UNIFORM:
            self._distribute_weighted(heights, capacity, eligible, remaining, [1.0] * len(eligible))
            return

        if distribution is RemainingDistribution.TOP_BOTTOM_LARGE:
            if len(heights) == 1:
                self._distribute_weighted(heights, capacity, [0], remaining, [1.0])
                return
            indices = sorted({0, len(heights) - 1})
            consumed = self._distribute_weighted(heights, capacity, indices, remaining, [1.0] * len(indices))
            leftover = max(remaining - consumed, 0.0)
            if leftover > 0.01:
                middle = [index for index in eligible if index not in indices]
                if middle:
                    self._distribute_weighted(heights, capacity, middle, leftover, [1.0] * len(middle))
            return

        if distribution is RemainingDistribution.LARGEST_OPENINGS:
            max_value = max(heights)
            indices = [index for index, value in enumerate(heights) if abs(value - max_value) < 0.01]
            self._distribute_weighted(heights, capacity, indices, remaining, [1.0] * len(indices))
            return

        self._distribute_weighted(heights, capacity, [0], remaining, [1.0])

    def _distribute_weighted(
        self,
        heights: list[float],
        capacity: list[float],
        indices: list[int],
        remaining: float,
        weights: list[float],
    ) -> float:
        active = list(indices)
        weight_map = {index: weight for index, weight in zip(indices, weights, strict=True)}
        total_consumed = 0.0
        while remaining > 0.01 and active:
            total_weight = sum(weight_map[index] for index in active)
            if total_weight <= 0:
                break

            consumed = 0.0
            for index in list(active):
                share = remaining * (weight_map[index] / total_weight)
                room = capacity[index]
                delta = share if room == float("inf") else min(share, room)
                if delta <= 0:
                    active.remove(index)
                    continue
                heights[index] += delta
                consumed += delta
                total_consumed += delta
                if room != float("inf"):
                    capacity[index] = max(room - delta, 0.0)
                    if capacity[index] <= 0.01:
                        active.remove(index)
            if consumed <= 0.01:
                break
            remaining -= consumed
        return total_consumed


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
