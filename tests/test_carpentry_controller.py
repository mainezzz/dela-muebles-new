from dataclasses import dataclass

from dela_furnfact.ui.carpentry_controller import CarpentryController
from dela_furnfact.ui.carpentry_state import CarpentrySettingsState


@dataclass
class FakeBoard:
    usage_percent: float | None = None


@dataclass
class FakeManufacturing:
    parts: list[object]
    board_layouts: list[FakeBoard]


@dataclass
class FakeBundle:
    manufacturing: FakeManufacturing | None = None


def test_visibility_requires_bundle() -> None:
    controller = CarpentryController()
    state = controller.visibility_for_bundle(None)
    assert state.enabled is False
    assert "Genera" in state.reason


def test_summary_reads_parts_and_boards() -> None:
    controller = CarpentryController()
    bundle = FakeBundle(
        manufacturing=FakeManufacturing(
            parts=[object(), object(), object()],
            board_layouts=[FakeBoard(70.0), FakeBoard(80.0)],
        )
    )
    summary = controller.summary_for_bundle(bundle)
    assert summary.parts_count == 3
    assert summary.board_count == 2
    assert summary.has_layout is True
    assert summary.estimated_yield_percent == 75.0


def test_normalize_settings_clamps_values() -> None:
    controller = CarpentryController()
    normalized = controller.normalize_settings(
        CarpentrySettingsState(
            kerf_mm=25.0,
            fixed_rows=-1,
            fixed_columns=0,
        )
    )
    assert normalized.kerf_mm == 10.0
    assert normalized.fixed_rows is None
    assert normalized.fixed_columns is None
