"""Tipos de error de validaci?n."""

from __future__ import annotations

from dela_furnfact.models import ValidationIssue


class RequestValidationError(ValueError):
    """Error agregado de validaci?n."""

    def __init__(self, issues: list[ValidationIssue]) -> None:
        self.issues = issues
        super().__init__("\n".join(f"{item.code}: {item.message}" for item in issues))
