"""Reglas de validaci?n del request."""

from __future__ import annotations

from collections.abc import Sequence

from dela_furnfact._validation_errors import RequestValidationError
from dela_furnfact.models import OpeningRequest, ShelfRequest, ValidationIssue
from dela_furnfact.profiles import expanded_openings, get_profile


def _issue(code: str, message: str, *, level: str = "error") -> ValidationIssue:
    return ValidationIssue(code=code, message=message, level=level)


def _validate_basic_request_rules(request: ShelfRequest) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    profile = get_profile(request.content_type)

    numeric_rules = (
        ("REQ_001", request.width_mm > 0, "El ancho debe ser mayor que cero."),
        ("REQ_002", request.height_mm > 0, "La altura debe ser mayor que cero."),
        ("REQ_003", request.depth_mm > 0, "La profundidad debe ser mayor que cero."),
        ("REQ_004", request.board_thickness_mm > 0, "El grosor del tablero debe ser mayor que cero."),
        ("REQ_005", request.back_panel_thickness_mm >= 0, "El grosor de la trasera no puede ser negativo."),
        ("REQ_006", request.kerf_mm >= 0, "El kerf no puede ser negativo."),
        ("REQ_007", request.units == "mm", "Las unidades soportadas son mm."),
        ("REQ_008", bool(request.name.strip()), "El proyecto debe tener nombre."),
        ("REQ_009", request.content_quantity >= 0, "La cantidad de contenido no puede ser negativa."),
    )

    for code, ok, message in numeric_rules:
        if not ok:
            issues.append(_issue(code, message))

    if request.board_thickness_mm >= request.depth_mm:
        issues.append(_issue("REQ_010", "El grosor del tablero debe ser menor que el fondo total."))

    if request.width_mm <= 2 * request.board_thickness_mm:
        issues.append(_issue("REQ_011", "El ancho total no deja espacio interior ?til."))

    if request.height_mm <= 2 * request.board_thickness_mm:
        issues.append(_issue("REQ_012", "La altura total no deja espacio interior ?til."))

    if request.fixed_columns is not None and request.fixed_columns < 1:
        issues.append(_issue("REQ_013", "Las columnas fijas deben ser >= 1."))

    if request.fixed_rows is not None and request.fixed_rows < 1:
        issues.append(_issue("REQ_014", "Las filas fijas deben ser >= 1."))

    if request.depth_mm < profile.min_depth_mm:
        issues.append(
            _issue(
                "REQ_015",
                (
                    f"El fondo ({request.depth_mm:.1f} mm) es menor que el m?nimo recomendado "
                    f"para {profile.label} ({profile.min_depth_mm:.1f} mm)."
                ),
            )
        )

    if request.depth_mm < profile.ideal_depth_mm:
        issues.append(
            _issue(
                "REQ_016",
                f"El fondo est? por debajo del ideal para {profile.label}. Puede ser v?lido, pero conviene revisarlo.",
                level="warning",
            )
        )

    return issues


