"""Reglas por tipo de contenido."""

from __future__ import annotations

from dela_furnfact.models import ContentType, LayoutMode, OpeningRequest, ShelfRequest, StorageProfile


PROFILES: dict[ContentType, StorageProfile] = {
    ContentType.BOOKS: StorageProfile(
        content_type=ContentType.BOOKS,
        label="Libros",
        min_clear_height_mm=210.0,
        ideal_clear_height_mm=250.0,
        min_depth_mm=230.0,
        ideal_depth_mm=300.0,
        width_per_item_mm=28.0,
        preferred_columns=(2, 3),
        preferred_rows=(3, 4, 5),
        max_section_width_mm=800.0,
        default_opening_label="books_general",
    ),
    ContentType.DVD: StorageProfile(
        content_type=ContentType.DVD,
        label="DVD",
        min_clear_height_mm=190.0,
        ideal_clear_height_mm=205.0,
        min_depth_mm=170.0,
        ideal_depth_mm=200.0,
        width_per_item_mm=15.0,
        preferred_columns=(2, 3, 4),
        preferred_rows=(6, 7, 8),
        max_section_width_mm=650.0,
        default_opening_label="dvds",
    ),
}


def get_profile(content_type: ContentType) -> StorageProfile:
    """Obtiene el perfil del contenido."""

    return PROFILES[content_type]


def expanded_openings(request: ShelfRequest) -> list[OpeningRequest]:
    """Expande las peticiones repetidas en peticiones unitarias."""

    items: list[OpeningRequest] = []
    for item in request.requested_openings:
        items.extend(item.expanded())
    return items


def candidate_columns(request: ShelfRequest) -> list[int]:
    """Rango de columnas candidatas."""

    if request.fixed_columns is not None:
        return [request.fixed_columns]

    profile = get_profile(request.content_type)
    min_columns = 2 if request.has_center_divider else 1
    max_columns = max(profile.preferred_columns[-1] + 1, min_columns)
    return list(range(min_columns, max_columns + 1))


def candidate_rows(request: ShelfRequest) -> list[int]:
    """Rango de filas candidatas."""

    required_rows = max(len(expanded_openings(request)), 1)
    if request.fixed_rows is not None:
        return [request.fixed_rows]

    profile = get_profile(request.content_type)
    preferred_max = profile.preferred_rows[-1]
    minimum = max(required_rows, profile.preferred_rows[0] - 1, 1)

    if request.layout_mode is LayoutMode.DENSE:
        maximum = max(preferred_max + 2, required_rows)
    elif request.layout_mode is LayoutMode.BALANCED:
        maximum = max(preferred_max + 1, required_rows)
    else:
        maximum = max(preferred_max, required_rows + 1)

    return list(range(minimum, maximum + 1))


def default_auto_opening(profile: StorageProfile) -> OpeningRequest:
    """Hueco automático por defecto."""

    return OpeningRequest(
        label=profile.default_opening_label,
        count=1,
        min_clear_height_mm=profile.min_clear_height_mm,
        preferred_clear_height_mm=profile.ideal_clear_height_mm,
        min_clear_width_mm=0.0,
        priority=3,
    )
