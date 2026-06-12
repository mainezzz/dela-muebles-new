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

class _SolverDistributionMixin:

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
