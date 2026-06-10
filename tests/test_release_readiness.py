from dela_furnfact.paths import docs_root


def test_release_docs_exist() -> None:
    docs = docs_root()
    assert (docs / "FINAL_STABILIZATION_CHECKLIST.md").exists()
    assert (docs / "RELEASE_READINESS.md").exists()
    assert (docs / "ARCHITECTURE_CONSOLIDATION.md").exists()