from dela_furnfact.paths import assets_root, docs_root, legacy_root, schema_path


def test_schema_exists() -> None:
    assert schema_path().exists()


def test_docs_root_exists() -> None:
    assert docs_root().exists()


def test_logo_exists() -> None:
    assert (assets_root() / "branding" / "dela_logo.png").exists()


def test_legacy_root_exists() -> None:
    assert legacy_root().exists()