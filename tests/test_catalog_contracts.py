from dela_furnfact.catalog import get_opening_type


def test_catalog_has_expected_fixed_dvd_height() -> None:
    dvd = get_opening_type("dvd")
    assert dvd.preferred_height_mm == 205
    assert dvd.fixed_height is True


def test_books_preview_labels_are_plural() -> None:
    assert get_opening_type("books_small").preview_label == "PEQUEÑOS"
    assert get_opening_type("books_large").preview_label == "GRANDES"
