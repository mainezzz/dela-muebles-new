"""Servicio principal de aplicación."""

from __future__ import annotations

from dataclasses import replace

from dela_furnfact.layout import SimpleBoardLayouter
from dela_furnfact.manufacturing import ManufacturingGenerator
from dela_furnfact.models import ManufacturingPlan, ProjectBundle, ShelfRequest
from dela_furnfact.solver import ShelfPlanner
from dela_furnfact.validation import raise_for_errors, validate_request


class FurnFactApplicationService:
    """Orquesta validación, solver y fabricación."""

    def generate(self, request: ShelfRequest) -> ProjectBundle:
        issues = validate_request(request)
        raise_for_errors(issues)

        plan = ShelfPlanner().solve(request)

        warnings = [issue.message for issue in issues if issue.level == "warning"]
        if warnings:
            plan = replace(plan, warnings=tuple([*plan.warnings, *warnings]))

        parts = ManufacturingGenerator().build_parts(plan)
        layouts = SimpleBoardLayouter(kerf_mm=request.kerf_mm).layout(parts)
        manufacturing = ManufacturingPlan(parts=parts, board_layouts=layouts, kerf_mm=request.kerf_mm)

        return ProjectBundle(request=request, plan=plan, manufacturing=manufacturing)
