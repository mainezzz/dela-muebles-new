from dela_furnfact.models import ContentType, VisualDistribution
from dela_furnfact.ui.controllers import ProjectController
from dela_furnfact.ui.state import ProjectFormState, status_for_generation


def test_project_form_state_builds_request() -> None:
    state = ProjectFormState.from_values(
        content_type=ContentType.DVD,
        overall_width_mm=2036,
        overall_height_mm=2000,
        overall_depth_mm=200,
        board_thickness_mm=18,
        visual_distribution=VisualDistribution.TOP_BOTTOM_LARGE,
        opening_quantities={"dvd": 6, "boxset": 2},
    )
    request = state.to_request()
    assert request.content_type is ContentType.DVD
    assert len(request.requested_openings) == 2
    assert request.requested_openings[0].label in {"dvd", "boxset"}


def test_status_changes_button_text() -> None:
    assert status_for_generation(False).button_text == "Generar proyecto"
    assert status_for_generation(True).button_text == "Regenerar proyecto"


def test_controller_returns_dvd_demo_payload() -> None:
    controller = ProjectController()
    payload = controller.dvd_demo()
    assert payload.content_type is ContentType.DVD
    assert payload.opening_quantities["dvd"] == 6
    assert payload.opening_quantities["boxset"] == 2
