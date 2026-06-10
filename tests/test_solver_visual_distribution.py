from dela_furnfact.application import FurnFactApplicationService
from dela_furnfact.models import (
    ContentType,
    OpeningRequest,
    ShelfRequest,
    VisualDistribution,
)
from dela_furnfact.validation import parse_request_dict


def test_visual_distribution_top_bottom_places_tall_openings_at_edges() -> None:
    request = ShelfRequest(
        name="DVD edge placement",
        width_mm=2036.0,
        height_mm=2000.0,
        depth_mm=200.0,
        content_type=ContentType.DVD,
        fixed_columns=2,
        fixed_rows=8,
        visual_distribution=VisualDistribution.TOP_BOTTOM_LARGE,
        requested_openings=[
            OpeningRequest(label="BOXSET", count=2, min_clear_height_mm=235.0, preferred_clear_height_mm=255.0),
            OpeningRequest(label="DVD", count=6, min_clear_height_mm=205.0, preferred_clear_height_mm=205.0, fixed_height=True),
        ],
    )

    bundle = FurnFactApplicationService().generate(request)

    labels = [opening.label.upper() for opening in bundle.plan.openings]
    assert labels[0] == "BOXSET"
    assert labels[-1] == "BOXSET"
    assert labels.count("BOXSET") == 2


def test_visual_distribution_center_places_tall_openings_near_middle() -> None:
    request = ShelfRequest(
        name="Books center placement",
        width_mm=1636.0,
        height_mm=2000.0,
        depth_mm=300.0,
        content_type=ContentType.BOOKS,
        fixed_columns=2,
        fixed_rows=6,
        visual_distribution=VisualDistribution.CENTER_LARGE,
        requested_openings=[
            OpeningRequest(label="Novela grande", count=2, min_clear_height_mm=249.0, preferred_clear_height_mm=256.0),
            OpeningRequest(label="Novela pequeña", count=4, min_clear_height_mm=210.0, preferred_clear_height_mm=214.0),
        ],
    )

    bundle = FurnFactApplicationService().generate(request)

    labels = [opening.label.lower() for opening in bundle.plan.openings]
    assert labels[2] == "novela grande"
    assert labels[3] == "novela grande"


def test_parse_request_accepts_visual_distribution() -> None:
    request = parse_request_dict(
        {
            "name": "JSON distribution",
            "width_mm": 1600,
            "height_mm": 2000,
            "depth_mm": 300,
            "content_type": "books",
            "visual_distribution": "center_large",
            "requested_openings": [
                {
                    "label": "novela",
                    "count": 2,
                    "min_clear_height_mm": 210,
                }
            ],
        }
    )

    assert request.visual_distribution is VisualDistribution.CENTER_LARGE
