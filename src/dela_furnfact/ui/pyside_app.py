"""GUI PySide6 rediseñada para DELA."""

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

DARK_THEME = {
    "window": "#0c0d11",
    "panel": "#14161c",
    "panel_alt": "#181b22",
    "panel_soft": "#20252d",
    "surface": "#111318",
    "text": "#f5f5f7",
    "muted": "#9aa3b2",
    "border": "#262b34",
    "accent": "#930000",
    "accent_soft": "#4a0a0a",
    "success": "#2fa26f",
    "warning": "#f0b04a",
    "preview": "#0f1116",
}

LIGHT_THEME = {
    "window": "#f4f5f7",
    "panel": "#ffffff",
    "panel_alt": "#f7f8fb",
    "panel_soft": "#f0f2f5",
    "surface": "#ffffff",
    "text": "#111318",
    "muted": "#616b79",
    "border": "#d7dce5",
    "accent": "#930000",
    "accent_soft": "#f1d7d7",
    "success": "#20845a",
    "warning": "#a76d14",
    "preview": "#ffffff",
}

CONTENT_LABELS = {
    ContentType.BOOKS.value: "Libros",
    ContentType.DVD.value: "DVD",
}

LAYOUT_LABELS = {
    LayoutMode.AUTO.value: "Que lo decida el sistema",
    LayoutMode.BALANCED.value: "Más regular",
    LayoutMode.DENSE.value: "Más capacidad",
}

DISTRIBUTION_LABELS = {
    RemainingDistribution.AUTO.value: "Automático",
    RemainingDistribution.UNIFORM.value: "Mixto regular",
    RemainingDistribution.TOP_BOTTOM_LARGE.value: "Grandes arriba y abajo",
    RemainingDistribution.LARGEST_OPENINGS.value: "Dar más espacio a los grandes",
    RemainingDistribution.NONE.value: "Sin recolocar",
}

VISUAL_DISTRIBUTION_LABELS = {
    "mixed": "Mixta",
    "top_bottom_large": "Grandes arriba y abajo",
    "large_emphasis": "Centro grande",
    "compact": "Alternada compacta",
}

