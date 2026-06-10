from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class MainApplicationFlow:
    bindings: Any
    coordinator: Any
    project_controller: Any
    render_controller: Any

    def apply_empty(self, form_state: Any) -> None:
        self.coordinator.apply_empty_state(form_state=form_state)

    def generate_from_form(self, form_state: Any):
        bundle = self.project_controller.generate(form_state)
        self.coordinator.apply_generated_state(bundle=bundle, form_state=form_state)
        return bundle
