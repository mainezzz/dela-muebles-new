"""Workers auxiliares de la GUI PySide6."""

from __future__ import annotations
from dataclasses import asdict
import json
from pathlib import Path
from typing import Iterable
from PySide6.QtCore import QObject, QSettings, QSize, Qt, QThread, QUrl, Signal, QRect
from PySide6.QtGui import (
    QAction,
    QColor,
    QDesktopServices,
    QFont,
    QFontMetrics,
    QLinearGradient,
    QPainter,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QAbstractSpinBox,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QPushButton,
    QPlainTextEdit,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from dela_furnfact.application import FurnFactApplicationService
from dela_furnfact.blender_adapter import (
    BlenderExecutableLocator,
    BlenderNotFoundError,
    LegacyBlenderBridge,
    LegacyCompatibilityReport,
    LegacyRenderBatch,
    LegacyRenderResult,
    flatten_generated_files,
)
from dela_furnfact.exporters import JsonExporter
from dela_furnfact.help_text import APP_HELP_TEXT, request_template_text
from dela_furnfact.opening_catalog import (
    OpeningTypeId,
    opening_request_from_type,
    opening_type_choices,
)
from dela_furnfact.models import (
    ContentType,
    LayoutMode,
    OpeningRequest,
    ProjectBundle,
    RemainingDistribution,
    ShelfRequest,
)
from dela_furnfact.paths import assets_root, default_render_output_root, docs_root, user_data_root
from dela_furnfact.ui.presentation import display_opening_label, opening_kind, summarize_opening_mix
from dela_furnfact.ui.preview_mapper import PreviewMapper
from dela_furnfact.ui.viewmodels import OpeningTypeViewModel
from dela_furnfact.validation import RequestValidationError, load_request, parse_request_dict

class RenderWorker(QObject):
    """Ejecuta Blender en un hilo aparte."""

    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, bundle: ProjectBundle, blender_path: str, output_dir: str, mode: str, include_content: bool = True) -> None:
        super().__init__()
        self.bundle = bundle
        self.blender_path = blender_path
        self.output_dir = Path(output_dir)
        self.mode = mode
        self.include_content = include_content

    def run(self) -> None:
        try:
            bridge = LegacyBlenderBridge(blender_executable=Path(self.blender_path) if self.blender_path else None)
            if self.mode == "visual":
                result = bridge.render_visual(self.bundle, self.output_dir / "visual", include_content=self.include_content)
            elif self.mode == "manufacturing":
                result = bridge.render_manufacturing(self.bundle, self.output_dir / "manufacturing")
            else:
                result = bridge.render_all(self.bundle, self.output_dir, include_content=self.include_content)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))
            return
        self.finished.emit(result)

__all__ = ["RenderWorker"]
