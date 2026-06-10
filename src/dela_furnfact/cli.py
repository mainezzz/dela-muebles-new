"""CLI principal del producto."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from dela_furnfact import __version__
from dela_furnfact.application import FurnFactApplicationService
from dela_furnfact.blender_adapter import (
    BlenderExecutableLocator,
    LegacyBlenderBridge,
    LegacyCompatibilityError,
    flatten_generated_files,
)
from dela_furnfact.exporters import JsonExporter
from dela_furnfact.gui import launch_gui
from dela_furnfact.help_text import APP_HELP_TEXT, request_template_text
from dela_furnfact.models import ContentType, LayoutMode, OpeningRequest, RemainingDistribution, ShelfRequest, VisualDistribution
from dela_furnfact.paths import default_render_output_root, docs_root, runtime_root, schema_path, user_data_root
from dela_furnfact.validation import load_request


def build_demo_request(content: ContentType) -> ShelfRequest:
    if content is ContentType.DVD:
        return ShelfRequest(
            name="Demo DVD",
            width_mm=2036.0,
            height_mm=2000.0,
            depth_mm=200.0,
            board_thickness_mm=18.0,
            back_panel_thickness_mm=5.0,
            content_type=ContentType.DVD,
            content_quantity=400,
            layout_mode=LayoutMode.DENSE,
            remaining_distribution=RemainingDistribution.TOP_BOTTOM_LARGE,
            visual_distribution=VisualDistribution.TOP_BOTTOM_LARGE,
            fixed_columns=2,
            requested_openings=[
                OpeningRequest(label="dvd_boxsets", count=1, min_clear_height_mm=255.0, preferred_clear_height_mm=255.0),
                OpeningRequest(label="dvds", count=6, min_clear_height_mm=205.0, preferred_clear_height_mm=205.0),
                OpeningRequest(label="dvd_boxsets", count=1, min_clear_height_mm=255.0, preferred_clear_height_mm=255.0),
            ],
        )

    return ShelfRequest(
        name="Demo Libros",
        width_mm=1636.0,
        height_mm=2000.0,
        depth_mm=300.0,
        board_thickness_mm=18.0,
        back_panel_thickness_mm=5.0,
        content_type=ContentType.BOOKS,
        content_quantity=220,
        layout_mode=LayoutMode.BALANCED,
        remaining_distribution=RemainingDistribution.UNIFORM,
            visual_distribution=VisualDistribution.MIXED,
        fixed_columns=2,
        requested_openings=[
            OpeningRequest(label="books_large", count=1, min_clear_height_mm=249.0, preferred_clear_height_mm=249.0),
            OpeningRequest(label="books_small", count=2, min_clear_height_mm=210.0, preferred_clear_height_mm=210.0),
            OpeningRequest(label="books_large", count=2, min_clear_height_mm=249.0, preferred_clear_height_mm=249.0),
            OpeningRequest(label="books_small", count=2, min_clear_height_mm=211.0, preferred_clear_height_mm=211.0),
            OpeningRequest(label="books_large", count=1, min_clear_height_mm=249.0, preferred_clear_height_mm=249.0),
        ],
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="furnfact", description="Configurador DELA de estanterías.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser("demo", help="Genera una demo rápida.")
    demo.add_argument("--content", choices=[item.value for item in ContentType], default=ContentType.BOOKS.value)
    demo.add_argument("--output", type=Path)

    generate = subparsers.add_parser("generate", help="Genera bundle desde JSON.")
    generate.add_argument("--input", type=Path, required=True)
    generate.add_argument("--output", type=Path, required=True)

    render = subparsers.add_parser("render", help="Genera bundle y lanza Blender legacy.")
    render.add_argument("--input", type=Path, required=True, help="Request JSON de entrada.")
    render.add_argument("--output-dir", type=Path, default=default_render_output_root() / "render_cli")
    render.add_argument("--bundle-output", type=Path, help="Ruta opcional para guardar el bundle JSON.")
    render.add_argument("--blender", type=Path, help="Ruta explícita al ejecutable de Blender.")
    render.add_argument(
        "--mode",
        choices=["visual", "manufacturing", "all"],
        default="all",
        help="Qué pipeline de Blender ejecutar.",
    )

    schema = subparsers.add_parser("schema", help="Muestra la ruta del schema JSON.")
    schema.add_argument("--path-only", action="store_true")

    docs = subparsers.add_parser("docs", help="Muestra la documentación disponible.")
    docs.add_argument("--path-only", action="store_true")

    template = subparsers.add_parser("template", help="Imprime o guarda un request JSON de ejemplo.")
    template.add_argument("--output", type=Path)

    help_cmd = subparsers.add_parser("helptext", help="Imprime ayuda embebida del producto.")

    subparsers.add_parser("version", help="Imprime la versión del paquete.")
    doctor = subparsers.add_parser("doctor", help="Comprueba rutas y dependencias locales.")
    doctor.add_argument("--blender", type=Path, help="Ruta explícita al ejecutable de Blender.")

    subparsers.add_parser("gui", help="Abre la interfaz gráfica PySide6.")

    return parser


def _run_and_export(request: ShelfRequest, output: Path | None) -> int:
    bundle = FurnFactApplicationService().generate(request)
    text = "\n".join(bundle.summary_lines())
    print(text)
    if output is not None:
        JsonExporter().write(bundle, output)
        print(f"\nJSON -> {output}")
    return 0



def _doctor(blender_path: Path | None) -> int:
    print(f"dela-furnfact {__version__}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Runtime root: {runtime_root()}")
    print(f"User data root: {user_data_root()}")
    print(f"Docs root: {docs_root()}")
    print(f"Schema: {schema_path()}")
    blender = BlenderExecutableLocator.find(blender_path)
    print(f"Blender: {blender if blender else 'NO ENCONTRADO'}")
    return 0


def _render_request(
    request: ShelfRequest,
    output_dir: Path,
    bundle_output: Path | None,
    blender_path: Path | None,
    mode: str,
) -> int:
    service = FurnFactApplicationService()
    bundle = service.generate(request)
    print("\n".join(bundle.summary_lines()))

    if bundle_output is not None:
        JsonExporter().write(bundle, bundle_output)
        print(f"\nBundle JSON -> {bundle_output}")

    bridge = LegacyBlenderBridge(blender_executable=blender_path)
    try:
        if mode == "visual":
            print(f"\nCompatibilidad visual legacy: {bridge.visual_compatibility(bundle).summary_text()}")
            result = bridge.render_visual(bundle, output_dir / "visual")
            print(f"\nRender visual -> {result.output_dir}")
            if result.generated_files:
                print(flatten_generated_files(result.generated_files))
            return 0

        if mode == "manufacturing":
            print(
                f"\nCompatibilidad fabricación legacy: "
                f"{bridge.manufacturing_compatibility(bundle).summary_text()}"
            )
            result = bridge.render_manufacturing(bundle, output_dir / "manufacturing")
            print(f"\nRender fabricación -> {result.output_dir}")
            if result.generated_files:
                print(flatten_generated_files(result.generated_files))
            return 0

        print(f"\nCompatibilidad visual legacy: {bridge.visual_compatibility(bundle).summary_text()}")
        print(f"\nCompatibilidad fabricación legacy: {bridge.manufacturing_compatibility(bundle).summary_text()}")
        batch = bridge.render_all(bundle, output_dir)
    except LegacyCompatibilityError as exc:
        print(f"\nNo se puede lanzar Blender legacy:\n{exc}")
        return 2

    print(f"\nRender completo -> {batch.output_dir}")
    if batch.generated_files():
        print(flatten_generated_files(batch.generated_files()))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "demo":
        request = build_demo_request(ContentType(args.content))
        return _run_and_export(request, args.output)

    if args.command == "generate":
        request = load_request(args.input)
        return _run_and_export(request, args.output)

    if args.command == "render":
        request = load_request(args.input)
        return _render_request(
            request=request,
            output_dir=args.output_dir,
            bundle_output=args.bundle_output,
            blender_path=args.blender,
            mode=args.mode,
        )

    if args.command == "schema":
        path = schema_path()
        print(path if args.path_only else f"Schema: {path}")
        return 0

    if args.command == "docs":
        path = docs_root()
        if args.path_only:
            print(path)
        else:
            print(f"Docs root: {path}")
            print("- TECHNICAL_GUIDE.md")
            print("- REQUEST_FORMAT.md")
            print("- SOLVER_RULES.md")
            print("- BLENDER_LEGACY.md")
            print("- kerf.md")
            print("- GITHUB_PUBLISH.md")
        return 0

    if args.command == "template":
        text = request_template_text()
        if args.output is None:
            print(text)
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text, encoding="utf-8")
            print(f"Template JSON -> {args.output}")
        return 0

    if args.command == "helptext":
        print(APP_HELP_TEXT)
        return 0

    if args.command == "version":
        print(__version__)
        return 0

    if args.command == "doctor":
        return _doctor(args.blender)

    if args.command == "gui":
        launch_gui()
        return 0

    parser.error("Comando no soportado.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
