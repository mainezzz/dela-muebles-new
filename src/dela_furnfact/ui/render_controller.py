from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dela_furnfact.blender_adapter import LegacyBlenderBridge, LegacyRenderBatch


@dataclass(frozen=True)
class RenderResultSummary:
    mode: str
    output_dir: str


class RenderController:
    def __init__(self, blender_bridge: LegacyBlenderBridge | None = None) -> None:
        self.blender_bridge = blender_bridge or LegacyBlenderBridge()

    def render_visual(self, bundle, include_content: bool = True, output_dir: str | Path | None = None):
        batch = self.blender_bridge.render_visual(bundle, include_books=include_content, output_dir=output_dir)
        return RenderResultSummary(mode="visual", output_dir=str(batch.output_dir))

    def render_technical(self, bundle, output_dir: str | Path | None = None):
        batch = self.blender_bridge.render_manufacturing(bundle, output_dir=output_dir)
        return RenderResultSummary(mode="technical", output_dir=str(batch.output_dir))

    def render_complete(self, bundle, include_content: bool = True, output_dir: str | Path | None = None):
        batch = self.blender_bridge.render_complete(bundle, include_books=include_content, output_dir=output_dir)
        return RenderResultSummary(mode="complete", output_dir=str(batch.output_dir))
