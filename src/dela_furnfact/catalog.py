from __future__ import annotations

"""Public wrapper around the DELA opening catalog.

This module consolidates the explicit opening-type catalogue introduced in v13.
It exposes a stable API for the rest of the application and for tests/docs:
- retrieve a type by id
- list the valid types for a content family
- build default opening requests
- summarize mixes
"""

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from dela_furnfact.models import ContentType, OpeningRequest
from dela_furnfact.opening_catalog import (
    OpeningTypeSpec as _LegacyOpeningTypeSpec,
    get_opening_type_spec,
    opening_request_from_type,
    opening_type_choices,
)


@dataclass(frozen=True)
class OpeningTypeSpec:
    type_id: str
    content_type: str
    label: str
    preview_label: str
    preferred_height_mm: int
    min_height_mm: int
    max_height_mm: int | None
    fixed_height: bool

    @classmethod
    def from_legacy(cls, spec: _LegacyOpeningTypeSpec) -> "OpeningTypeSpec":
        preferred = spec.preferred_clear_height_mm or spec.min_clear_height_mm
        max_height = int(spec.max_clear_height_mm) if spec.max_clear_height_mm is not None else None
        return cls(
            type_id=str(spec.id),
            content_type=spec.content_type.value,
            label=spec.display_label,
            preview_label=spec.short_label,
            preferred_height_mm=int(round(preferred)),
            min_height_mm=int(round(spec.min_clear_height_mm)),
            max_height_mm=max_height,
            fixed_height=spec.fixed_height,
        )


def get_opening_type(type_id: str) -> OpeningTypeSpec:
    spec = get_opening_type_spec(type_id)
    if spec is None:
        raise ValueError(f"Tipo de hueco desconocido: {type_id}")
    return OpeningTypeSpec.from_legacy(spec)


def catalog_for_content(content_type: str | ContentType) -> list[OpeningTypeSpec]:
    enum_value = content_type if isinstance(content_type, ContentType) else ContentType(str(content_type))
    return [OpeningTypeSpec.from_legacy(spec) for spec in opening_type_choices(enum_value)]


def default_opening_request(type_id: str, quantity: int = 1) -> OpeningRequest:
    return opening_request_from_type(type_id, count=quantity)


def mix_summary(type_ids: Iterable[str]) -> str:
    counts: Counter[str] = Counter(type_ids)
    parts: list[str] = []
    for type_id, count in counts.items():
        parts.append(f"{count} {get_opening_type(type_id).preview_label}")
    return " · ".join(parts)
