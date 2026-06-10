from dela_furnfact.models import OpeningPlan, ShelfPlan, ContentType, VisualDistribution
from dela_furnfact.ui.preview_controller import PreviewController
from dela_furnfact.ui.preview_mapper import map_plan_to_preview
from dela_furnfact.ui.preview_state import PreviewUiMode


def _plan(label: str, h: int) -> ShelfPlan:
    return ShelfPlan(
        name="demo",
        content_type=ContentType.DVD,
        columns=2,
        rows=1,
        outer_width_mm=1000,
        outer_height_mm=2000,
        outer_depth_mm=200,
        internal_width_mm=900,
        internal_height_mm=1900,
        clear_section_width_mm=450,
        clear_section_depth_mm=180,
        board_thickness_mm=18,
        back_panel_thickness_mm=5,
        kerf_mm=3,
        estimated_capacity=1,
        openings=(OpeningPlan(index=0, label=label, clear_height_mm=h, clear_width_mm=450, clear_depth_mm=180, estimated_capacity=1),),
        has_back_panel=True,
        split_back_panel=True,
        visual_distribution=VisualDistribution.MIXED,
    )


def test_empty_visual_state_has_message() -> None:
    state = PreviewController().empty_state(mode=PreviewUiMode.VISUAL)
    assert state.is_empty is True
    assert "Genera" in state.empty_message


def test_visual_mode_shows_badges() -> None:
    vm = map_plan_to_preview(_plan("dvd", 205))
    state = PreviewController().from_view_model(vm, mode=PreviewUiMode.VISUAL)
    assert state.rows[0].show_visual_badge is True
    assert state.rows[0].show_technical_label is False


def test_technical_mode_hides_badges() -> None:
    vm = map_plan_to_preview(_plan("boxset", 255))
    state = PreviewController().from_view_model(vm, mode=PreviewUiMode.TECHNICAL)
    assert state.rows[0].show_visual_badge is False
    assert state.rows[0].show_technical_label is True
