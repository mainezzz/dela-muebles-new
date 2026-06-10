"""Exportadores del bundle del proyecto."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
import json
from pathlib import Path
from typing import Any

from dela_furnfact.models import ProjectBundle


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {key: _to_jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(item) for item in value]
    return value


class JsonExporter:
    """Exportador legible a JSON."""

    def dumps(self, bundle: ProjectBundle) -> str:
        return json.dumps(_to_jsonable(bundle), indent=2, ensure_ascii=False)

    def write(self, bundle: ProjectBundle, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.dumps(bundle), encoding="utf-8")
        return path
