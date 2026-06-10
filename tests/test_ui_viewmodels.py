
from dela_furnfact.models import (
    ContentType,
    ManufacturingPlan,
    OpeningPlan,
    OpeningRequest,
    ProjectBundle,
    ShelfPlan,
    ShelfRequest,
)
from dela_furnfact.ui.preview_mapper import PreviewMapper
from dela_furnfact.ui.viewmodels import OpeningTypeViewModel


def test_opening_type_view_model_builds_human_summary() -> None:
    opening = OpeningRequest(
        label="dvd",
        count=6,
        min_clear_height_mm=205,
        preferred_clear_height_mm=205,
        max_clear_height_mm=205,
        fixed_height=True,
    )
    view_model = OpeningTypeViewModel.from_request(opening)
    assert view_model.display_label == "DVD"
    assert view_model.summary == "DVD · 6 huecos · base 205 mm · fijo"


def test_preview_mapper_marks_selected_label() -> None:
    request = ShelfRequest(
        name="DVD demo",
        width_mm=2036,
        height_mm=2000,
        depth_mm=200,
        content_type=ContentType.DVD,
        requested_openings=[
            OpeningRequest("boxset", 2, 235, 255, 320),
            OpeningRequest("dvd", 6, 205, 205, 205, fixed_height=True),
        ],
    )
    plan = ShelfPlan(
        name="DVD demo",
        content_type=ContentType.DVD,
        columns=2,
        rows=3,
        outer_width_mm=2036,
        outer_height_mm=2000,
        outer_depth_mm=200,
        internal_width_mm=1990,
        internal_height_mm=1950,
        clear_section_width_mm=991,
        clear_section_depth_mm=177,
        board_thickness_mm=18,
        back_panel_thickness_mm=5,
        kerf_mm=3,
        estimated_capacity=120,
        openings=(
            OpeningPlan(0, "boxset", 255, 991, 177, 10),
            OpeningPlan(1, "dvd", 205, 991, 177, 50),
            OpeningPlan(2, "boxset", 255, 991, 177, 10),
        ),
        has_back_panel=True,
        split_back_panel=True,
    )
    bundle = ProjectBundle(
        request=request,
        plan=plan,
        manufacturing=ManufacturingPlan(parts=(), board_layouts=(), kerf_mm=3),
    )

    preview = PreviewMapper.from_bundle(bundle, selected_label="dvd")

    assert len(preview.row_items) == 3
    assert preview.row_items[1].highlighted is True
    assert preview.row_items[0].short_label == "BOXSET"
    assert preview.row_items[0].display_label == "BOXSET"
