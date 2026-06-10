from dela_furnfact.models import ContentType, OpeningPlan, ShelfPlan, VisualDistribution
from dela_furnfact.ui.preview_mapper import map_plan_to_preview


def test_preview_mapper_exposes_preview_labels() -> None:
    plan = ShelfPlan(
        name="demo",
        content_type=ContentType.DVD,
        columns=2,
        rows=2,
        outer_width_mm=2036,
        outer_height_mm=2000,
        outer_depth_mm=200,
        internal_width_mm=1960,
        internal_height_mm=1900,
        clear_section_width_mm=980,
        clear_section_depth_mm=180,
        board_thickness_mm=18,
        back_panel_thickness_mm=5,
        kerf_mm=3,
        estimated_capacity=8,
        openings=(
            OpeningPlan(index=0, label="dvd", clear_height_mm=205, clear_width_mm=980, clear_depth_mm=180, estimated_capacity=6),
            OpeningPlan(index=1, label="boxset", clear_height_mm=255, clear_width_mm=980, clear_depth_mm=180, estimated_capacity=2),
        ),
        has_back_panel=True,
        split_back_panel=True,
        visual_distribution=VisualDistribution.TOP_BOTTOM_LARGE,
    )
    vm = map_plan_to_preview(plan)
    assert [row.short_label for row in vm.row_items] == ["DVD", "BOXSET"]
