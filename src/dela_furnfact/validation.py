"""Validación sintáctica y semántica del request."""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path
import json

from dela_furnfact.models import (
    ContentType,
    LayoutMode,
    OpeningRequest,
    RemainingDistribution,
    ShelfRequest,
    VisualDistribution,
    ValidationIssue,
)
from dela_furnfact.profiles import expanded_openings, get_profile
from dela_furnfact.opening_catalog import canonical_opening_label


class RequestValidationError(ValueError):
    """Error agregado de validación."""

    def __init__(self, issues: list[ValidationIssue]) -> None:
        self.issues = issues
        super().__init__("\n".join(f"{item.code}: {item.message}" for item in issues))


def parse_request_dict(payload: dict) -> ShelfRequest:
    """Construye un ShelfRequest desde JSON/dict."""

    requested_openings = [
        OpeningRequest(
            label=canonical_opening_label(str(item["label"])),
            count=int(item.get("count", 1)),
            min_clear_height_mm=float(item["min_clear_height_mm"]),
            preferred_clear_height_mm=(
                None
                if item.get("preferred_clear_height_mm") in (None, "")
                else float(item["preferred_clear_height_mm"])
            ),
            max_clear_height_mm=(
                None
                if item.get("max_clear_height_mm") in (None, "")
                else float(item["max_clear_height_mm"])
            ),
            min_clear_width_mm=float(item.get("min_clear_width_mm", 0.0)),
            priority=int(item.get("priority", 3)),
            fixed_height=bool(item.get("fixed_height", False)),
        )
        for item in payload.get("requested_openings", [])
    ]

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
        fixed_columns=None if payload.get("fixed_columns") in (None, "") else int(payload["fixed_columns"]),
        fixed_rows=None if payload.get("fixed_rows") in (None, "") else int(payload["fixed_rows"]),
        allow_auto_fill=bool(payload.get("allow_auto_fill", True)),
        requested_openings=requested_openings,
    )


