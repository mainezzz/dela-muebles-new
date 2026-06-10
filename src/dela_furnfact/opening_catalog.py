"""Catálogo explícito de tipos de hueco de DELA.

Fase 3 de v13:
- evita trabajar con strings sueltos repartidos por GUI, solver y validación
- define un catálogo central con ids, labels visibles y medidas base
- permite crecer luego a manga, vinilo, arte, etc.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable

from dela_furnfact.models import ContentType, OpeningRequest


class OpeningTypeId(StrEnum):
    """Ids estables para los tipos de hueco soportados actualmente."""

    DVD = "dvd"
    BOXSET = "boxset"
    BOOK_SMALL = "books_small"
    BOOK_LARGE = "books_large"


@dataclass(frozen=True)
class OpeningTypeSpec:
    """Especificación de un tipo de hueco reutilizable."""

    id: OpeningTypeId
    canonical_label: str
    display_label: str
    short_label: str
    content_type: ContentType
    kind: str
    min_clear_height_mm: float
    preferred_clear_height_mm: float | None
    max_clear_height_mm: float | None
    fixed_height: bool
    default_count: int = 1
    aliases: tuple[str, ...] = ()


OPENING_TYPE_CATALOG: dict[OpeningTypeId, OpeningTypeSpec] = {
    OpeningTypeId.DVD: OpeningTypeSpec(
        id=OpeningTypeId.DVD,
        canonical_label="dvd",
        display_label="DVD",
        short_label="DVD",
        content_type=ContentType.DVD,
        kind="dvd",
        min_clear_height_mm=205.0,
        preferred_clear_height_mm=205.0,
        max_clear_height_mm=205.0,
        fixed_height=True,
        aliases=("dvds", "dvd normal", "dvd normales", "dvd standard", "dvd estándar"),
    ),
    OpeningTypeId.BOXSET: OpeningTypeSpec(
        id=OpeningTypeId.BOXSET,
        canonical_label="boxset",
        display_label="BOXSET",
        short_label="BOXSET",
        content_type=ContentType.DVD,
        kind="boxset",
        min_clear_height_mm=235.0,
        preferred_clear_height_mm=255.0,
        max_clear_height_mm=320.0,
        fixed_height=False,
        aliases=("boxsets", "dvd boxset", "dvd boxsets", "dvd_boxsets"),
    ),
    OpeningTypeId.BOOK_SMALL: OpeningTypeSpec(
        id=OpeningTypeId.BOOK_SMALL,
        canonical_label="books_small",
        display_label="NOVELA PEQUEÑA",
        short_label="PEQUEÑOS",
        content_type=ContentType.BOOKS,
        kind="small_book",
        min_clear_height_mm=210.0,
        preferred_clear_height_mm=214.0,
        max_clear_height_mm=220.0,
        fixed_height=False,
        aliases=(
            "novela pequeña",
            "libro pequeño",
            "libros pequeños",
            "books small",
            "pequeña",
            "pequeños",
        ),
    ),
    OpeningTypeId.BOOK_LARGE: OpeningTypeSpec(
        id=OpeningTypeId.BOOK_LARGE,
        canonical_label="books_large",
        display_label="NOVELA GRANDE",
        short_label="GRANDES",
        content_type=ContentType.BOOKS,
        kind="large_book",
        min_clear_height_mm=249.0,
        preferred_clear_height_mm=256.0,
        max_clear_height_mm=270.0,
        fixed_height=False,
        aliases=(
            "novela grande",
            "libro grande",
            "libros grandes",
            "books large",
            "grande",
            "grandes",
        ),
    ),
}


_ALIAS_INDEX: dict[str, OpeningTypeSpec] = {}
for spec in OPENING_TYPE_CATALOG.values():
    _ALIAS_INDEX[spec.canonical_label] = spec
    _ALIAS_INDEX[spec.id.value] = spec
    for alias in spec.aliases:
        _ALIAS_INDEX[alias.strip().lower().replace("_", " ")] = spec


def _normalize(label: str) -> str:
    return label.strip().lower().replace("_", " ")


def get_opening_type_spec(label: str | OpeningTypeId) -> OpeningTypeSpec | None:
    """Busca un spec por id, label canónico o alias."""

    key = label.value if isinstance(label, OpeningTypeId) else str(label)
    return _ALIAS_INDEX.get(_normalize(key))


def canonical_opening_label(label: str | OpeningTypeId) -> str:
    """Devuelve el label canónico interno de un tipo conocido."""

    spec = get_opening_type_spec(label)
    if spec is None:
        return _normalize(str(label))
    return spec.canonical_label


def opening_type_choices(content_type: ContentType) -> tuple[OpeningTypeSpec, ...]:
    """Lista ordenada de tipos disponibles para un contenido dado."""

    ordered_ids = (
        (OpeningTypeId.DVD, OpeningTypeId.BOXSET)
        if content_type is ContentType.DVD
        else (OpeningTypeId.BOOK_SMALL, OpeningTypeId.BOOK_LARGE)
    )
    return tuple(OPENING_TYPE_CATALOG[item] for item in ordered_ids)


def opening_request_from_type(
    opening_type: str | OpeningTypeId,
    *,
    count: int = 1,
) -> OpeningRequest:
    """Crea un OpeningRequest a partir del catálogo."""

    spec = get_opening_type_spec(opening_type)
    if spec is None:
        raise KeyError(f"Tipo de hueco desconocido: {opening_type!r}")

    return OpeningRequest(
        label=spec.canonical_label,
        count=count,
        min_clear_height_mm=spec.min_clear_height_mm,
        preferred_clear_height_mm=spec.preferred_clear_height_mm,
        max_clear_height_mm=spec.max_clear_height_mm,
        fixed_height=spec.fixed_height,
    )


def summarize_catalog_mix(labels: Iterable[str]) -> str:
    """Resume un mix de labels usando el catálogo."""

    counts: dict[str, int] = {}
    order: list[str] = []
    for label in labels:
        spec = get_opening_type_spec(label)
        display = spec.short_label if spec is not None else str(label).upper()
        if display not in counts:
            order.append(display)
            counts[display] = 0
        counts[display] += 1
    if not order:
        return "—"
    return " · ".join(f"{counts[label]} {label}" for label in order)
