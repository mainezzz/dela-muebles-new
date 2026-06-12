from __future__ import annotations

from dataclasses import dataclass

from math import floor
from dela_furnfact.models import (
    LayoutCandidate,
    LayoutMode,
    OpeningPlan,
    OpeningRequest,
    RemainingDistribution,
    ShelfPlan,
    ShelfRequest,
    VisualDistribution,
)
from dela_furnfact.profiles import candidate_columns, candidate_rows, default_auto_opening, expanded_openings, get_profile

@dataclass
class CandidateRejection:
    """Motivo de descarte de un candidato del solver."""

    code: str
    message: str
    columns: int
    rows: int

__all__ = ["CandidateRejection"]