def load_request(path: Path) -> ShelfRequest:
    """Carga un request desde JSON."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    return parse_request_dict(payload)


def validate_request(request: ShelfRequest) -> list[ValidationIssue]:
    """Valida el request."""

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
            issues.append(ValidationIssue(code=code, message=message))

    if request.board_thickness_mm >= request.depth_mm:
        issues.append(
            ValidationIssue(
                code="REQ_010",
                message="El grosor del tablero debe ser menor que el fondo total.",
            )
        )

    if request.width_mm <= 2 * request.board_thickness_mm:
        issues.append(
            ValidationIssue(
                code="REQ_011",
                message="El ancho total no deja espacio interior útil.",
            )
        )

    if request.height_mm <= 2 * request.board_thickness_mm:
        issues.append(
            ValidationIssue(
                code="REQ_012",
                message="La altura total no deja espacio interior útil.",
            )
        )

    if request.fixed_columns is not None and request.fixed_columns < 1:
        issues.append(ValidationIssue(code="REQ_013", message="Las columnas fijas deben ser >= 1."))

    if request.fixed_rows is not None and request.fixed_rows < 1:
        issues.append(ValidationIssue(code="REQ_014", message="Las filas fijas deben ser >= 1."))

    if request.depth_mm < profile.min_depth_mm:
        issues.append(
            ValidationIssue(
                code="REQ_015",
                message=(
                    f"El fondo ({request.depth_mm:.1f} mm) es menor que el mínimo recomendado "
                    f"para {profile.label} ({profile.min_depth_mm:.1f} mm)."
                ),
            )
        )

    if request.depth_mm < profile.ideal_depth_mm:
        issues.append(
            ValidationIssue(
                code="REQ_016",
                message=(
                    f"El fondo está por debajo del ideal para {profile.label}. "
                    "Puede ser válido, pero conviene revisarlo."
                ),
                level="warning",
            )
        )

    expanded = expanded_openings(request)
    if request.fixed_rows is not None and len(expanded) > request.fixed_rows:
        issues.append(
            ValidationIssue(
                code="REQ_017",
                message="Hay más huecos requeridos que filas fijas disponibles.",
            )
        )

    if not request.allow_auto_fill and request.fixed_rows is None and request.requested_openings:
        issues.append(
            ValidationIssue(
                code="REQ_018",
                message="Si no hay auto-fill, debes fijar el número de filas.",
            )
        )

    for index, item in enumerate(expanded, start=1):
        if item.count != 1:
            issues.append(
                ValidationIssue(
                    code="REQ_019",
                    message=f"El hueco #{index} debe venir expandido internamente con count=1.",
                )
            )
        if item.min_clear_height_mm <= 0:
            issues.append(
                ValidationIssue(
                    code="REQ_020",
                    message=f"El hueco #{index} debe tener altura útil mínima > 0.",
                )
            )
        if item.min_clear_width_mm < 0:
            issues.append(
                ValidationIssue(
                    code="REQ_021",
                    message=f"El hueco #{index} no puede tener anchura mínima negativa.",
                )
            )
        if item.preferred_clear_height_mm is not None and item.preferred_clear_height_mm < item.min_clear_height_mm:
            issues.append(
                ValidationIssue(
                    code="REQ_022",
                    message=f"El hueco #{index} tiene una altura preferida menor que la mínima.",
                )
            )

        if item.max_clear_height_mm is not None and item.max_clear_height_mm < item.min_clear_height_mm:
            issues.append(
                ValidationIssue(
                    code="REQ_026",
                    message=f"El hueco #{index} tiene una altura máxima menor que la mínima.",
                )
            )
        if (
            item.preferred_clear_height_mm is not None
            and item.max_clear_height_mm is not None
            and item.preferred_clear_height_mm > item.max_clear_height_mm
        ):
            issues.append(
                ValidationIssue(
                    code="REQ_027",
                    message=f"El hueco #{index} tiene una altura preferida mayor que la máxima.",
                )
            )
        if item.priority < 1 or item.priority > 5:
            issues.append(
                ValidationIssue(
                    code="REQ_028",
                    message=f"El hueco #{index} debe tener prioridad entre 1 y 5.",
                )
            )
        if item.fixed_height and item.preferred_clear_height_mm is None:
            issues.append(
                ValidationIssue(
                    code="REQ_029",
                    message=f"El hueco #{index} marcado como fijo necesita una altura preferida o exacta.",
                )
            )

    internal_height_mm = request.height_mm - (2 * request.board_thickness_mm)
    required_rows = max(len(expanded), 1)
    estimated_rows = request.fixed_rows or required_rows
    usable_height_mm = internal_height_mm - max(estimated_rows - 1, 0) * request.board_thickness_mm
    required_height_mm = sum(item.min_clear_height_mm for item in expanded)

    if required_height_mm > usable_height_mm and expanded:
        issues.append(
            ValidationIssue(
                code="REQ_023",
                message=(
                    f"Los huecos mínimos pedidos necesitan {required_height_mm:.1f} mm, "
                    f"pero solo hay {usable_height_mm:.1f} mm útiles con la configuración actual."
                ),
            )
        )
    fixed_target_height_mm = sum(
        item.target_height_mm for item in expanded if item.fixed_height
    )
    if fixed_target_height_mm > usable_height_mm and expanded:
        issues.append(
            ValidationIssue(
                code="REQ_030",
                message=(
                    f"Los huecos con altura fija necesitan {fixed_target_height_mm:.1f} mm, "
                    f"pero solo hay {usable_height_mm:.1f} mm útiles con la configuración actual."
                ),
            )
        )

    if request.fixed_columns is not None:
        divider_count = max(request.fixed_columns - 1, 0)
        usable_width_mm = request.width_mm - (2 * request.board_thickness_mm) - divider_count * request.board_thickness_mm
        section_width_mm = usable_width_mm / request.fixed_columns
        too_wide = [item for item in expanded if item.min_clear_width_mm > section_width_mm]
        if too_wide:
            issues.append(
                ValidationIssue(
                    code="REQ_024",
                    message=(
                        f"Hay huecos que requieren más anchura útil que la sección disponible "
                        f"({section_width_mm:.1f} mm)."
                    ),
                )
            )

    if request.has_center_divider and request.fixed_columns == 1:
        issues.append(
            ValidationIssue(
                code="REQ_025",
                message="No tiene sentido pedir divisor central con una sola columna fija.",
                level="warning",
            )
        )

    return issues


def raise_for_errors(issues: list[ValidationIssue]) -> None:
    """Lanza si existe al menos un error."""

    errors = [issue for issue in issues if issue.level == "error"]
    if errors:
        raise RequestValidationError(errors)
