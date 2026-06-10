from __future__ import annotations

from dataclasses import replace

from dela_furnfact.ui.carpentry_state import (
    CarpentrySettingsState,
    CarpentrySummaryState,
    CarpentryVisibilityState,
)


class CarpentryController:
    def visibility_for_bundle(self, bundle) -> CarpentryVisibilityState:
        if bundle is None:
            return CarpentryVisibilityState(
                enabled=False,
                reason="Genera primero un proyecto para activar Carpintería.",
            )
        return CarpentryVisibilityState(enabled=True)

    def summary_for_bundle(self, bundle) -> CarpentrySummaryState:
        if bundle is None or getattr(bundle, "manufacturing", None) is None:
            return CarpentrySummaryState()

        manufacturing = bundle.manufacturing
        layouts = list(getattr(manufacturing, "board_layouts", ()))
        parts = list(getattr(manufacturing, "parts", ()))

        usage_values = [layout.usage_percent for layout in layouts if getattr(layout, "usage_percent", None) is not None]
        estimated = round(sum(usage_values) / len(usage_values), 1) if usage_values else None
        return CarpentrySummaryState(
            parts_count=len(parts),
            board_count=len(layouts),
            estimated_yield_percent=estimated,
            has_layout=bool(layouts),
        )

    def normalize_settings(self, settings: CarpentrySettingsState) -> CarpentrySettingsState:
        kerf = min(max(settings.kerf_mm, 0.5), 10.0)
        fixed_rows = settings.fixed_rows if settings.fixed_rows and settings.fixed_rows > 0 else None
        fixed_columns = settings.fixed_columns if settings.fixed_columns and settings.fixed_columns > 0 else None
        return replace(
            settings,
            kerf_mm=kerf,
            fixed_rows=fixed_rows,
            fixed_columns=fixed_columns,
        )
