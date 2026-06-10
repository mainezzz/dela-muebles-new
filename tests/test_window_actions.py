from dela_furnfact.ui.window_actions import WindowActionState, WindowActionsController


def test_window_action_state_defaults() -> None:
    state = WindowActionState(
        generate_text="Generar proyecto",
        status_text="Sin generar",
        carpentry_visible=False,
    )
    assert state.generate_text == "Generar proyecto"
    assert state.status_text == "Sin generar"
    assert state.carpentry_visible is False


def test_window_actions_controller_changes_state_when_generated() -> None:
    controller = WindowActionsController()
    state = controller.build(generated=True)
    assert state.generate_text == "Regenerar proyecto"
    assert state.carpentry_visible is True
