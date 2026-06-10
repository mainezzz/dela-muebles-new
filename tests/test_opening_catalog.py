from dela_furnfact.models import ContentType
from dela_furnfact.opening_catalog import (
    OpeningTypeId,
    canonical_opening_label,
    get_opening_type_spec,
    opening_request_from_type,
    opening_type_choices,
)
from dela_furnfact.validation import parse_request_dict


def test_catalog_resolves_aliases() -> None:
    spec = get_opening_type_spec("Novela grande")
    assert spec is not None
    assert spec.id is OpeningTypeId.BOOK_LARGE
    assert canonical_opening_label("dvd_boxsets") == "boxset"


def test_catalog_builds_default_opening_request() -> None:
    opening = opening_request_from_type(OpeningTypeId.DVD, count=6)
    assert opening.label == "dvd"
    assert opening.count == 6
    assert opening.fixed_height is True
    assert opening.min_clear_height_mm == 205


def test_content_choices_are_ordered() -> None:
    dvd_choices = opening_type_choices(ContentType.DVD)
    assert [item.id for item in dvd_choices] == [OpeningTypeId.DVD, OpeningTypeId.BOXSET]
    book_choices = opening_type_choices(ContentType.BOOKS)
    assert [item.id for item in book_choices] == [OpeningTypeId.BOOK_SMALL, OpeningTypeId.BOOK_LARGE]


def test_parse_request_normalizes_labels_to_catalog() -> None:
    request = parse_request_dict(
        {
            "name": "Demo",
            "width_mm": 1600,
            "height_mm": 2000,
            "depth_mm": 300,
            "requested_openings": [
                {"label": "DVD normales", "count": 6, "min_clear_height_mm": 205},
                {"label": "Novela grande", "count": 2, "min_clear_height_mm": 249},
            ],
        }
    )
    assert request.requested_openings[0].label == "dvd"
    assert request.requested_openings[1].label == "books_large"
