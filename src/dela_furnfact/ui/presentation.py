"""Helpers de presentación para la GUI de DELA.

Este módulo centraliza las transformaciones entre labels de dominio
y el texto mostrado en GUI/preview.
"""

from __future__ import annotations

from collections import Counter
from typing import Iterable

from dela_furnfact.models import OpeningRequest
from dela_furnfact.opening_catalog import get_opening_type_spec


def normalize_opening_label(label: str) -> str:
    """Normaliza una etiqueta de hueco para comparación interna."""
    return label.strip().lower().replace("_", " ")


def display_opening_label(label: str, short: bool = False) -> str:
    """Devuelve el label legible que debe ver el usuario."""
    spec = get_opening_type_spec(label)
    if spec is not None:
        return spec.short_label if short else spec.display_label

    normalized = normalize_opening_label(label)
    return normalized.upper()


def opening_kind(label: str) -> str:
    """Clasifica una etiqueta en un tipo visual para la preview."""
    spec = get_opening_type_spec(label)
    if spec is not None:
        return spec.kind
    return "generic"


def summarize_opening_mix(requested_openings: Iterable[OpeningRequest]) -> str:
    """Agrupa el mix de tipos evitando cadenas repetitivas del tipo '1 DVD · 1 DVD'."""
    counter: Counter[str] = Counter()
    order: list[str] = []
    for opening in requested_openings:
        short_label = display_opening_label(opening.label, short=True)
        if short_label not in counter:
            order.append(short_label)
        counter[short_label] += opening.count
    if not order:
        return "—"
    return " · ".join(f"{counter[label]} {label}" for label in order)
