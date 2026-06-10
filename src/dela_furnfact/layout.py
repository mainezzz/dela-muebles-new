"""Layout simple de corte con kerf."""

from __future__ import annotations

from dataclasses import replace
from math import inf

from dela_furnfact.models import BoardLayout, CutPlacement, ManufacturingPart, StockBoard


def stock_board_for_material(material: str, thickness_mm: float, longest_edge_mm: float) -> StockBoard:
    """Crea el tablero base según material.

    Para tablero principal usa 2000x600 por defecto y escala a 2440x600
    cuando alguna pieza supera la longitud nominal.
    """

    upper = material.upper()
    if "MDF" in upper:
        return StockBoard(
            material=material,
            width_mm=1220.0,
            height_mm=2440.0,
            thickness_mm=thickness_mm,
        )

    board_height = 2440.0 if longest_edge_mm > 2000.0 else 2000.0
    return StockBoard(
        material=material,
        width_mm=600.0,
        height_mm=board_height,
        thickness_mm=thickness_mm,
    )


class _BoardState:
    def __init__(self, board: StockBoard, index: int) -> None:
        self.board = board
        self.index = index
        self.cursor_x = 0.0
        self.cursor_y = 0.0
        self.row_height = 0.0
        self.placements: list[CutPlacement] = []

    def to_layout(self) -> BoardLayout:
        return BoardLayout(board=self.board, board_index=self.index, placements=tuple(self.placements))


class SimpleBoardLayouter:
    """Algoritmo estable tipo shelf packing con rotación opcional."""

    def __init__(self, kerf_mm: float = 3.0) -> None:
        self.kerf_mm = kerf_mm

    def layout(self, parts: tuple[ManufacturingPart, ...]) -> tuple[BoardLayout, ...]:
        expanded: list[ManufacturingPart] = []
        for part in parts:
            for index in range(part.quantity):
                expanded.append(
                    replace(
                        part,
                        key=f"{part.key}_{index + 1}",
                        quantity=1,
                    )
                )

        expanded.sort(key=lambda item: item.width_mm * item.height_mm, reverse=True)

        grouped: dict[str, list[ManufacturingPart]] = {}
        for part in expanded:
            grouped.setdefault(part.material, []).append(part)

        layouts: list[BoardLayout] = []
        for material, material_parts in grouped.items():
            longest_edge = max(max(part.width_mm, part.height_mm) for part in material_parts)
            board = stock_board_for_material(material, material_parts[0].thickness_mm, longest_edge)
            states: list[_BoardState] = []

            for part in material_parts:
                placed = False
                for state in states:
                    if self._try_place(state, part):
                        placed = True
                        break

                if not placed:
                    state = _BoardState(board=board, index=len(states) + 1)
                    if not self._try_place(state, part):
                        raise ValueError(
                            f"La pieza {part.key} ({part.width_mm:.1f} x {part.height_mm:.1f}) "
                            f"no cabe en el tablero {material}."
                        )
                    states.append(state)

            layouts.extend(state.to_layout() for state in states)

        return tuple(layouts)

    def _try_place(self, state: _BoardState, part: ManufacturingPart) -> bool:
        orientations = [
            (part.width_mm, part.height_mm, False),
            (part.height_mm, part.width_mm, True),
        ]
        best: tuple[float, float, bool, float, float] | None = None

        for width_mm, height_mm, rotated in orientations:
            if width_mm > state.board.width_mm or height_mm > state.board.height_mm:
                continue

            fit = self._fit_on_board(state=state, width_mm=width_mm, height_mm=height_mm)
            if fit is None:
                continue

            x_mm, y_mm, row_height_after = fit
            waste = (state.board.width_mm - (x_mm + width_mm)) + (state.board.height_mm - (y_mm + row_height_after))
            if best is None or waste < best[0]:
                best = (waste, x_mm, rotated, width_mm, height_mm)

        if best is None:
            return False

        _, x_mm, rotated, width_mm, height_mm = best
        fit = self._fit_on_board(state=state, width_mm=width_mm, height_mm=height_mm)
        if fit is None:
            return False
        x_mm, y_mm, row_height_after = fit

        state.placements.append(
            CutPlacement(
                part_key=part.key,
                label=part.label,
                x_mm=x_mm,
                y_mm=y_mm,
                width_mm=width_mm,
                height_mm=height_mm,
                rotated=rotated,
                board_index=state.index,
            )
        )

        kerf = self.kerf_mm
        if y_mm == state.cursor_y:
            state.cursor_x = x_mm + width_mm + kerf
            state.row_height = max(state.row_height, height_mm)
        else:
            state.cursor_y = y_mm
            state.cursor_x = x_mm + width_mm + kerf
            state.row_height = height_mm

        return True

    def _fit_on_board(self, state: _BoardState, width_mm: float, height_mm: float) -> tuple[float, float, float] | None:
        kerf = self.kerf_mm
        x_mm = state.cursor_x
        y_mm = state.cursor_y

        if x_mm + width_mm <= state.board.width_mm and y_mm + height_mm <= state.board.height_mm:
            return x_mm, y_mm, max(state.row_height, height_mm)

        new_y_mm = y_mm + state.row_height + (kerf if state.placements else 0.0)
        if width_mm <= state.board.width_mm and new_y_mm + height_mm <= state.board.height_mm:
            return 0.0, new_y_mm, height_mm

        return None
