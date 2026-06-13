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
from dela_furnfact.ui._main_window_domain_panels import _MainWindowDomainPanelsMixin
from dela_furnfact.ui._main_window_header import _MainWindowHeaderMixin
from dela_furnfact.ui._main_window_layout_panels import _MainWindowLayoutPanelsMixin

class FurnFactMainWindow(_MainWindowHeaderMixin, _MainWindowLayoutPanelsMixin, _MainWindowDomainPanelsMixin, QMainWindow):

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

    def _double_spin(value: float, minimum: float, maximum: float, decimals: int) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(minimum, maximum)
        spin.setDecimals(decimals)
        spin.setValue(value)
        spin.setAlignment(Qt.AlignmentFlag.AlignRight)
        spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        spin.setMinimumWidth(110)
        return spin

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

def launch_gui() -> None:
    """Lanza la aplicación PySide6 rediseñada."""

    app = QApplication.instance() or QApplication([])
    app.setApplicationName("dela-furnfact")
    app.setOrganizationName("DELA")
    window = FurnFactMainWindow()
    window.show()
    app.exec()
