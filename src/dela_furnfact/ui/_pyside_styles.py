"""Estilos compartidos de la GUI PySide6."""

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

def app_stylesheet(theme: str) -> str:
    palette = DARK_THEME if theme == "dark" else LIGHT_THEME
    return f"""
    * {{
        color: {palette["text"]};
        font-family: "Segoe UI", "Inter", "Arial";
        font-size: 13px;
    }}
    QMainWindow, QWidget#RootWidget {{
        background: {palette["window"]};
    }}
    QFrame#HeaderFrame {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {palette["panel"]},
            stop:0.35 {palette["panel_alt"]},
            stop:1 {palette["panel"]});
        border: 1px solid {palette["border"]};
        border-radius: 18px;
    }}
    QFrame#PanelCard, QGroupBox#PanelCard, QFrame#PreviewShell, QFrame#MetricsStrip {{
        background: {palette["panel"]};
        border: 1px solid {palette["border"]};
        border-radius: 18px;
    }}
    QFrame#PreviewInner {{
        background: {palette["preview"]};
        border: 1px solid {palette["border"]};
        border-radius: 20px;
    }}
    QFrame#InlineCard {{
        background: {palette["panel_alt"]};
        border: 1px solid {palette["border"]};
        border-radius: 14px;
    }}
    QLabel#BrandTitle {{
        font-size: 34px;
        font-weight: 800;
        letter-spacing: 2px;
    }}
    QLabel#BrandSubtitle {{
        color: {palette["muted"]};
        font-size: 12px;
        letter-spacing: 1px;
        text-transform: uppercase;
    }}
    QLabel#SectionTitle {{
        font-size: 14px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }}
    QLabel#PanelHint {{
        color: {palette["muted"]};
        font-size: 11px;
    }}
    QLabel#MetricValue {{
        font-size: 22px;
        font-weight: 700;
    }}
    QLabel#MetricCaption {{
        color: {palette["muted"]};
        font-size: 11px;
        letter-spacing: 0.4px;
    }}
    QLabel#ChipLabel {{
        background: {palette["accent_soft"]};
        color: {palette["text"]};
        padding: 4px 10px;
        border-radius: 10px;
        border: 1px solid {palette["border"]};
        font-size: 11px;
        font-weight: 600;
    }}
    QGroupBox {{
        margin-top: 18px;
        padding-top: 18px;
        font-weight: 700;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        top: 4px;
        color: {palette["muted"]};
    }}
    QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox, QPlainTextEdit, QListWidget {{
        background: {palette["panel_alt"]};
        border: 1px solid {palette["border"]};
        border-radius: 12px;
        padding: 8px 10px;
        selection-background-color: {palette["accent"]};
        selection-color: #ffffff;
        color: {palette["text"]};
    }}
    QComboBox {{
        padding-right: 28px;
    }}
    QComboBox:on {{
        border-color: {palette["accent"]};
    }}
    QComboBox QAbstractItemView {{
        background: {palette["panel_alt"]};
        color: {palette["text"]};
        border: 1px solid {palette["border"]};
        outline: none;
        selection-background-color: {palette["accent"]};
        selection-color: #ffffff;
        padding: 6px;
    }}
    QDoubleSpinBox::up-button, QDoubleSpinBox::down-button,
    QSpinBox::up-button, QSpinBox::down-button {{
        width: 18px;
        border: none;
        background: transparent;
    }}
    QPlainTextEdit {{
        padding: 12px;
    }}
    QListWidget {{
        outline: none;
    }}
    QListWidget::item {{
        border: 1px solid {palette["border"]};
        border-radius: 12px;
        background: {palette["panel_alt"]};
        margin: 3px;
        padding: 10px;
    }}
    QListWidget::item:selected {{
        background: {palette["accent_soft"]};
        border: 1px solid {palette["accent"]};
    }}
    QPushButton {{
        background: {palette["panel_alt"]};
        border: 1px solid {palette["border"]};
        border-radius: 12px;
        padding: 9px 14px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        border-color: {palette["accent"]};
    }}
    QPushButton#PrimaryButton {{
        background: {palette["accent"]};
        border: 1px solid {palette["accent"]};
        color: white;
    }}
    QPushButton#GhostButton {{
        background: transparent;
    }}
    QPushButton#ModeButton:checked {{
        background: {palette["accent"]};
        border: 1px solid {palette["accent"]};
        color: white;
    }}
    QToolButton {{
        background: transparent;
        border: 1px solid {palette["border"]};
        border-radius: 12px;
        padding: 8px 12px;
        font-weight: 600;
    }}
    QToolButton:checked {{
        background: {palette["accent"]};
        border-color: {palette["accent"]};
        color: white;
    }}
    QCheckBox {{
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 6px;
        border: 1px solid {palette["border"]};
        background: {palette["panel_alt"]};
    }}
    QCheckBox::indicator:checked {{
        background: {palette["accent"]};
        border: 1px solid {palette["accent"]};
    }}
    QTabWidget::pane {{
        border: 1px solid {palette["border"]};
        border-radius: 16px;
        background: {palette["panel"]};
        top: -1px;
    }}
    QTabBar::tab {{
        background: transparent;
        padding: 10px 14px;
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        margin-right: 2px;
        color: {palette["muted"]};
    }}
    QTabBar::tab:selected {{
        color: {palette["text"]};
        background: {palette["panel_alt"]};
        border-bottom: 2px solid {palette["accent"]};
    }}
    QSplitter::handle {{
        background: {palette["window"]};
    }}
    QStatusBar {{
        background: transparent;
        color: {palette["muted"]};
    }}
    """

__all__ = ["app_stylesheet"]
