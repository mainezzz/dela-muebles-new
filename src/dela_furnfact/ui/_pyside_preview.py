"""Widgets de preview y tarjetas auxiliares de la GUI."""

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

class MetricCard(QFrame):
    """Tarjeta de métrica compacta."""

    def __init__(self, caption: str) -> None:
        super().__init__()
        self.setObjectName("InlineCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        self.value_label = QLabel("—")
        self.value_label.setObjectName("MetricValue")
        self.caption_label = QLabel(caption)
        self.caption_label.setObjectName("MetricCaption")
        layout.addWidget(self.value_label)
        layout.addWidget(self.caption_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)

class InlineAlertCard(QFrame):
    """Aviso inline elegante para errores y pistas de uso."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("AlertCard")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        icon = QLabel("!")
        icon.setObjectName("ChipLabel")
        icon.setFixedWidth(28)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon, 0, Qt.AlignmentFlag.AlignTop)

        copy = QVBoxLayout()
        copy.setSpacing(4)
        self.title_label = QLabel("Aviso")
        self.title_label.setObjectName("AlertTitle")
        self.text_label = QLabel("")
        self.text_label.setObjectName("AlertText")
        self.text_label.setWordWrap(True)
        copy.addWidget(self.title_label)
        copy.addWidget(self.text_label)
        layout.addLayout(copy, 1)

        self.dismiss_button = QToolButton()
        self.dismiss_button.setText("✕")
        self.dismiss_button.setAutoRaise(True)
        self.dismiss_button.clicked.connect(self.hide)
        layout.addWidget(self.dismiss_button, 0, Qt.AlignmentFlag.AlignTop)

        self.hide()

    def show_message(self, title: str, text: str) -> None:
        self.title_label.setText(title)
        self.text_label.setText(text)
        self.show()

class ShelfPreviewWidget(QWidget):
    """Preview principal DELA con modos visual y técnico."""

    def __init__(self) -> None:
        super().__init__()
        self._bundle: ProjectBundle | None = None
        self._mode = "visual"
        self._theme = "dark"
        self._selected_index: int | None = None
        self.setMinimumSize(280, 300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_bundle(self, bundle: ProjectBundle | None) -> None:
        self._bundle = bundle
        self.update()

    def set_preview_mode(self, mode: str) -> None:
        self._mode = mode
        self.update()

    def set_theme(self, theme: str) -> None:
        self._theme = theme
        self.update()

    def set_selected_opening(self, index: int | None) -> None:
        self._selected_index = index
        self.update()

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(620, 500)

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        painter = QPainter()
        try:
            painter.begin(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            palette = DARK_THEME if self._theme == "dark" else LIGHT_THEME
            canvas = self.rect().adjusted(16, 16, -16, -16)
            gradient = QLinearGradient(canvas.topLeft(), canvas.bottomRight())
            if self._mode == "visual":
                gradient.setColorAt(0.0, QColor("#111318" if self._theme == "dark" else "#ffffff"))
                gradient.setColorAt(1.0, QColor("#191d23" if self._theme == "dark" else "#eef1f6"))
            else:
                gradient.setColorAt(0.0, QColor("#0f1218" if self._theme == "dark" else "#ffffff"))
                gradient.setColorAt(1.0, QColor("#121720" if self._theme == "dark" else "#f5f7fb"))
            painter.setPen(QPen(QColor(palette["border"]), 1.3))
            painter.setBrush(gradient)
            painter.drawRoundedRect(canvas, 22, 22)

            title_rect = canvas.adjusted(24, 18, -24, -canvas.height() + 60)
            painter.setPen(QColor(palette["muted"]))
            painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "PREVIEW STUDIO")

            if self._bundle is None:
                self._draw_empty_state(painter, canvas, palette)
                return

            self._draw_bundle(painter, canvas, palette)
        finally:
            if painter.isActive():
                painter.end()

    def _draw_empty_state(self, painter: QPainter, canvas, palette: dict[str, str]) -> None:
        inner = canvas.adjusted(42, 90, -42, -42)
        painter.setPen(QPen(QColor(palette["border"]), 1.2, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(inner, 20, 20)

        painter.setPen(QColor(palette["text"]))
        title_font = QFont(painter.font())
        title_font.setPointSize(20)
        title_font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(title_font)
        painter.drawText(inner.adjusted(0, 60, 0, -80), Qt.AlignmentFlag.AlignHCenter, "DELA Preview Studio")

        painter.setPen(QColor(palette["muted"]))
        body_font = QFont(painter.font())
        body_font.setPointSize(11)
        body_font.setWeight(QFont.Weight.Normal)
        painter.setFont(body_font)
        painter.drawText(
            inner.adjusted(60, 120, -60, -40),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
            "Define las medidas, ajusta los huecos y pulsa “Generar proyecto”.\n"
            "Cuando la preview esté aprobada, usa Blender para obtener los PNG y archivos finales.",
        )

    def _draw_bundle(self, painter: QPainter, canvas, palette: dict[str, str]) -> None:
        bundle = self._bundle
        assert bundle is not None

        plan = bundle.plan
        board = max(plan.board_thickness_mm, 1.0)
        total_w = max(plan.outer_width_mm, 1.0)
        total_h = max(plan.outer_height_mm, 1.0)

        work = canvas.adjusted(48, 84, -48, -58)
        label_band = 70 if self._mode == "technical" else 38
        draw_area = work.adjusted(0, 0, -0, -label_band)

        scale = min(draw_area.width() / total_w, draw_area.height() / total_h)
        draw_w = total_w * scale
        draw_h = total_h * scale

        origin_x = draw_area.x() + (draw_area.width() - draw_w) / 2
        origin_y = draw_area.y() + (draw_area.height() - draw_h) / 2

        board_px = max(board * scale, 4.0)
        shelf_fill = QColor("#f4f1eb" if self._mode == "visual" else "#181c23")
        wood_fill = QColor("#c8b39a" if self._mode == "visual" else "#1f2630")
        opening_fill = QColor("#ece4da" if self._mode == "visual" else "#0f1116")
        opening_pen = QColor("#15181d" if self._mode == "visual" else palette["border"])

        if self._mode == "visual":
            shadow_color = QColor(0, 0, 0, 45)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(shadow_color)
            painter.drawRoundedRect(int(origin_x + 12), int(origin_y + 18), int(draw_w), int(draw_h), 20, 20)

        outer_rect = self._rounded_rect_tuple(origin_x, origin_y, draw_w, draw_h)
        painter.setPen(QPen(QColor("#24272f" if self._mode == "visual" else palette["border"]), 1.4))
        painter.setBrush(shelf_fill)
        painter.drawRoundedRect(*outer_rect)

        rows = max(plan.rows, 1)
        cols = max(plan.columns, 1)
        section_width_px = plan.clear_section_width_mm * scale
        row_heights_px = [opening.clear_height_mm * scale for opening in plan.openings[:rows]]

        # Carcasa.
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(wood_fill)
        painter.drawRect(int(origin_x), int(origin_y), int(draw_w), int(board_px))
        painter.drawRect(int(origin_x), int(origin_y + draw_h - board_px), int(draw_w), int(board_px))
        painter.drawRect(int(origin_x), int(origin_y), int(board_px), int(draw_h))
        painter.drawRect(int(origin_x + draw_w - board_px), int(origin_y), int(board_px), int(draw_h))

        internal_x = origin_x + board_px
        internal_y = origin_y + board_px
        internal_h = draw_h - (2 * board_px)

        for divider in range(1, cols):
            divider_x = internal_x + divider * section_width_px + (divider - 1) * board_px
            painter.drawRect(int(divider_x), int(origin_y + board_px), int(board_px), int(internal_h))

        y_cursor = internal_y
        measurement_color = QColor(palette["accent"])
        technical_pen = QPen(measurement_color, 1.1)
        technical_pen.setCosmetic(True)

        selected_label = None
        requested_types = list(bundle.request.requested_openings)
        if self._selected_index is not None and 0 <= self._selected_index < len(requested_types):
            selected_label = requested_types[self._selected_index].label

        preview_model = PreviewMapper.from_bundle(bundle, selected_label=selected_label)

        for row in range(rows):
            opening_h = row_heights_px[row] if row < len(row_heights_px) else max(internal_h / rows - board_px, 20)
            x_cursor = internal_x
            row_view = preview_model.row_items[row] if row < len(preview_model.row_items) else None

            for col in range(cols):
                open_rect = self._rounded_rect_tuple(x_cursor, y_cursor, section_width_px, opening_h)
                painter.setPen(QPen(opening_pen, 1.2))
                painter.setBrush(opening_fill)
                painter.drawRoundedRect(*open_rect)

                if row_view is not None:
                    if self._mode == "visual":
                        self._draw_opening_content(painter, open_rect, row_view.source_label, palette)
                    if row_view.highlighted:
                        painter.setPen(QPen(QColor(palette["accent"]), 2.8))
                        painter.setBrush(Qt.BrushStyle.NoBrush)
                        highlight = self._rounded_rect_tuple(x_cursor - 3, y_cursor - 3, section_width_px + 6, opening_h + 6)
                        painter.drawRoundedRect(*highlight)

                    if self._mode == "technical":
                        self._draw_opening_measurements(
                            painter,
                            open_rect,
                            row_view.clear_height_mm,
                            row_view.clear_width_mm,
                            technical_pen,
                            palette,
                            show_vertical=(col == 0),
                            show_horizontal=False,
                        )
                x_cursor += section_width_px + board_px

            if self._mode == "technical" and row_view is not None:
                total_row_width = cols * section_width_px + (cols - 1) * board_px
                self._draw_technical_row_label(
                    painter,
                    internal_x,
                    y_cursor,
                    total_row_width,
                    opening_h,
                    row_view.source_label,
                    palette,
                )

            if row < rows - 1:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(wood_fill)
                painter.drawRect(int(origin_x + board_px), int(y_cursor + opening_h), int(draw_w - 2 * board_px), int(board_px))
            y_cursor += opening_h + board_px

        self._draw_main_measurements(painter, origin_x, origin_y, draw_w, draw_h, plan.outer_width_mm, plan.outer_height_mm, palette)

        if self._mode == "technical":
            legend_rect = canvas.adjusted(28, canvas.height() - 54, -28, -16)
            painter.setPen(QColor(palette["muted"]))
            painter.drawText(
                legend_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                f"Modo técnico · {plan.columns} columnas · {plan.rows} filas · Grosor {plan.board_thickness_mm:.0f} mm",
            )

    @staticmethod
    def _rounded_rect_tuple(x: float, y: float, w: float, h: float) -> tuple[int, int, int, int, int, int]:
        return (int(x), int(y), int(w), int(h), 18, 18)


    def _draw_opening_content(self, painter: QPainter, rect_args, label: str, palette: dict[str, str]) -> None:
        x, y, w, h, _, _ = rect_args
        inner = QRect(int(x + 12), int(y + 12), int(max(w - 24, 10)), int(max(h - 24, 10)))
        display_label = display_opening_label(label, short=self._mode == "visual")
        content_kind = opening_kind(label)

        if self._mode == "visual":
            self._draw_visual_content_hint(painter, inner, content_kind, palette)
        else:
            self._draw_technical_label(painter, inner, display_label, palette)
            return

        pill_margin_x = 18
        max_width = max(min(int(inner.width() - pill_margin_x * 2), 200), 60)

        label_font = QFont(painter.font())
        label_font.setWeight(QFont.Weight.Bold)
        point_size = 10 if h > 96 else 9
        target_width = 72
        clipped = display_label
        while point_size >= 7:
            label_font.setPointSize(point_size)
            painter.setFont(label_font)
            metrics = painter.fontMetrics()
            clipped = self._elided_text(display_label, metrics, max(max_width - 16, 20))
            target_width = metrics.horizontalAdvance(clipped) + 22
            if target_width <= max_width or point_size == 7:
                break
            point_size -= 1

        pill_width = min(max(target_width, 58), max_width)
        pill_height = min(max(int(inner.height() * 0.28), 16), 26)
        pill_y = int(inner.center().y() - pill_height / 2)
        pill_rect = QRect(
            int(inner.center().x() - pill_width / 2),
            int(pill_y),
            int(pill_width),
            int(pill_height),
        )
        pill_fill = QColor("#930000")
        pill_border = QColor("#f3d7dc")
        painter.setPen(QPen(pill_border, 1.2))
        painter.setBrush(pill_fill)
        painter.drawRoundedRect(pill_rect, 12, 12)

        painter.setPen(QColor("#fff7f7"))
        metrics = painter.fontMetrics()
        clipped = self._elided_text(display_label, metrics, max(pill_rect.width() - 12, 20))
        text_rect = pill_rect.adjusted(4, 0, -4, 0)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, clipped)

    @staticmethod
    def _display_opening_label(label: str, short: bool = False) -> str:
        return display_opening_label(label, short=short)

    @staticmethod
    def _opening_kind(label: str) -> str:
        return opening_kind(label)


    def _draw_spines(
        self,
        painter: QPainter,
        inner: QRect,
        count: int,
        body_color: QColor,
        accent_color: QColor,
        width_factor: float = 1.0,
    ) -> None:
        painter.save()
        count = max(int(count), 1)

        available_w = max(float(inner.width()), 12.0)
        available_h = max(float(inner.height()), 12.0)
        gap = max(available_w * 0.02, 3.0)

        raw_w = (available_w - gap * (count - 1)) / count
        spine_w = max(raw_w * width_factor, 6.0)
        total_w = spine_w * count + gap * (count - 1)

        if total_w > available_w:
            scale = available_w / total_w
            spine_w *= scale
            gap *= scale
            total_w = spine_w * count + gap * (count - 1)

        start_x = inner.x() + (available_w - total_w) / 2.0
        radius = min(max(inner.height() * 0.18, 4.0), 10.0)

        for index in range(count):
            x = start_x + index * (spine_w + gap)
            spine_rect = QRect(
                int(round(x)),
                int(inner.y()),
                max(int(round(spine_w)), 4),
                int(available_h),
            )
            painter.setPen(QPen(QColor("#1c1f27"), 1))
            painter.setBrush(body_color)
            painter.drawRoundedRect(spine_rect, radius, radius)

            band_h = max(int(spine_rect.height() * 0.16), 5)
            band_rect = QRect(
                spine_rect.x(),
                spine_rect.y() + int(spine_rect.height() * 0.20),
                spine_rect.width(),
                band_h,
            )
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(accent_color)
            painter.drawRoundedRect(band_rect, max(radius - 2, 2), max(radius - 2, 2))

        painter.restore()

    def _draw_visual_content_hint(self, painter: QPainter, inner: QRect, content_kind: str, palette: dict[str, str]) -> None:
        painter.save()
        # v12-fixed6: keep the visual preview clean; the pill label is enough to identify the opening type.
        painter.restore()


    def _draw_technical_label(self, painter: QPainter, inner: QRect, display_label: str, palette: dict[str, str]) -> None:
        painter.save()
        font = QFont(painter.font())
        font.setPointSize(8)
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.setPen(QColor("#eef1f6"))
        text_rect = inner.adjusted(10, 10, -10, -10)
        clipped = self._elided_text(display_label, painter.fontMetrics(), max(text_rect.width(), 20))
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, clipped)
        painter.restore()

    def _draw_technical_row_label(
        self,
        painter: QPainter,
        origin_x: float,
        y: float,
        total_width: float,
        opening_h: float,
        label: str,
        palette: dict[str, str],
    ) -> None:
        painter.save()
        font = QFont(painter.font())
        font.setPointSize(8)
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.setPen(QColor("#eef1f6"))
        rect = QRect(int(origin_x), int(y), int(total_width), int(opening_h))
        display = self._display_opening_label(label, short=True)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, display)
        painter.restore()

    def _draw_opening_measurements(
        self,
        painter: QPainter,
        rect_args,
        clear_height_mm: float,
        clear_width_mm: float,
        pen: QPen,
        palette: dict[str, str],
        show_vertical: bool = True,
        show_horizontal: bool = True,
    ) -> None:
        x, y, w, h, _, _ = rect_args

        painter.setPen(QColor(palette["muted"]))
        font = QFont(painter.font())
        font.setPointSize(5)
        painter.setFont(font)

        if show_horizontal:
            painter.drawText(int(x), int(y + h + 16), int(w), 12, Qt.AlignmentFlag.AlignCenter, f"{clear_width_mm:.0f} mm")

        if show_vertical:
            painter.save()
            painter.translate(int(x - 18), int(y + h / 2))
            painter.rotate(-90)
            painter.drawText(-int(h / 2), -2, int(h), 11, Qt.AlignmentFlag.AlignCenter, f"{clear_height_mm:.0f} mm")
            painter.restore()

    def _draw_main_measurements(
        self,
        painter: QPainter,
        origin_x: float,
        origin_y: float,
        draw_w: float,
        draw_h: float,
        width_mm: float,
        height_mm: float,
        palette: dict[str, str],
    ) -> None:
        painter.setPen(QPen(QColor(palette["accent"]), 1.4))
        painter.drawLine(int(origin_x), int(origin_y + draw_h + 30), int(origin_x + draw_w), int(origin_y + draw_h + 30))
        painter.drawLine(int(origin_x), int(origin_y + draw_h + 24), int(origin_x), int(origin_y + draw_h + 36))
        painter.drawLine(int(origin_x + draw_w), int(origin_y + draw_h + 24), int(origin_x + draw_w), int(origin_y + draw_h + 36))

        painter.drawLine(int(origin_x - 30), int(origin_y), int(origin_x - 30), int(origin_y + draw_h))
        painter.drawLine(int(origin_x - 36), int(origin_y), int(origin_x - 24), int(origin_y))
        painter.drawLine(int(origin_x - 36), int(origin_y + draw_h), int(origin_x - 24), int(origin_y + draw_h))

        painter.setPen(QColor(palette["text"]))
        width_font = QFont(painter.font())
        width_font.setPointSize(10)
        width_font.setWeight(QFont.Weight.Medium)
        painter.setFont(width_font)
        painter.drawText(int(origin_x), int(origin_y + draw_h + 36), int(draw_w), 20, Qt.AlignmentFlag.AlignCenter, f"{width_mm:.0f} mm")

        painter.save()
        painter.translate(int(origin_x - 54), int(origin_y + draw_h / 2))
        painter.rotate(-90)
        painter.drawText(-int(draw_h / 2), -4, int(draw_h), 20, Qt.AlignmentFlag.AlignCenter, f"{height_mm:.0f} mm")
        painter.restore()

    @staticmethod
    def _elided_text(text: str, metrics: QFontMetrics, width: int) -> str:
        return metrics.elidedText(text, Qt.TextElideMode.ElideRight, width)

__all__ = ["MetricCard", "InlineAlertCard", "ShelfPreviewWidget"]
