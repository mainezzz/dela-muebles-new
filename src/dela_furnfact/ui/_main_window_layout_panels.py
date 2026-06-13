"""Paneles estructurales de la ventana principal PySide6."""

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

class _MainWindowLayoutPanelsMixin:

    def _build_left_panel(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        shell = QFrame()
        shell.setObjectName("PanelCard")
        shell.setMinimumWidth(220)
        scroll.setWidget(shell)

        layout = QVBoxLayout(shell)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        title = QLabel("Paso 1 · Configura")
        title.setObjectName("SectionTitle")
        hint = QLabel("Empieza por medidas y contenido. Justo debajo define qué tipos de hueco quieres y cuántos.")
        hint.setObjectName("PanelHint")
        hint.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(hint)

        project_card = QFrame()
        project_card.setObjectName("InlineCard")
        project_layout = QFormLayout(project_card)
        project_layout.setContentsMargins(14, 14, 14, 14)
        project_layout.setSpacing(10)
        project_layout.addRow("Ancho (mm)", self.width_input)
        project_layout.addRow("Alto (mm)", self.height_input)
        project_layout.addRow("Fondo (mm)", self.depth_input)
        layout.addWidget(project_card)

        design_card = QFrame()
        design_card.setObjectName("InlineCard")
        design_layout = QFormLayout(design_card)
        design_layout.setContentsMargins(14, 14, 14, 14)
        design_layout.setSpacing(10)
        design_layout.addRow("Contenido", self.content_combo)
        design_layout.addRow("Distribución visual", self.visual_distribution_combo)
        layout.addWidget(design_card)

        layout.addWidget(self._build_openings_panel())

        steps = QFrame()
        steps.setObjectName("InlineCard")
        steps_layout = QVBoxLayout(steps)
        steps_layout.setContentsMargins(14, 12, 14, 12)
        steps_layout.setSpacing(6)
        steps_title = QLabel("Cómo usar")
        steps_title.setObjectName("StepsTitle")
        steps_body = QLabel(
            "1. Ajusta ancho, alto y fondo.\n"
            "2. Elige DVD o Libros.\n"
            "3. Debajo define los tipos de hueco y cuántos quieres.\n"
            "4. Elige una distribución visual sencilla.\n"
            "5. Usa un demo si quieres arrancar con una propuesta ya generada.\n"
            "6. Si cambias algo, pulsa Generar proyecto.\n"
            "7. Cuando la preview te convenza, usa Render visual para sacar PNG."
        )
        steps_body.setObjectName("PanelHint")
        steps_body.setWordWrap(True)
        steps_layout.addWidget(steps_title)
        steps_layout.addWidget(steps_body)
        layout.addWidget(steps)

        layout.addStretch(1)
        return scroll

    def _build_center_panel(self) -> QWidget:
        shell = QFrame()
        shell.setObjectName("PreviewShell")
        shell.setMinimumWidth(340)
        layout = QVBoxLayout(shell)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        top = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Paso 2 · Preview")
        title.setObjectName("SectionTitle")
        subtitle = QLabel("Visual te ayuda a decidir dónde van los tipos de hueco. Técnico sirve para comprobar medidas y proporciones.")
        subtitle.setObjectName("PanelHint")
        subtitle.setWordWrap(True)
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        top.addLayout(title_box, 1)

        mode_box = QHBoxLayout()
        mode_box.setSpacing(6)
        mode_box.addWidget(self.visual_mode_button)
        mode_box.addWidget(self.technical_mode_button)
        top.addLayout(mode_box)
        layout.addLayout(top)
        layout.addWidget(self.inline_alert)

        preview_frame = QFrame()
        preview_frame.setObjectName("PreviewInner")
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(10, 10, 10, 10)
        preview_layout.addWidget(self.preview_widget, 1)
        layout.addWidget(preview_frame, 1)

        metrics = QFrame()
        metrics.setObjectName("MetricsStrip")
        metrics_layout = QGridLayout(metrics)
        metrics_layout.setContentsMargins(10, 10, 10, 10)
        metrics_layout.setHorizontalSpacing(10)
        metrics_layout.setVerticalSpacing(10)

        cards = [
            self.metric_columns_rows,
            self.metric_section_width,
            self.metric_row_height,
            self.metric_capacity,
        ]
        for index, card in enumerate(cards):
            metrics_layout.addWidget(card, 0, index)
        layout.addWidget(metrics)

        return shell

    def _build_right_panel(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        shell = QWidget()
        shell.setMinimumWidth(220)
        scroll.setWidget(shell)

        layout = QVBoxLayout(shell)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        layout.addWidget(self._build_actions_panel())
        layout.addWidget(self._build_blender_panel())
        layout.addWidget(self._build_carpentry_panel())
        layout.addStretch(1)
        return scroll

    def _build_actions_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("PanelCard")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Paso 3 · Genera y renderiza")
        title.setObjectName("SectionTitle")
        subtitle = QLabel(
            "Usa esta columna solo para generar, renderizar y abrir el módulo de carpintería cuando la propuesta ya esté clara."
        )
        subtitle.setObjectName("PanelHint")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        self.project_state_chip = QLabel("Sin generar")
        self.project_state_chip.setObjectName("ChipLabel")
        layout.addWidget(self.project_state_chip, 0, Qt.AlignmentFlag.AlignLeft)

        small = QLabel("Los demos ya vienen generados.")
        small.setObjectName("PanelHint")
        layout.addWidget(small)
        return panel
