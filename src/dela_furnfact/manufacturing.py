"""Convierte un ShelfPlan en piezas de fabricación."""

from __future__ import annotations

from dela_furnfact.models import ManufacturingPart, ShelfPlan


def _main_material(thickness_mm: float) -> str:
    return f"PINE 2000x600x{thickness_mm:g}"


def _back_material(thickness_mm: float) -> str:
    return f"MDF 2440x1220x{thickness_mm:g}"


class ManufacturingGenerator:
    """Generador de piezas agrupadas."""

    def build_parts(self, plan: ShelfPlan) -> tuple[ManufacturingPart, ...]:
        main_material = _main_material(plan.board_thickness_mm)
        parts: list[ManufacturingPart] = []

        parts.append(
            ManufacturingPart(
                key="side_panel",
                label="Lateral",
                width_mm=plan.outer_depth_mm,
                height_mm=plan.outer_height_mm,
                thickness_mm=plan.board_thickness_mm,
                quantity=2,
                material=main_material,
                semantic="side",
            )
        )

        internal_span_width_mm = plan.outer_width_mm - (2 * plan.board_thickness_mm)

        parts.append(
            ManufacturingPart(
                key="top_panel",
                label="Tapa superior",
                width_mm=internal_span_width_mm,
                height_mm=plan.outer_depth_mm,
                thickness_mm=plan.board_thickness_mm,
                quantity=1,
                material=main_material,
                semantic="top_bottom",
            )
        )

        parts.append(
            ManufacturingPart(
                key="bottom_panel",
                label="Base inferior",
                width_mm=internal_span_width_mm,
                height_mm=plan.outer_depth_mm,
                thickness_mm=plan.board_thickness_mm,
                quantity=1,
                material=main_material,
                semantic="top_bottom",
            )
        )

        divider_quantity = max(plan.columns - 1, 0)
        if divider_quantity > 0:
            parts.append(
                ManufacturingPart(
                    key="vertical_divider",
                    label="Divisor vertical",
                    width_mm=plan.outer_depth_mm,
                    height_mm=plan.outer_height_mm - (2 * plan.board_thickness_mm),
                    thickness_mm=plan.board_thickness_mm,
                    quantity=divider_quantity,
                    material=main_material,
                    semantic="divider",
                )
            )

        shelf_quantity = max(plan.rows - 1, 0) * plan.columns
        if shelf_quantity > 0:
            parts.append(
                ManufacturingPart(
                    key="internal_shelf",
                    label="Balda interior",
                    width_mm=plan.clear_section_width_mm,
                    height_mm=plan.outer_depth_mm,
                    thickness_mm=plan.board_thickness_mm,
                    quantity=shelf_quantity,
                    material=main_material,
                    semantic="shelf",
                )
            )

        if plan.has_back_panel and plan.back_panel_thickness_mm > 0:
            back_material = _back_material(plan.back_panel_thickness_mm)
            back_quantity = 2 if plan.split_back_panel else 1
            back_width_mm = plan.outer_width_mm / back_quantity
            parts.append(
                ManufacturingPart(
                    key="back_panel",
                    label="Trasera",
                    width_mm=back_width_mm,
                    height_mm=plan.outer_height_mm,
                    thickness_mm=plan.back_panel_thickness_mm,
                    quantity=back_quantity,
                    material=back_material,
                    semantic="back",
                )
            )

        return tuple(parts)
