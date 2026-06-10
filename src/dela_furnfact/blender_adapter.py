"""Integración opcional con Blender legacy."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import shutil
import subprocess
from typing import Iterable

from dela_furnfact.models import ContentType, ManufacturingPart, OpeningPlan, ProjectBundle
from dela_furnfact.paths import legacy_root as default_legacy_root


class BlenderNotFoundError(FileNotFoundError):
    """No se encontró un ejecutable válido de Blender."""


class LegacyScriptNotFoundError(FileNotFoundError):
    """Falta un script legacy requerido."""


@dataclass(frozen=True)
class LegacyCompatibilityIssue:
    """Problema de compatibilidad con el pipeline legacy."""

    code: str
    message: str
    level: str = "error"


@dataclass(frozen=True)
class LegacyCompatibilityReport:
    """Resultado agregado de compatibilidad legacy."""

    target: str
    issues: tuple[LegacyCompatibilityIssue, ...] = ()

    @property
    def is_supported(self) -> bool:
        return not any(issue.level == "error" for issue in self.issues)

    def errors(self) -> tuple[LegacyCompatibilityIssue, ...]:
        return tuple(issue for issue in self.issues if issue.level == "error")

    def warnings(self) -> tuple[LegacyCompatibilityIssue, ...]:
        return tuple(issue for issue in self.issues if issue.level == "warning")

    def to_dict(self) -> dict:
        return {
            "target": self.target,
            "supported": self.is_supported,
            "issues": [
                {"code": issue.code, "level": issue.level, "message": issue.message}
                for issue in self.issues
            ],
        }

    def summary_text(self) -> str:
        if not self.issues:
            return f"{self.target}: compatible"
        lines = [f"{self.target}: {'compatible' if self.is_supported else 'no compatible'}"]
        lines.extend(f"- [{issue.level}] {issue.code}: {issue.message}" for issue in self.issues)
        return "\n".join(lines)


class LegacyCompatibilityError(ValueError):
    """El bundle no se puede representar de forma fiable en Blender legacy."""

    def __init__(self, report: LegacyCompatibilityReport) -> None:
        self.report = report
        super().__init__(report.summary_text())


@dataclass(frozen=True)
class LegacyRenderResult:
    """Resultado de una ejecución individual de Blender."""

    mode: str
    command: tuple[str, ...]
    payload_path: Path
    output_dir: Path
    stdout: str
    stderr: str
    returncode: int
    generated_files: tuple[Path, ...]

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0


@dataclass(frozen=True)
class LegacyRenderBatch:
    """Conjunto de resultados de render."""

    output_dir: Path
    visual: LegacyRenderResult | None = None
    manufacturing: LegacyRenderResult | None = None

    def generated_files(self) -> tuple[Path, ...]:
        files: list[Path] = []
        if self.visual is not None:
            files.extend(self.visual.generated_files)
        if self.manufacturing is not None:
            files.extend(self.manufacturing.generated_files)
        return tuple(sorted(set(files)))


class BlenderExecutableLocator:
    """Localiza Blender en rutas comunes o mediante PATH."""

    CANDIDATE_NAMES = ("blender", "blender.exe")

    @classmethod
    def find(cls, explicit_path: Path | str | None = None) -> Path | None:
        if explicit_path:
            candidate = Path(explicit_path).expanduser()
            if candidate.exists():
                return candidate.resolve()

        for name in cls.CANDIDATE_NAMES:
            found = shutil.which(name)
            if found:
                return Path(found).resolve()

        candidates = cls._common_install_locations()
        for candidate in candidates:
            if candidate.exists():
                return candidate.resolve()

        return None

    @staticmethod
    def _common_install_locations() -> tuple[Path, ...]:
        return (
            Path("/Applications/Blender.app/Contents/MacOS/Blender"),
            Path("/usr/bin/blender"),
            Path("/usr/local/bin/blender"),
            Path("C:/Program Files/Blender Foundation/Blender/blender.exe"),
            Path("C:/Program Files/Blender Foundation/Blender 4.5/blender.exe"),
            Path("C:/Program Files/Blender Foundation/Blender 4.4/blender.exe"),
            Path("C:/Program Files/Blender Foundation/Blender 4.3/blender.exe"),
            Path("C:/Program Files/Blender Foundation/Blender 4.2/blender.exe"),
            Path("C:/Program Files/Blender Foundation/Blender 4.1/blender.exe"),
            Path("C:/Program Files/Blender Foundation/Blender 4.0/blender.exe"),
            Path("C:/Program Files/Blender Foundation/Blender 3.6/blender.exe"),
        )


class LegacyPayloadBuilder:
    """Genera payloads compatibles con los scripts heredados."""

    VISUAL_BOOK_LABELS = {"books_small", "books_standard", "books_large", "books_general"}
    VISUAL_DVD_LABELS = {"dvds", "dvd_boxsets"}

    def analyze_visual_support(self, bundle: ProjectBundle) -> LegacyCompatibilityReport:
        issues: list[LegacyCompatibilityIssue] = []

        if bundle.plan.columns not in (1, 2):
            issues.append(
                LegacyCompatibilityIssue(
                    code="VIS_001",
                    message=(
                        "El render visual legacy solo soporta 1 o 2 columnas. "
                        f"El plan actual tiene {bundle.plan.columns} columnas."
                    ),
                )
            )

        if len(bundle.plan.openings) != bundle.plan.rows:
            issues.append(
                LegacyCompatibilityIssue(
                    code="VIS_002",
                    message="El pipeline legacy espera una lista lineal de huecos, uno por fila.",
                )
            )

        if bundle.plan.columns == 1 and bundle.request.has_center_divider:
            issues.append(
                LegacyCompatibilityIssue(
                    code="VIS_003",
                    message="El request marca divisor central, pero el solver resolvió una sola columna.",
                    level="warning",
                )
            )

        if any(opening.clear_height_mm <= 0 for opening in bundle.plan.openings):
            issues.append(
                LegacyCompatibilityIssue(
                    code="VIS_004",
                    message="Hay huecos con altura no positiva; Blender legacy no puede representarlos.",
                )
            )

        return LegacyCompatibilityReport(target="visual", issues=tuple(issues))

    def analyze_manufacturing_support(self, bundle: ProjectBundle) -> LegacyCompatibilityReport:
        issues: list[LegacyCompatibilityIssue] = []

        if bundle.plan.columns != 2:
            issues.append(
                LegacyCompatibilityIssue(
                    code="MFG_001",
                    message=(
                        "El póster de fabricación legacy solo soporta un mueble simétrico de 2 columnas "
                        f"con divisor central. El plan actual tiene {bundle.plan.columns} columnas."
                    ),
                )
            )

        if not bundle.plan.has_back_panel:
            issues.append(
                LegacyCompatibilityIssue(
                    code="MFG_002",
                    message="El render de fabricación legacy asume trasera instalada.",
                )
            )

        if bundle.plan.has_back_panel and not bundle.plan.split_back_panel:
            issues.append(
                LegacyCompatibilityIssue(
                    code="MFG_003",
                    message="El render de fabricación legacy asume trasera partida en dos paneles verticales.",
                )
            )

        if bundle.plan.back_panel_thickness_mm <= 0:
            issues.append(
                LegacyCompatibilityIssue(
                    code="MFG_004",
                    message="El render de fabricación legacy necesita una trasera con grosor positivo.",
                )
            )

        divider_parts = [part for part in bundle.manufacturing.parts if part.semantic == "divider"]
        if bundle.plan.columns == 2 and len(divider_parts) != 1:
            issues.append(
                LegacyCompatibilityIssue(
                    code="MFG_005",
                    message="El plan de fabricación legacy espera exactamente un divisor central.",
                )
            )

        return LegacyCompatibilityReport(target="manufacturing", issues=tuple(issues))

    def build_visual_spec(self, bundle: ProjectBundle, include_content: bool = True) -> dict:
        report = self.analyze_visual_support(bundle)
        plan = bundle.plan

        return {
            "project_name": self._slugify(bundle.request.name),
            "type": "bookshelf",
            "units": "mm",
            "overall_dimensions": {
                "width": plan.outer_width_mm,
                "height": plan.outer_height_mm,
                "depth": plan.outer_depth_mm,
            },
            "structure": {
                "board_thickness": plan.board_thickness_mm,
                "side_panels": True,
                "top_panel": True,
                "bottom_panel": True,
            },
            "dividers": {"center": plan.columns == 2},
            "zones": [
                {
                    "type": self._normalize_visual_opening_type(bundle.request.content_type, opening),
                    "count": 1,
                    "clear_height": opening.clear_height_mm,
                    "original_label": opening.label,
                    "source": opening.source,
                }
                for opening in plan.openings
            ],
            "solver": {
                "remaining_distribution": "none",
                "source_distribution": bundle.request.remaining_distribution.value,
            },
            "back_panel": {
                "enabled": plan.has_back_panel,
                "split_vertical_panels": plan.split_back_panel,
                "panel_width": self._back_panel_width(bundle),
                "panel_height": plan.outer_height_mm,
                "thickness": plan.back_panel_thickness_mm,
            },
            "visualization": self._build_visualization_block(bundle.request.content_type, include_content=include_content),
            "legacy_compatibility": report.to_dict(),
        }

    def build_manufacturing_payload(self, bundle: ProjectBundle) -> dict:
        report = self.analyze_manufacturing_support(bundle)
        plan = bundle.plan

        horizontal_length = self._horizontal_length(bundle)
        divider_height = self._divider_height(bundle)

        return {
            "project_name": self._slugify(bundle.request.name),
            "kerf_mm": bundle.request.kerf_mm,
            "cabinet": {
                "type": "dvd_shelf" if bundle.request.content_type is ContentType.DVD else "book_shelf",
                "variant": f"{plan.columns}x{plan.rows}",
                "construction_type": (
                    "laterales continuos + horizontales entre laterales + separador central + "
                    "trasera superpuesta dividida"
                ),
                "internal_horizontal": horizontal_length,
                "horizontal_length": horizontal_length,
                "outer_width": plan.outer_width_mm,
                "height": plan.outer_height_mm,
                "depth": plan.outer_depth_mm,
                "nominal_depth": plan.outer_depth_mm,
                "board_thickness": plan.board_thickness_mm,
                "back_thickness": plan.back_panel_thickness_mm,
                "divider_height": divider_height,
                "section_width": plan.clear_section_width_mm,
                "back_panel_width": self._back_panel_width(bundle),
                "shelf_levels": plan.rows,
                "opening_heights": [opening.clear_height_mm for opening in plan.openings],
            },
            "colors": self._default_colors(),
            "parts": [
                {
                    "name": part.label,
                    "key": part.key,
                    "semantic": part.semantic,
                    "width": part.width_mm,
                    "height": part.height_mm,
                    "thickness": part.thickness_mm,
                    "quantity": part.quantity,
                    "material": part.material,
                }
                for part in bundle.manufacturing.parts
            ],
            "boards": [
                {
                    "name": f"{layout.board.material} #{layout.board_index}",
                    "material": layout.board.material,
                    "width": layout.board.width_mm,
                    "height": layout.board.height_mm,
                    "thickness": layout.board.thickness_mm,
                    "pieces": [
                        {
                            "name": placement.label,
                            "semantic": placement.part_key,
                            "x": placement.x_mm,
                            "y": placement.y_mm,
                            "width": placement.width_mm,
                            "height": placement.height_mm,
                            "rotated": placement.rotated,
                        }
                        for placement in layout.placements
                    ],
                    "cuts": [],
                    "remainders": [],
                }
                for layout in bundle.manufacturing.board_layouts
            ],
            "legacy_compatibility": report.to_dict(),
        }

    def _normalize_visual_opening_type(self, content_type: ContentType, opening: OpeningPlan) -> str:
        label = self._normalize_label(opening.label)

        if content_type is ContentType.DVD:
            if label in self.VISUAL_DVD_LABELS:
                return label
            if any(token in label for token in ("box", "boxset", "coleccion", "colección", "pack", "edicion", "edición")):
                return "dvd_boxsets"
            return "dvd_boxsets" if opening.clear_height_mm >= 235.0 else "dvds"

        if label in self.VISUAL_BOOK_LABELS:
            return label
        if any(token in label for token in ("large", "grande", "atlas", "arte", "album", "álbum", "revistero")):
            return "books_large"
        if any(token in label for token in ("small", "novela", "pocket", "comic", "cómic", "manga")):
            return "books_small"
        return "books_large" if opening.clear_height_mm >= 235.0 else "books_small"

    @staticmethod
    def _build_visualization_block(content_type: ContentType, include_content: bool = True) -> dict:
        return {
            "add_books": include_content and content_type is ContentType.BOOKS,
            "add_dvds": include_content and content_type is ContentType.DVD,
            "gap": 2,
            "dvd_width": 14,
            "dvd_height": 190,
            "dvd_depth": 135,
            "boxset_width": 50,
            "boxset_height": 200,
            "boxset_depth": 135,
            "book_small_width": 20,
            "book_small_height": 200,
            "book_small_depth": 140,
            "book_large_width": 24,
            "book_large_height": 240,
            "book_large_depth": 180,
        }

    @staticmethod
    def _default_colors() -> dict[str, list[float]]:
        return {
            "pine": [0.82, 0.68, 0.46],
            "side": [0.78, 0.61, 0.39],
            "divider": [0.69, 0.53, 0.34],
            "shelf": [0.86, 0.72, 0.50],
            "top_bottom": [0.76, 0.60, 0.38],
            "back": [0.74, 0.74, 0.74],
            "panel": [0.98, 0.98, 0.98],
            "panel_border": [0.78, 0.78, 0.78],
            "text": [0.14, 0.14, 0.14],
            "remaining": [0.86, 0.93, 0.90],
            "kerf": [0.84, 0.18, 0.18],
        }

    @staticmethod
    def _slugify(name: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "_", name.strip().lower())
        return slug.strip("_") or "project"

    @staticmethod
    def _normalize_label(label: str) -> str:
        return re.sub(r"[^a-z0-9_]+", "_", label.strip().lower())

    @staticmethod
    def _find_part(bundle: ProjectBundle, key: str | None = None, semantic: str | None = None) -> ManufacturingPart | None:
        for part in bundle.manufacturing.parts:
            if key is not None and part.key == key:
                return part
            if semantic is not None and part.semantic == semantic:
                return part
        return None

    def _horizontal_length(self, bundle: ProjectBundle) -> float:
        top = self._find_part(bundle, key="top_panel")
        if top is not None:
            return top.width_mm
        return bundle.plan.outer_width_mm - (2 * bundle.plan.board_thickness_mm)

    def _divider_height(self, bundle: ProjectBundle) -> float:
        divider = self._find_part(bundle, semantic="divider")
        if divider is not None:
            return divider.height_mm
        return bundle.plan.outer_height_mm - (2 * bundle.plan.board_thickness_mm)

    def _back_panel_width(self, bundle: ProjectBundle) -> float:
        back = self._find_part(bundle, semantic="back")
        if back is not None:
            return back.width_mm
        return bundle.plan.outer_width_mm / (2 if bundle.plan.split_back_panel else 1)


class LegacyBlenderBridge:
    """Serializa payloads e invoca Blender legacy."""

    def __init__(self, blender_executable: Path | str | None = None, legacy_root: Path | None = None) -> None:
        self.blender_executable = BlenderExecutableLocator.find(blender_executable)
        self.legacy_root = legacy_root or default_legacy_root()
        self.builder = LegacyPayloadBuilder()

    def is_available(self) -> bool:
        return self.blender_executable is not None and self.blender_executable.exists()

    def require_blender(self) -> Path:
        if self.blender_executable is None or not self.blender_executable.exists():
            raise BlenderNotFoundError(
                "No se ha encontrado Blender. Configura la ruta del ejecutable o instala Blender y asegúrate de que "
                "está en PATH."
            )
        return self.blender_executable

    def visual_compatibility(self, bundle: ProjectBundle) -> LegacyCompatibilityReport:
        return self.builder.analyze_visual_support(bundle)

    def manufacturing_compatibility(self, bundle: ProjectBundle) -> LegacyCompatibilityReport:
        return self.builder.analyze_manufacturing_support(bundle)

    def export_visual_payload(self, bundle: ProjectBundle, path: Path, include_content: bool = True) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.builder.build_visual_spec(bundle, include_content=include_content), indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def export_manufacturing_payload(self, bundle: ProjectBundle, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.builder.build_manufacturing_payload(bundle), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    def render_visual(self, bundle: ProjectBundle, output_dir: Path, include_content: bool = True) -> LegacyRenderResult:
        self._ensure_supported(self.visual_compatibility(bundle))
        payload = self.export_visual_payload(bundle, output_dir / "legacy_visual_spec.json", include_content=include_content)
        script = self._resolve_script("blender/generate_bookshelf.py")
        return self._run(mode="visual", script=script, payload=payload, output_dir=output_dir)

    def render_manufacturing(self, bundle: ProjectBundle, output_dir: Path) -> LegacyRenderResult:
        self._ensure_supported(self.manufacturing_compatibility(bundle))
        payload = self.export_manufacturing_payload(bundle, output_dir / "legacy_manufacturing_payload.json")
        script = self._resolve_script("blender/generate_kerf_layout.py")
        return self._run(mode="manufacturing", script=script, payload=payload, output_dir=output_dir)

    def render_all(self, bundle: ProjectBundle, output_dir: Path, include_content: bool = True) -> LegacyRenderBatch:
        self._ensure_supported(self.visual_compatibility(bundle))
        self._ensure_supported(self.manufacturing_compatibility(bundle))
        output_dir.mkdir(parents=True, exist_ok=True)
        visual = self.render_visual(bundle, output_dir / "visual", include_content=include_content)
        manufacturing = self.render_manufacturing(bundle, output_dir / "manufacturing")
        return LegacyRenderBatch(output_dir=output_dir, visual=visual, manufacturing=manufacturing)

    def _ensure_supported(self, report: LegacyCompatibilityReport) -> None:
        if not report.is_supported:
            raise LegacyCompatibilityError(report)

    def _resolve_script(self, relative_path: str) -> Path:
        script = self.legacy_root / relative_path
        if not script.exists():
            raise LegacyScriptNotFoundError(f"Script legacy no encontrado: {script}")
        return script

    def _run(self, mode: str, script: Path, payload: Path, output_dir: Path) -> LegacyRenderResult:
        blender = self.require_blender()
        output_dir.mkdir(parents=True, exist_ok=True)
        command = self._build_command(blender, script, payload, output_dir)
        completed = subprocess.run(command, check=True, capture_output=True, text=True)
        return LegacyRenderResult(
            mode=mode,
            command=tuple(command),
            payload_path=payload,
            output_dir=output_dir,
            stdout=completed.stdout,
            stderr=completed.stderr,
            returncode=completed.returncode,
            generated_files=self._list_output_files(output_dir),
        )

    @staticmethod
    def _build_command(blender: Path, script: Path, payload: Path, output_dir: Path) -> list[str]:
        return [
            str(blender),
            "--background",
            "--python",
            str(script),
            "--",
            str(payload),
            str(output_dir),
        ]

    @staticmethod
    def _list_output_files(output_dir: Path) -> tuple[Path, ...]:
        if not output_dir.exists():
            return tuple()
        files = sorted(path for path in output_dir.rglob("*") if path.is_file())
        return tuple(files)


def flatten_generated_files(paths: Iterable[Path]) -> str:
    """Devuelve una lista legible de archivos generados."""

    return "\n".join(f"- {path}" for path in paths)
