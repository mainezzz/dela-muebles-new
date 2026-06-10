from __future__ import annotations

from dataclasses import dataclass

from dela_furnfact.ui.app_flow import MainApplicationFlow


@dataclass
class DummyPlan:
    rows: list
    columns: int = 2


@dataclass
class DummyBundle:
    plan: DummyPlan


class DummyCoordinator:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def apply_empty_state(self, **kwargs) -> None:
        self.calls.append("empty")

    def apply_generated_state(self, **kwargs) -> None:
        self.calls.append("generated")


class DummyProjectController:
    def __init__(self) -> None:
        self.generated = DummyBundle(plan=DummyPlan(rows=[]))

    def generate(self, form_state):
        return self.generated


class DummyRenderController:
    pass


def test_flow_generate_applies_generated_state():
    flow = MainApplicationFlow(
        bindings=None,
        coordinator=DummyCoordinator(),
        project_controller=DummyProjectController(),
        render_controller=DummyRenderController(),
    )

    bundle = flow.generate_from_form(form_state=object())
    assert bundle.plan.columns == 2
    assert flow.coordinator.calls == ["generated"]


def test_flow_apply_empty_delegates():
    flow = MainApplicationFlow(
        bindings=None,
        coordinator=DummyCoordinator(),
        project_controller=DummyProjectController(),
        render_controller=DummyRenderController(),
    )

    class FormState:
        content_type = "dvd"

    flow.apply_empty(FormState())
    assert flow.coordinator.calls == ["empty"]
