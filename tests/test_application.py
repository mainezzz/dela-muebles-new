from pathlib import Path
import json

import pytest

from dela_furnfact.application import FurnFactApplicationService
from dela_furnfact.cli import main as cli_main
from dela_furnfact.blender_adapter import (
    BlenderExecutableLocator,
    LegacyBlenderBridge,
    LegacyCompatibilityError,
)
from dela_furnfact.models import ContentType, LayoutMode, OpeningRequest, RemainingDistribution, ShelfRequest
from dela_furnfact.validation import RequestValidationError, load_request


def test_books_pipeline_generates_bundle() -> None:
    request = ShelfRequest(
        name="Biblioteca",
        width_mm=1636.0,
        height_mm=2000.0,
        depth_mm=300.0,
        content_type=ContentType.BOOKS,
        content_quantity=220,
        layout_mode=LayoutMode.BALANCED,
        remaining_distribution=RemainingDistribution.UNIFORM,
        fixed_columns=2,
        requested_openings=[
            OpeningRequest(label="books_large", count=1, min_clear_height_mm=249.0, preferred_clear_height_mm=249.0),
            OpeningRequest(label="books_small", count=2, min_clear_height_mm=210.0, preferred_clear_height_mm=210.0),
            OpeningRequest(label="books_large", count=2, min_clear_height_mm=249.0, preferred_clear_height_mm=249.0),
            OpeningRequest(label="books_small", count=2, min_clear_height_mm=211.0, preferred_clear_height_mm=211.0),
            OpeningRequest(label="books_large", count=1, min_clear_height_mm=249.0, preferred_clear_height_mm=249.0),
        ],
    )

    bundle = FurnFactApplicationService().generate(request)

    assert bundle.plan.columns == 2
    assert bundle.plan.rows == 8
    assert bundle.plan.clear_row_height_mm >= 210
    assert bundle.manufacturing.total_part_count() > 0
    assert bundle.manufacturing.find_parts("side")
    assert bundle.manufacturing.board_layouts


def test_dvd_pipeline_generates_dense_solution() -> None:
    request = ShelfRequest(
        name="DVD",
        width_mm=2036.0,
        height_mm=2000.0,
        depth_mm=200.0,
        content_type=ContentType.DVD,
        content_quantity=400,
        layout_mode=LayoutMode.DENSE,
        remaining_distribution=RemainingDistribution.TOP_BOTTOM_LARGE,
        fixed_columns=2,
        requested_openings=[
            OpeningRequest(label="dvd_boxsets", count=1, min_clear_height_mm=255.0, preferred_clear_height_mm=255.0),
            OpeningRequest(label="dvds", count=6, min_clear_height_mm=205.0, preferred_clear_height_mm=205.0),
            OpeningRequest(label="dvd_boxsets", count=1, min_clear_height_mm=255.0, preferred_clear_height_mm=255.0),
        ],
    )

    bundle = FurnFactApplicationService().generate(request)

    assert bundle.plan.rows == 8
    assert bundle.plan.estimated_capacity >= 400
    assert bundle.manufacturing.find_parts("back")


def test_custom_openings_are_respected() -> None:
    request = ShelfRequest(
        name="Custom",
        width_mm=1800.0,
        height_mm=2200.0,
        depth_mm=320.0,
        content_type=ContentType.BOOKS,
        content_quantity=260,
        layout_mode=LayoutMode.BALANCED,
        remaining_distribution=RemainingDistribution.UNIFORM,
        requested_openings=[
            OpeningRequest(label="atlas", count=2, min_clear_height_mm=360.0, preferred_clear_height_mm=380.0),
            OpeningRequest(label="novela", count=4, min_clear_height_mm=230.0, preferred_clear_height_mm=240.0),
        ],
    )

    bundle = FurnFactApplicationService().generate(request)

    assert bundle.plan.rows >= 3
    heights = [opening.clear_height_mm for opening in bundle.plan.openings]
    assert max(heights) >= 360.0


def test_invalid_request_raises() -> None:
    request = ShelfRequest(
        name="Inválido",
        width_mm=0.0,
        height_mm=1000.0,
        depth_mm=200.0,
    )

    with pytest.raises(RequestValidationError):
        FurnFactApplicationService().generate(request)


def test_load_request_from_json(tmp_path: Path) -> None:
    payload = {
        "name": "Desde JSON",
        "width_mm": 1600,
        "height_mm": 2000,
        "depth_mm": 300,
        "content_type": "books",
        "requested_openings": [{"label": "libros", "count": 2, "min_clear_height_mm": 220}],
    }
    path = tmp_path / "request.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    request = load_request(path)

    assert request.name == "Desde JSON"
    assert request.requested_openings[0].label == "libros"


def test_blender_locator_accepts_explicit_path(tmp_path: Path) -> None:
    fake_blender = tmp_path / "blender.exe"
    fake_blender.write_text("", encoding="utf-8")

    found = BlenderExecutableLocator.find(fake_blender)

    assert found == fake_blender.resolve()


def test_blender_bridge_exports_payloads() -> None:
    request = ShelfRequest(
        name="Bridge",
        width_mm=1600.0,
        height_mm=2000.0,
        depth_mm=300.0,
        content_type=ContentType.BOOKS,
        fixed_columns=2,
        requested_openings=[OpeningRequest(label="books", count=4, min_clear_height_mm=230.0)],
    )
    bundle = FurnFactApplicationService().generate(request)
    bridge = LegacyBlenderBridge(blender_executable=None)

    visual_payload = bridge.builder.build_visual_spec(bundle)
    manufacturing_payload = bridge.builder.build_manufacturing_payload(bundle)

    assert visual_payload["type"] == "bookshelf"
    assert "boards" in manufacturing_payload
    assert visual_payload["legacy_compatibility"]["supported"] is True
    assert manufacturing_payload["legacy_compatibility"]["supported"] is True