def _validate_opening_collection_rules(
    request: ShelfRequest,
    expanded: Sequence[OpeningRequest],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if request.fixed_rows is not None and len(expanded) > request.fixed_rows:
        issues.append(_issue("REQ_017", "Hay m?s huecos requeridos que filas fijas disponibles."))

    if not request.allow_auto_fill and request.fixed_rows is None and request.requested_openings:
        issues.append(_issue("REQ_018", "Si no hay auto-fill, debes fijar el n?mero de filas."))

    return issues


def _validate_opening_item(index: int, item: OpeningRequest) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if item.count != 1:
        issues.append(_issue("REQ_019", f"El hueco #{index} debe venir expandido internamente con count=1."))

    if item.min_clear_height_mm <= 0:
        issues.append(_issue("REQ_020", f"El hueco #{index} debe tener altura ?til m?nima > 0."))

    if item.min_clear_width_mm < 0:
        issues.append(_issue("REQ_021", f"El hueco #{index} no puede tener anchura m?nima negativa."))

    if (
        item.preferred_clear_height_mm is not None
        and item.preferred_clear_height_mm < item.min_clear_height_mm
    ):
        issues.append(_issue("REQ_022", f"El hueco #{index} tiene una altura preferida menor que la m?nima."))

    if item.max_clear_height_mm is not None and item.max_clear_height_mm < item.min_clear_height_mm:
        issues.append(_issue("REQ_026", f"El hueco #{index} tiene una altura m?xima menor que la m?nima."))

    if (
        item.preferred_clear_height_mm is not None
        and item.max_clear_height_mm is not None
        and item.preferred_clear_height_mm > item.max_clear_height_mm
    ):
        issues.append(_issue("REQ_027", f"El hueco #{index} tiene una altura preferida mayor que la m?xima."))

    if item.priority < 1 or item.priority > 5:
        issues.append(_issue("REQ_028", f"El hueco #{index} debe tener prioridad entre 1 y 5."))

    if item.fixed_height and item.preferred_clear_height_mm is None:
        issues.append(
            _issue(
                "REQ_029",
                f"El hueco #{index} marcado como fijo necesita una altura preferida o exacta.",
            )
        )

    return issues


def _validate_opening_items(expanded: Sequence[OpeningRequest]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    for index, item in enumerate(expanded, start=1):
        issues.extend(_validate_opening_item(index, item))

    return issues


def _validate_height_capacity(
    request: ShelfRequest,
    expanded: Sequence[OpeningRequest],
) -> list[ValidationIssue]:
    if not expanded:
        return []

    issues: list[ValidationIssue] = []

    internal_height_mm = request.height_mm - (2 * request.board_thickness_mm)
    required_rows = max(len(expanded), 1)
    estimated_rows = request.fixed_rows or required_rows
    usable_height_mm = internal_height_mm - max(estimated_rows - 1, 0) * request.board_thickness_mm

    required_height_mm = sum(item.min_clear_height_mm for item in expanded)
    if required_height_mm > usable_height_mm:
        issues.append(
            _issue(
                "REQ_023",
                (
                    f"Los huecos m?nimos pedidos necesitan {required_height_mm:.1f} mm, "
                    f"pero solo hay {usable_height_mm:.1f} mm ?tiles con la configuraci?n actual."
                ),
            )
        )

    fixed_target_height_mm = sum(item.target_height_mm for item in expanded if item.fixed_height)
    if fixed_target_height_mm > usable_height_mm:
        issues.append(
            _issue(
                "REQ_030",
                (
                    f"Los huecos con altura fija necesitan {fixed_target_height_mm:.1f} mm, "
                    f"pero solo hay {usable_height_mm:.1f} mm ?tiles con la configuraci?n actual."
                ),
            )
        )

    return issues


def _validate_column_constraints(
    request: ShelfRequest,
    expanded: Sequence[OpeningRequest],
) -> list[ValidationIssue]:
    if request.fixed_columns is None:
        return []

    issues: list[ValidationIssue] = []

    divider_count = max(request.fixed_columns - 1, 0)
    usable_width_mm = request.width_mm - (2 * request.board_thickness_mm) - divider_count * request.board_thickness_mm
    section_width_mm = usable_width_mm / request.fixed_columns

    too_wide = [item for item in expanded if item.min_clear_width_mm > section_width_mm]
    if too_wide:
        issues.append(
            _issue(
                "REQ_024",
                (
                    f"Hay huecos que requieren m?s anchura ?til que la secci?n disponible "
                    f"({section_width_mm:.1f} mm)."
                ),
            )
        )

    if request.has_center_divider and request.fixed_columns == 1:
        issues.append(
            _issue(
                "REQ_025",
                "No tiene sentido pedir divisor central con una sola columna fija.",
                level="warning",
            )
        )

    return issues


def validate_request(request: ShelfRequest) -> list[ValidationIssue]:
    """Valida el request."""

    expanded = expanded_openings(request)

    issues: list[ValidationIssue] = []
    issues.extend(_validate_basic_request_rules(request))
    issues.extend(_validate_opening_collection_rules(request, expanded))
    issues.extend(_validate_opening_items(expanded))
    issues.extend(_validate_height_capacity(request, expanded))
    issues.extend(_validate_column_constraints(request, expanded))
    return issues


def raise_for_errors(issues: list[ValidationIssue]) -> None:
    """Lanza si existe al menos un error."""

    errors = [issue for issue in issues if issue.level == "error"]
    if errors:
        raise RequestValidationError(errors)
