"""Paneles de dominio de la ventana principal PySide6."""

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

class _MainWindowDomainPanelsMixin:

    def _build_openings_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("PanelCard")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Tipos de hueco")
        title.setObjectName("SectionTitle")
        subtitle = QLabel(
            "Elige qué tipos de hueco necesitas y cuántos. "
            "DVD siempre mide 205 mm. BOXSET puede variar. "
            "En libros usamos Novela pequeña y Novela grande como base editable."
        )
        subtitle.setObjectName("PanelHint")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        presets = QFrame()
        presets.setObjectName("InlineCard")
        presets_layout = QVBoxLayout(presets)
        presets_layout.setContentsMargins(12, 10, 12, 10)
        presets_layout.setSpacing(8)
        presets_title = QLabel("Tipos rápidos")
        presets_title.setObjectName("StepsTitle")
        presets_help = QLabel(
            "Empieza con tipos típicos y luego cambia solo lo necesario. "
            "La cantidad por tipo es lo más importante."
        )
        presets_help.setObjectName("PanelHint")
        presets_help.setWordWrap(True)
        presets_layout.addWidget(presets_title)
        presets_layout.addWidget(presets_help)
        presets_buttons = QHBoxLayout()
        self.quick_button_a = QPushButton("DVD")
        self.quick_button_b = QPushButton("BOXSET")
        self.quick_button_a.clicked.connect(self.add_primary_preset_opening)
        self.quick_button_b.clicked.connect(self.add_secondary_preset_opening)
        presets_buttons.addWidget(self.quick_button_a)
        presets_buttons.addWidget(self.quick_button_b)
        presets_layout.addLayout(presets_buttons)
        layout.addWidget(presets)

        action_row = QHBoxLayout()
        add_button = QPushButton("Añadir")
        add_button.clicked.connect(self.add_opening)
        duplicate_button = QPushButton("Duplicar")
        duplicate_button.clicked.connect(self.duplicate_opening)
        remove_button = QPushButton("Eliminar")
        remove_button.clicked.connect(self.remove_opening)
        action_row.addWidget(add_button)
        action_row.addWidget(duplicate_button)
        action_row.addWidget(remove_button)
        layout.addLayout(action_row)

        self.openings_list.setMinimumHeight(170)
        layout.addWidget(self.openings_list)

        editor = QFrame()
        editor.setObjectName("InlineCard")
        editor_layout = QVBoxLayout(editor)
        editor_layout.setContentsMargins(12, 12, 12, 12)
        editor_layout.setSpacing(10)

        editor_layout.addWidget(QLabel("Editor del tipo seleccionado"))
        editor_layout.addWidget(self.opening_summary_label)

        form = QFormLayout()
        form.setSpacing(8)
        form.addRow("Tipo", self.opening_label_input)
        form.addRow("Cantidad", self.opening_count_input)
        form.addRow("Hueco base", self.opening_min_height_input)
        form.addRow("Hueco ideal", self.opening_pref_height_input)
        form.addRow("Puede crecer hasta", self.opening_max_height_input)
        editor_layout.addLayout(form)

        editor_buttons = QHBoxLayout()
        apply_button = QPushButton("Aplicar cambios")
        apply_button.setObjectName("PrimaryButton")
        apply_button.clicked.connect(self.apply_opening_changes)
        clear_button = QPushButton("Nuevo tipo limpio")
        clear_button.clicked.connect(self.reset_opening_editor)
        editor_buttons.addWidget(apply_button)
        editor_buttons.addWidget(clear_button)
        editor_layout.addLayout(editor_buttons)

        layout.addWidget(editor)
        return panel

    def _build_blender_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("PanelCard")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Render final · Blender")
        title.setObjectName("SectionTitle")
        subtitle = QLabel("Usa esta zona cuando ya hayas generado una propuesta. Puedes sacar el mueble limpio o incluir libros/DVD en el visual.")
        subtitle.setObjectName("PanelHint")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        chips = QHBoxLayout()
        chips.addWidget(self.blender_state_chip)
        chips.addWidget(self.legacy_state_chip)
        chips.addStretch(1)
        layout.addLayout(chips)

        path_form = QFormLayout()
        path_form.addRow("Ruta Blender", self.blender_path_input)
        path_form.addRow("Salida render", self.render_output_input)
        layout.addLayout(path_form)
        layout.addWidget(self.include_content_check)
        render_hint = QLabel("Desactiva la casilla si quieres un render visual limpio, sin libros ni DVD dentro del mueble.")
        render_hint.setObjectName("PanelHint")
        render_hint.setWordWrap(True)
        layout.addWidget(render_hint)
        layout.addWidget(self.auto_open_folder_check)

        buttons_top = QHBoxLayout()
        autodetect = QPushButton("Detectar Blender")
        autodetect.clicked.connect(self.autodetect_blender)
        browse_blender = QPushButton("Buscar ejecutable")
        browse_blender.clicked.connect(self.select_blender_executable)
        buttons_top.addWidget(autodetect)
        buttons_top.addWidget(browse_blender)
        layout.addLayout(buttons_top)

        buttons_mid = QHBoxLayout()
        browse_output = QPushButton("Carpeta salida")
        browse_output.clicked.connect(self.select_output_directory)
        open_output = QPushButton("Abrir salida")
        open_output.clicked.connect(self.open_output_directory)
        buttons_mid.addWidget(browse_output)
        buttons_mid.addWidget(open_output)
        layout.addLayout(buttons_mid)

        render_row = QHBoxLayout()
        render_visual = QPushButton("Render visual PNG")
        render_visual.clicked.connect(self.render_visual)
        render_technical = QPushButton("Render técnico")
        render_technical.clicked.connect(self.render_manufacturing)
        render_full = QPushButton("Render completo")
        render_full.setObjectName("PrimaryButton")
        render_full.clicked.connect(self.render_all)
        render_row.addWidget(render_visual)
        render_row.addWidget(render_technical)
        layout.addLayout(render_row)
        layout.addWidget(render_full)
        return panel

    def _build_project_summary_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("PanelCard")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel("Resultado rápido")
        title.setObjectName("SectionTitle")
        subtitle = QLabel("Aquí verás una lectura corta del proyecto generado. La carpintería y el kerf solo aparecen cuando ya tienes una propuesta elegida.")
        subtitle.setObjectName("PanelHint")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        self.summary_card_text = QLabel(
            "Genera un proyecto para ver columnas, filas, ancho útil y una explicación resumida de la propuesta."
        )
        self.summary_card_text.setObjectName("PanelHint")
        self.summary_card_text.setWordWrap(True)
        layout.addWidget(self.summary_card_text)
        return panel

    def _build_carpentry_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("PanelCard")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel("Módulo carpintería")
        title.setObjectName("SectionTitle")
        subtitle = QLabel("Este bloque es para afinar fabricación una vez tengas clara la elección. Aquí vive el kerf y los ajustes que usarás tú como carpintera.")
        subtitle.setObjectName("PanelHint")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        form = QFormLayout()
        form.setSpacing(8)
        form.addRow("Kerf", self.kerf_input)
        form.addRow("Composición", self.layout_combo)
        form.addRow("Reparto restante", self.distribution_combo)
        form.addRow("Columnas fijas", self.fixed_columns_input)
        form.addRow("Filas fijas", self.fixed_rows_input)
        layout.addLayout(form)

        toggles = QVBoxLayout()
        toggles.setSpacing(6)
        toggles.addWidget(self.has_back_check)
        toggles.addWidget(self.split_back_check)
        toggles.addWidget(self.center_divider_check)
        toggles.addWidget(self.auto_fill_check)
        layout.addLayout(toggles)

        self.carpentry_apply_button = QPushButton("Recalcular con ajustes de carpintería")
        self.carpentry_apply_button.clicked.connect(self.generate_bundle)
        layout.addWidget(self.carpentry_apply_button)

        self.carpentry_panel = panel
        panel.setVisible(False)
        return panel

    def _build_advanced_settings_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("PanelCard")
        layout = QFormLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        intro = QLabel("Ajustes avanzados del motor y de fabricación. Si no tienes claro qué tocar, deja Automático.")
        intro.setObjectName("PanelHint")
        intro.setWordWrap(True)
        layout.addRow(intro)
        layout.addRow("Composición", self.layout_combo)
        layout.addRow("Colocación", self.distribution_combo)
        layout.addRow("Kerf", self.kerf_input)
        layout.addRow("Cantidad aprox.", self.quantity_input)
        layout.addRow("Columnas fijas", self.fixed_columns_input)
        layout.addRow("Filas fijas", self.fixed_rows_input)
        layout.addRow("Trasera", self.back_input)

        toggles = QVBoxLayout()
        toggles.addWidget(self.has_back_check)
        toggles.addWidget(self.split_back_check)
        toggles.addWidget(self.center_divider_check)
        toggles.addWidget(self.auto_fill_check)
        wrapper = QWidget()
        wrapper.setLayout(toggles)
        layout.addRow("Construcción", wrapper)
        return panel

    def _build_bottom_tabs(self) -> QWidget:
        placeholder = QWidget()
        placeholder.setVisible(False)
        return placeholder