def test_visual_payload_maps_custom_labels_to_legacy_types() -> None:
    request = ShelfRequest(
        name="Custom Visual",
        width_mm=1636.0,
        height_mm=2100.0,
        depth_mm=320.0,
        content_type=ContentType.BOOKS,
        fixed_columns=2,
        requested_openings=[
            OpeningRequest(label="atlas", count=1, min_clear_height_mm=360.0, preferred_clear_height_mm=380.0),
            OpeningRequest(label="novela", count=2, min_clear_height_mm=220.0, preferred_clear_height_mm=230.0),
        ],
    )
    bundle = FurnFactApplicationService().generate(request)
    payload = LegacyBlenderBridge().builder.build_visual_spec(bundle)

    zone_types = {zone["type"] for zone in payload["zones"]}
    original_labels = {zone["original_label"] for zone in payload["zones"]}

    assert zone_types <= {"books_small", "books_large", "books_standard", "books_general"}
    assert "atlas" in original_labels
    assert "novela" in original_labels


def test_legacy_manufacturing_rejects_non_compatible_topology(tmp_path: Path) -> None:
    request = ShelfRequest(
        name="Tres columnas",
        width_mm=2400.0,
        height_mm=2000.0,
        depth_mm=300.0,
        content_type=ContentType.BOOKS,
        fixed_columns=3,
        requested_openings=[OpeningRequest(label="books_large", count=4, min_clear_height_mm=240.0)],
    )
    bundle = FurnFactApplicationService().generate(request)
    bridge = LegacyBlenderBridge(blender_executable=None)

    report = bridge.manufacturing_compatibility(bundle)

    assert report.is_supported is False
    assert any(issue.code == "MFG_001" for issue in report.issues)

    with pytest.raises(LegacyCompatibilityError):
        bridge.render_manufacturing(bundle, tmp_path / "manufacturing")


def test_fixed_height_opening_is_respected() -> None:
    request = ShelfRequest(
        name="Hueco fijo",
        width_mm=1800.0,
        height_mm=2200.0,
        depth_mm=320.0,
        content_type=ContentType.BOOKS,
        layout_mode=LayoutMode.BALANCED,
        remaining_distribution=RemainingDistribution.UNIFORM,
        requested_openings=[
            OpeningRequest(
                label="arte_grande",
                count=1,
                min_clear_height_mm=360.0,
                preferred_clear_height_mm=390.0,
                max_clear_height_mm=390.0,
                priority=1,
                fixed_height=True,
            ),
            OpeningRequest(
                label="novela",
                count=4,
                min_clear_height_mm=230.0,
                preferred_clear_height_mm=255.0,
                max_clear_height_mm=270.0,
                priority=4,
            ),
        ],
    )

    bundle = FurnFactApplicationService().generate(request)

    fixed = next(opening for opening in bundle.plan.openings if opening.label == "arte_grande")
    assert abs(fixed.clear_height_mm - 390.0) < 0.01


def test_solver_reduces_low_priority_openings_first() -> None:
    request = ShelfRequest(
        name="Prioridades",
        width_mm=1600.0,
        height_mm=1350.0,
        depth_mm=300.0,
        content_type=ContentType.BOOKS,
        fixed_columns=2,
        fixed_rows=4,
        allow_auto_fill=False,
        requested_openings=[
            OpeningRequest(
                label="referencia",
                count=1,
                min_clear_height_mm=320.0,
                preferred_clear_height_mm=360.0,
                priority=1,
            ),
            OpeningRequest(
                label="album",
                count=1,
                min_clear_height_mm=320.0,
                preferred_clear_height_mm=360.0,
                priority=2,
            ),
            OpeningRequest(
                label="novela",
                count=2,
                min_clear_height_mm=220.0,
                preferred_clear_height_mm=280.0,
                priority=5,
            ),
        ],
    )

    bundle = FurnFactApplicationService().generate(request)
    heights_by_label = {}
    for opening in bundle.plan.openings:
        heights_by_label.setdefault(opening.label, []).append(opening.clear_height_mm)

    assert min(heights_by_label["referencia"]) >= 340.0
    assert min(heights_by_label["album"]) >= 330.0
    assert max(heights_by_label["novela"]) < 280.0


def test_load_request_supports_fixed_and_max_height(tmp_path: Path) -> None:
    payload = {
        "name": "Con restricciones",
        "width_mm": 1700,
        "height_mm": 2100,
        "depth_mm": 300,
        "content_type": "books",
        "requested_openings": [
            {
                "label": "atlas",
                "count": 1,
                "min_clear_height_mm": 340,
                "preferred_clear_height_mm": 380,
                "max_clear_height_mm": 380,
                "fixed_height": True,
                "priority": 1,
            }
        ],
    }
    path = tmp_path / "request_fixed.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    request = load_request(path)

    assert request.requested_openings[0].fixed_height is True
    assert request.requested_openings[0].max_clear_height_mm == 380.0

def test_cli_template_writes_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    output = tmp_path / "template.json"

    exit_code = cli_main(["template", "--output", str(output)])

    assert exit_code == 0
    assert output.exists()
    assert '"requested_openings"' in output.read_text(encoding="utf-8")


def test_cli_docs_prints_docs_root(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli_main(["docs"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Docs root:" in captured.out
    assert "REQUEST_FORMAT.md" in captured.out


def test_cli_version(capsys) -> None:
    exit_code = cli_main(["version"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip()


def test_cli_doctor(capsys) -> None:
    exit_code = cli_main(["doctor"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Runtime root:" in captured.out
