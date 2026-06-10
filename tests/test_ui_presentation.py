
from dela_furnfact.models import OpeningRequest
from dela_furnfact.ui.presentation import display_opening_label, opening_kind, summarize_opening_mix


def test_display_opening_label_short_and_long() -> None:
    assert display_opening_label("dvd") == "DVD"
    assert display_opening_label("novela_pequeña") == "NOVELA PEQUEÑA"
    assert display_opening_label("novela_grande", short=True) == "GRANDES"


def test_opening_kind_classifies_known_types() -> None:
    assert opening_kind("dvd") == "dvd"
    assert opening_kind("boxset") == "boxset"
    assert opening_kind("novela_grande") == "large_book"


def test_summarize_opening_mix_aggregates_counts() -> None:
    openings = [
        OpeningRequest(label="dvd", count=6, min_clear_height_mm=205, preferred_clear_height_mm=205, fixed_height=True),
        OpeningRequest(label="boxset", count=2, min_clear_height_mm=235, preferred_clear_height_mm=255),
    ]
    assert summarize_opening_mix(openings) == "6 DVD · 2 BOXSET"
