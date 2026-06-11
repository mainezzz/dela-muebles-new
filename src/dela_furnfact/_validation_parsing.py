"""Helpers de parseo de requests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from dela_furnfact.models import (
    ContentType,
    LayoutMode,
    OpeningRequest,
    RemainingDistribution,
    ShelfRequest,
    VisualDistribution,
)
from dela_furnfact.opening_catalog import canonical_opening_label


def _optional_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _parse_opening(item: Mapping[str, Any]) -> OpeningRequest:
    return OpeningRequest(
        label=canonical_opening_label(str(item["label"])),
        count=int(item.get("count", 1)),
        min_clear_height_mm=float(item["min_clear_height_mm"]),
        preferred_clear_height_mm=_optional_float(item.get("preferred_clear_height_mm")),
        max_clear_height_mm=_optional_float(item.get("max_clear_height_mm")),
        min_clear_width_mm=float(item.get("min_clear_width_mm", 0.0)),
        priority=int(item.get("priority", 3)),
        fixed_height=bool(item.get("fixed_height", False)),
    )


def _parse_requested_openings(payload: Mapping[str, Any]) -> list[OpeningRequest]:
    return [_parse_opening(item) for item in payload.get("requested_openings", [])]


def parse_request_dict(payload: Mapping[str, Any]) -> ShelfRequest:
    """Construye un ShelfRequest desde JSON/dict."""

    return ShelfRequest(
        name=str(payload["name"]),
        width_mm=float(payload["width_mm"]),
        height_mm=float(payload["height_mm"]),
        depth_mm=float(payload["depth_mm"]),
        board_thickness_mm=float(payload.get("board_thickness_mm", 18.0)),
        back_panel_thickness_mm=float(payload.get("back_panel_thickness_mm", 5.0)),
        content_type=ContentType(str(payload.get("content_type", ContentType.BOOKS.value))),
        content_quantity=int(payload.get("content_quantity", 0)),
        layout_mode=LayoutMode(str(payload.get("layout_mode", LayoutMode.AUTO.value))),
        remaining_distribution=RemainingDistribution(
            str(payload.get("remaining_distribution", RemainingDistribution.AUTO.value))
        ),
        visual_distribution=VisualDistribution(
            str(payload.get("visual_distribution", VisualDistribution.AUTO.value))
        ),
        has_back_panel=bool(payload.get("has_back_panel", True)),
        split_back_panel=bool(payload.get("split_back_panel", True)),
        has_center_divider=bool(payload.get("has_center_divider", True)),
        kerf_mm=float(payload.get("kerf_mm", 3.0)),
        units=str(payload.get("units", "mm")),
        fixed_columns=_optional_int(payload.get("fixed_columns")),
        fixed_rows=_optional_int(payload.get("fixed_rows")),
        allow_auto_fill=bool(payload.get("allow_auto_fill", True)),
        requested_openings=_parse_requested_openings(payload),
    )


def load_request(path: Path) -> ShelfRequest:
    """Carga un request desde JSON."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    return parse_request_dict(payload)
