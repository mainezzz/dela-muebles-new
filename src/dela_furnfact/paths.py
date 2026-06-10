"""Rutas de proyecto para ejecución normal o empaquetada."""

from __future__ import annotations

from pathlib import Path
import sys


def runtime_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent / "resources"


def schemas_root() -> Path:
    return runtime_root() / "schemas"


def examples_root() -> Path:
    return runtime_root() / "examples"


def assets_root() -> Path:
    return runtime_root() / "assets"


def docs_root() -> Path:
    return runtime_root() / "docs"


def legacy_root() -> Path:
    return runtime_root() / "legacy"


def user_data_root() -> Path:
    path = Path.home() / ".dela-furnfact"
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_render_output_root() -> Path:
    path = user_data_root() / "renders"
    path.mkdir(parents=True, exist_ok=True)
    return path


def schema_path(filename: str = "shelf_request.schema.json") -> Path:
    return schemas_root() / filename