class FurnFactMainWindow(QMainWindow):
    """Ventana principal DELA Furniture Factory."""

    def __init__(self) -> None:
        super().__init__()
        self.service = FurnFactApplicationService()
        self.current_bundle: ProjectBundle | None = None
        self.current_request_path: Path | None = None
        self.current_output_path: Path | None = None
        self.render_thread: QThread | None = None
        self.render_worker: RenderWorker | None = None
        self.settings = QSettings("DELA", "dela-furnfact")
        self.theme = self.settings.value("theme", "dark")
        if self.theme not in {"dark", "light"}:
            self.theme = "dark"

        self.openings: list[OpeningRequest] = []
        self.current_opening_index: int | None = None

        self._init_fields()
        self._build_window()
        self._restore_settings()
        self._apply_theme()
        self.new_project()
        self.statusBar().showMessage("Listo para diseñar en DELA.")

    def _init_fields(self) -> None:
        self.name_input = QLineEdit("Proyecto DELA")
        self.width_input = self._double_spin(1636, 600, 6000, 0)
        self.height_input = self._double_spin(2000, 600, 5000, 0)
        self.depth_input = self._double_spin(300, 120, 1200, 0)
        self.board_input = self._double_spin(18, 10, 60, 1)
        self.back_input = self._double_spin(5, 0, 30, 1)
        self.kerf_input = self._double_spin(3, 0, 10, 1)
        self.quantity_input = self._spin(220, 0, 50000)
        self.fixed_columns_input = self._spin(None, 0, 12, special="Auto")
        self.fixed_rows_input = self._spin(None, 0, 20, special="Auto")

        self.content_combo = self._combo(CONTENT_LABELS, ContentType.BOOKS.value)
        self.visual_distribution_combo = self._combo(VISUAL_DISTRIBUTION_LABELS, "mixed")
        self.layout_combo = self._combo(LAYOUT_LABELS, LayoutMode.BALANCED.value)
        self.distribution_combo = self._combo(
            DISTRIBUTION_LABELS,
            RemainingDistribution.UNIFORM.value,
        )

        self.has_back_check = QCheckBox("Trasera")
        self.has_back_check.setChecked(True)
        self.split_back_check = QCheckBox("Trasera partida")
        self.split_back_check.setChecked(True)
        self.center_divider_check = QCheckBox("Divisor central")
        self.center_divider_check.setChecked(True)
        self.auto_fill_check = QCheckBox("Relleno automático")
        self.auto_fill_check.setChecked(True)

        self.blender_path_input = QLineEdit()
        self.render_output_input = QLineEdit(str(default_render_output_root() / "gui_render"))
        self.auto_open_folder_check = QCheckBox("Abrir carpeta al terminar")
        self.auto_open_folder_check.setChecked(False)
        self.include_content_check = QCheckBox("Incluir libros/DVD en el render visual")
        self.include_content_check.setChecked(True)

        self.preview_widget = ShelfPreviewWidget()
        self.preview_mode_stack = QStackedWidget()
        self.inline_alert = InlineAlertCard()

        self.openings_list = QListWidget()
        self.openings_list.currentRowChanged.connect(self._load_opening_to_editor)

        self.opening_label_input = QLineEdit()
        self.opening_label_input.setPlaceholderText("Ejemplo: DVD, BOXSET, novela pequeña, novela grande")
        self.opening_count_input = self._spin(1, 1, 50)
        self.opening_min_height_input = self._double_spin(240, 40, 2000, 0)
        self.opening_pref_height_input = self._double_spin(280, 40, 2000, 0)
        self.opening_max_height_input = self._double_spin(0, 0, 2000, 0)
        self.opening_min_width_input = self._double_spin(0, 0, 2000, 0)
        self.opening_priority_input = self._spin(3, 1, 5)
        self.opening_fixed_check = QCheckBox("Altura fija")
        self.opening_summary_label = QLabel("Selecciona un hueco para editarlo.")
        self.opening_summary_label.setObjectName("PanelHint")
        self.opening_label_input.textChanged.connect(self._update_opening_editor_state)

        self.metric_columns_rows = MetricCard("Columnas × filas")
        self.metric_section_width = MetricCard("Ancho útil sección")
        self.metric_row_height = MetricCard("Altura útil media")
        self.metric_capacity = MetricCard("Tipos / cantidad")
        self.metric_parts = MetricCard("Piezas")
        self.metric_boards = MetricCard("Tableros")

        self.bundle_json = QPlainTextEdit()
        self.bundle_json.setReadOnly(True)
        self.summary_text = QPlainTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_card_text = self.summary_text
        self.parts_text = QPlainTextEdit()
        self.parts_text.setReadOnly(True)
        self.boards_text = QPlainTextEdit()
        self.boards_text.setReadOnly(True)
        self.render_log = QPlainTextEdit()
        self.render_log.setReadOnly(True)
        self.help_text = QPlainTextEdit()
        self.help_text.setReadOnly(True)
        self.help_text.setPlainText(APP_HELP_TEXT + "\n\nPlantilla JSON:\n\n" + request_template_text())

        self.visual_mode_button = self._mode_button("Visual", True)
        self.technical_mode_button = self._mode_button("Técnico", False)
        self.visual_mode_button.clicked.connect(lambda: self._set_preview_mode("visual"))
        self.technical_mode_button.clicked.connect(lambda: self._set_preview_mode("technical"))

        self.theme_button = QPushButton("Modo claro")
        self.theme_button.clicked.connect(self.toggle_theme)
        self.content_combo.currentIndexChanged.connect(self._on_content_type_changed)
        self.content_combo.currentIndexChanged.connect(self._update_quick_preset_labels)
        self.visual_distribution_combo.currentIndexChanged.connect(self._apply_visual_distribution_choice)

        self.blender_state_chip = QLabel("Blender: pendiente")
        self.blender_state_chip.setObjectName("ChipLabel")
        self.legacy_state_chip = QLabel("Legacy: pendiente")
        self.legacy_state_chip.setObjectName("ChipLabel")

    @staticmethod
    def _combo(values: Iterable[str] | dict[str, str], current: str) -> QComboBox:
        combo = QComboBox()
        if isinstance(values, dict):
            for value, label in values.items():
                combo.addItem(label, value)
            target = combo.findData(current)
            combo.setCurrentIndex(target if target >= 0 else 0)
        else:
            combo.addItems(list(values))
            combo.setCurrentText(current)
        return combo

    @staticmethod
    def _double_spin(value: float, minimum: float, maximum: float, decimals: int) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(minimum, maximum)
        spin.setDecimals(decimals)
        spin.setValue(value)
        spin.setAlignment(Qt.AlignmentFlag.AlignRight)
        spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        spin.setMinimumWidth(110)
        return spin

    @staticmethod
    def _spin(value: int | None, minimum: int, maximum: int, special: str | None = None) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(minimum, maximum)
        if special is not None:
            spin.setSpecialValueText(special)
            spin.setValue(minimum)
        elif value is not None:
            spin.setValue(value)
        spin.setAlignment(Qt.AlignmentFlag.AlignRight)
        spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        spin.setMinimumWidth(100)
        return spin

    @staticmethod
    def _mode_button(text: str, checked: bool) -> QToolButton:
        button = QToolButton()
        button.setText(text)
        button.setCheckable(True)
        button.setChecked(checked)
        button.setObjectName("ModeButton")
        return button

    def _build_window(self) -> None:
        self.setWindowTitle("DELA · Furniture Factory")
        self.resize(1560, 960)
        self.setStatusBar(QStatusBar(self))

        root = QWidget()
        root.setObjectName("RootWidget")
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(16, 16, 16, 12)
        root_layout.setSpacing(14)

        root_layout.addWidget(self._build_header())

        body_splitter = QSplitter(Qt.Orientation.Horizontal)
        body_splitter.setChildrenCollapsible(False)
        body_splitter.setHandleWidth(10)
        body_splitter.addWidget(self._build_left_panel())
        body_splitter.addWidget(self._build_center_panel())
        body_splitter.addWidget(self._build_right_panel())
        body_splitter.setStretchFactor(0, 1)
        body_splitter.setStretchFactor(1, 1)
        body_splitter.setStretchFactor(2, 1)
        body_splitter.setSizes([220, 360, 220])

        root_layout.addWidget(body_splitter)

    def _build_menu(self) -> None:
        return

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

    def _on_content_type_changed(self) -> None:
        self._update_quick_preset_labels()
        if self.openings:
            self.openings = []
            self.refresh_openings_ui()
            self.preview_widget.set_bundle(None)
            self.current_bundle = None
            self._clear_metrics()
            self._notify_inline(
                "Contenido cambiado",
                "Se han limpiado los tipos de hueco del proyecto anterior. Añade tipos del nuevo contenido y pulsa Generar proyecto.",
            )
            if hasattr(self, "project_state_chip"):
                self.project_state_chip.setText("Sin generar")
            self.generate_button.setText("Generar proyecto")
        else:
            self.reset_opening_editor()

    def _update_quick_preset_labels(self) -> None:
        if not hasattr(self, "quick_button_a"):
            return
        current_value = self.content_combo.currentData() or self.content_combo.currentText()
        content_type = ContentType(current_value)
        choices = opening_type_choices(content_type)
        self.quick_button_a.setText(choices[0].display_label)
        self.quick_button_b.setText(choices[1].display_label)
        if self.current_opening_index is None:
            self.reset_opening_editor()

    def _apply_visual_distribution_choice(self) -> None:
        choice = self.visual_distribution_combo.currentData() or self.visual_distribution_combo.currentText()
        mapping = {
            "mixed": (LayoutMode.AUTO.value, RemainingDistribution.UNIFORM.value),
            "top_bottom_large": (LayoutMode.AUTO.value, RemainingDistribution.TOP_BOTTOM_LARGE.value),
            "large_emphasis": (LayoutMode.AUTO.value, RemainingDistribution.LARGEST_OPENINGS.value),
            "compact": (LayoutMode.DENSE.value, RemainingDistribution.UNIFORM.value),
        }
        layout_mode, distribution = mapping.get(choice, (LayoutMode.AUTO.value, RemainingDistribution.UNIFORM.value))
        self.layout_combo.setCurrentIndex(max(0, self.layout_combo.findData(layout_mode)))
        self.distribution_combo.setCurrentIndex(max(0, self.distribution_combo.findData(distribution)))

    def _set_preview_mode(self, mode: str) -> None:
        if mode == "visual":
            self.visual_mode_button.setChecked(True)
            self.technical_mode_button.setChecked(False)
        else:
            self.visual_mode_button.setChecked(False)
            self.technical_mode_button.setChecked(True)
        self.preview_widget.set_preview_mode(mode)

    def toggle_theme(self) -> None:
        self.theme = "light" if self.theme == "dark" else "dark"
        self._apply_theme()
        self.settings.setValue("theme", self.theme)

    def _apply_theme(self) -> None:
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(app_stylesheet(self.theme))
        self.preview_widget.set_theme(self.theme)
        self.theme_button.setText("Modo claro" if self.theme == "dark" else "Modo oscuro")

    def closeEvent(self, event) -> None:  # noqa: N802
        self._save_settings()
        super().closeEvent(event)

    def _save_settings(self) -> None:
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("blender_path", self.blender_path_input.text().strip())
        self.settings.setValue("render_output", self.render_output_input.text().strip())
        self.settings.setValue("theme", self.theme)

    def _restore_settings(self) -> None:
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        blender_path = self.settings.value("blender_path", "")
        render_output = self.settings.value("render_output", "")
        if blender_path:
            self.blender_path_input.setText(str(blender_path))
        if render_output:
            self.render_output_input.setText(str(render_output))

    def _seed_demo_books(self, silent: bool = False) -> None:
        self.name_input.setText("DELA · Libros 4-4")
        self.width_input.setValue(1636)
        self.height_input.setValue(2000)
        self.depth_input.setValue(300)
        self.board_input.setValue(18)
        self.back_input.setValue(5)
        self.quantity_input.setValue(160)
        self.kerf_input.setValue(3)
        self.content_combo.setCurrentIndex(max(0, self.content_combo.findData(ContentType.BOOKS.value)))
        self.visual_distribution_combo.setCurrentIndex(max(0, self.visual_distribution_combo.findData("top_bottom_large")))
        self._apply_visual_distribution_choice()
        self.fixed_columns_input.setValue(0)
        self.fixed_rows_input.setValue(0)
        self.has_back_check.setChecked(True)
        self.split_back_check.setChecked(True)
        self.center_divider_check.setChecked(True)
        self.auto_fill_check.setChecked(True)
        self.openings = [
            opening_request_from_type(OpeningTypeId.BOOK_LARGE, count=4),
            opening_request_from_type(OpeningTypeId.BOOK_SMALL, count=4),
        ]
        self.refresh_openings_ui()
        self._update_quick_preset_labels()
        self.generate_bundle(notify_errors=not silent)

    def _seed_demo_books_5_3(self, silent: bool = False) -> None:
        self.name_input.setText("DELA · Libros 5-3")
        self.width_input.setValue(1636)
        self.height_input.setValue(2000)
        self.depth_input.setValue(300)
        self.board_input.setValue(18)
        self.back_input.setValue(5)
        self.quantity_input.setValue(160)
        self.kerf_input.setValue(3)
        self.content_combo.setCurrentIndex(max(0, self.content_combo.findData(ContentType.BOOKS.value)))
        self.visual_distribution_combo.setCurrentIndex(max(0, self.visual_distribution_combo.findData("mixed")))
        self._apply_visual_distribution_choice()
        self.fixed_columns_input.setValue(0)
        self.fixed_rows_input.setValue(0)
        self.has_back_check.setChecked(True)
        self.split_back_check.setChecked(True)
        self.center_divider_check.setChecked(True)
        self.auto_fill_check.setChecked(True)
        self.openings = [
            OpeningRequest("Novela grande", 3, 249, 256, 260, 0, 2, False),
            OpeningRequest("Novela pequeña", 5, 210, 214, 220, 0, 3, False),
        ]
        self.refresh_openings_ui()
        self._update_quick_preset_labels()
        self.generate_bundle(notify_errors=not silent)

    def _seed_demo_dvd(self, silent: bool = False) -> None:
        self.name_input.setText("DELA · DVD")
        self.width_input.setValue(2036)
        self.height_input.setValue(2000)
        self.depth_input.setValue(200)
        self.board_input.setValue(18)
        self.back_input.setValue(5)
        self.quantity_input.setValue(400)
        self.kerf_input.setValue(3)
        self.content_combo.setCurrentIndex(max(0, self.content_combo.findData(ContentType.DVD.value)))
        self.visual_distribution_combo.setCurrentIndex(max(0, self.visual_distribution_combo.findData("top_bottom_large")))
        self._apply_visual_distribution_choice()
        self.fixed_columns_input.setValue(2)
        self.fixed_rows_input.setValue(0)
        self.has_back_check.setChecked(True)
        self.split_back_check.setChecked(True)
        self.center_divider_check.setChecked(True)
        self.auto_fill_check.setChecked(True)
        self.openings = [
            opening_request_from_type(OpeningTypeId.DVD, count=6),
            opening_request_from_type(OpeningTypeId.BOXSET, count=2),
        ]
        self.refresh_openings_ui()
        self.generate_bundle(notify_errors=not silent)

    def new_project(self) -> None:
        self.current_bundle = None
        self.current_request_path = None
        self.current_output_path = None
        self.name_input.setText("Proyecto DELA")
        self.width_input.setValue(1600)
        self.height_input.setValue(2000)
        self.depth_input.setValue(300)
        self.board_input.setValue(18)
        self.back_input.setValue(5)
        self.quantity_input.setValue(0)
        self.kerf_input.setValue(3)
        self.content_combo.setCurrentIndex(max(0, self.content_combo.findData(ContentType.BOOKS.value)))
        self.visual_distribution_combo.setCurrentIndex(max(0, self.visual_distribution_combo.findData("mixed")))
        self._apply_visual_distribution_choice()
        self.fixed_columns_input.setValue(0)
        self.fixed_rows_input.setValue(0)
        self.has_back_check.setChecked(True)
        self.split_back_check.setChecked(True)
        self.center_divider_check.setChecked(True)
        self.auto_fill_check.setChecked(True)
        self.openings = []
        self.refresh_openings_ui()
        self.preview_widget.set_bundle(None)
        self.preview_widget.set_selected_opening(None)
        self._update_opening_editor_state()
        self.summary_text.setPlainText(
            "1. Define medidas.\n"
            "2. Añade tipos de hueco.\n"
            "3. Indica cantidades por tipo.\n"
            "4. Elige una distribución visual.\n"
            "5. Pulsa Generar proyecto.\n"
            "6. Cuando lo tengas claro, usa Blender para el PNG final."
        )
        self.bundle_json.clear()
        self.parts_text.clear()
        self.boards_text.clear()
        self.render_log.clear()
        self._clear_metrics()
        self._update_blender_status()
        if hasattr(self, "carpentry_panel"):
            self.carpentry_panel.setVisible(False)
        self.inline_alert.hide()
        self.generate_button.setText("Generar proyecto")
        if hasattr(self, "project_state_chip"):
            self.project_state_chip.setText("Sin generar")
        self.statusBar().showMessage("Nuevo proyecto listo.")

    def _clear_metrics(self) -> None:
        for card in (
            self.metric_columns_rows,
            self.metric_section_width,
            self.metric_row_height,
            self.metric_capacity,
            self.metric_parts,
            self.metric_boards,
        ):
            card.set_value("—")

    def refresh_openings_ui(self) -> None:
        self.openings_list.clear()
        for opening in self.openings:
            view_model = OpeningTypeViewModel.from_request(opening)
            item = QListWidgetItem(view_model.summary)
            item.setData(Qt.ItemDataRole.UserRole, view_model)
            self.openings_list.addItem(item)

        if self.openings:
            target = self.current_opening_index if self.current_opening_index is not None else 0
            target = max(0, min(target, len(self.openings) - 1))
            self.openings_list.setCurrentRow(target)
        else:
            self.current_opening_index = None
            self.reset_opening_editor()

    def _collect_debug_state(self) -> dict:
        return {
            "theme": self.theme,
            "request": self._request_payload(),
            "has_bundle": self.current_bundle is not None,
        }

def launch_gui() -> None:
    """Lanza la aplicación PySide6 rediseñada."""

    app = QApplication.instance() or QApplication([])
    app.setApplicationName("dela-furnfact")
    app.setOrganizationName("DELA")
    window = FurnFactMainWindow()
    window.show()
    app.exec()
