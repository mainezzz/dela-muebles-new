"""Bloques de cabecera de la ventana principal PySide6."""

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
from dela_furnfact.ui._pyside_preview import InlineAlertCard, MetricCard, ShelfPreviewWidget
from dela_furnfact.ui._pyside_styles import app_stylesheet
from dela_furnfact.ui._pyside_worker import RenderWorker

class _MainWindowHeaderMixin:

    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("HeaderFrame")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(18)

        logo_label = QLabel()
        logo_label.setMinimumSize(420, 112)
        logo_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        logo_path = assets_root() / "branding" / "dela_logo.png"
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            logo_label.setPixmap(
                pixmap.scaled(
                    520,
                    128,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            logo_label.setText("DELA")
            logo_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            logo_label.setObjectName("BrandTitle")
        layout.addWidget(logo_label, 1, Qt.AlignmentFlag.AlignVCenter)

        title_box = QVBoxLayout()
        product = QLabel("Furniture Factory")
        product.setObjectName("BrandTitle")
        product.setStyleSheet("font-size: 24px;")
        caption = QLabel("Los demos ya vienen generados. Si cambias medidas o huecos, usa Regenerar proyecto y luego Render visual cuando quieras sacar PNG.")
        caption.setObjectName("BrandSubtitle")
        caption.setWordWrap(True)
        title_box.addWidget(product)
        title_box.addWidget(caption)
        layout.addLayout(title_box, 0)

        action_box = QHBoxLayout()
        action_box.setSpacing(8)

        self.new_button = QPushButton("Nuevo")
        self.new_button.clicked.connect(self.new_project)
        demo_books_button = QPushButton("Demo libros 4-4")
        demo_books_button.clicked.connect(self._seed_demo_books)
        demo_books53_button = QPushButton("Demo libros 5-3")
        demo_books53_button.clicked.connect(self._seed_demo_books_5_3)
        demo_dvd_button = QPushButton("Demo DVD")
        demo_dvd_button.clicked.connect(self._seed_demo_dvd)
        self.load_button = QPushButton("Abrir")
        self.load_button.clicked.connect(self.load_request_file)
        self.save_button = QPushButton("Guardar")
        self.save_button.clicked.connect(self.save_request_file)
        self.generate_button = QPushButton("Generar proyecto")
        self.generate_button.setObjectName("PrimaryButton")
        self.generate_button.clicked.connect(self.generate_bundle)

        for button in (
            self.new_button,
            demo_books_button,
            demo_books53_button,
            demo_dvd_button,
            self.load_button,
            self.save_button,
            self.theme_button,
            self.generate_button,
        ):
            action_box.addWidget(button)

        layout.addLayout(action_box)
        return header
