"""Launchers de GUI."""

from __future__ import annotations


def launch_gui() -> None:
    """Lanza la interfaz PySide6."""

    try:
        from dela_furnfact.ui.pyside_app import launch_gui as launch_pyside_gui
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith("PySide6"):
            raise RuntimeError(
                "PySide6 no está instalado. Instala las dependencias de escritorio con: "
                "pip install -e .[desktop]"
            ) from exc
        raise

    launch_pyside_gui()


if __name__ == "__main__":
    launch_gui()
