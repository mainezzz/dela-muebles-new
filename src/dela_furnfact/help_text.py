"""Textos de ayuda embebidos para CLI y GUI."""

from __future__ import annotations


APP_HELP_TEXT = """    DELA FurnFact · Ayuda rápida

1. Qué hace
- Convierte medidas + reglas de huecos + tipo de contenido en una estantería fabricable.
- Genera un bundle con layout resuelto, piezas y tableros con kerf.
- Puede lanzar Blender legacy para render visual y fabricación cuando la topología es compatible.

2. Flujo recomendado
- Define ancho, alto, fondo y grosor.
- Elige content_type = books o dvd.
- Añade requested_openings si quieres controlar huecos concretos.
- Usa fixed_columns o fixed_rows solo cuando quieras bloquear la solución.
- Genera el proyecto.
- Exporta el bundle o lanza Blender.

3. Reglas de huecos
- min_clear_height_mm: altura útil mínima obligatoria.
- preferred_clear_height_mm: objetivo preferido del solver.
- max_clear_height_mm: techo opcional; el hueco no debe crecer más allá.
- min_clear_width_mm: anchura mínima útil por hueco.
- priority: 1 = más importante, 5 = menos importante.
- fixed_height: si es true, el solver intenta respetar la altura preferida de forma exacta.

4. Compatibilidad Blender legacy
- Visual legacy: soporta sobre todo 1 o 2 columnas.
- Manufacturing legacy: soporta la topología clásica de 2 columnas, divisor central y trasera partida.
- Si el proyecto no encaja, la app lo bloquea antes de lanzar Blender.

5. Soporte local
- `furnfact doctor`: comprueba rutas, docs y Blender detectado.
- `furnfact version`: imprime la versión instalada.

6. Documentación
- docs/TECHNICAL_GUIDE.md
- docs/REQUEST_FORMAT.md
- docs/SOLVER_RULES.md
- docs/BLENDER_LEGACY.md
- docs/kerf.md
"""


def request_template_text() -> str:
    """Devuelve un ejemplo de request JSON documentado."""
    return """    {
  "name": "Proyecto DELA",
  "width_mm": 1800,
  "height_mm": 2200,
  "depth_mm": 320,
  "board_thickness_mm": 18,
  "back_panel_thickness_mm": 5,
  "content_type": "books",
  "content_quantity": 240,
  "layout_mode": "balanced",
  "remaining_distribution": "uniform",
  "has_back_panel": true,
  "split_back_panel": true,
  "has_center_divider": true,
  "kerf_mm": 3,
  "units": "mm",
  "fixed_columns": 2,
  "fixed_rows": null,
  "allow_auto_fill": true,
  "requested_openings": [
    {
      "label": "arte_grande",
      "count": 1,
      "min_clear_height_mm": 360,
      "preferred_clear_height_mm": 390,
      "max_clear_height_mm": 390,
      "min_clear_width_mm": 0,
      "priority": 1,
      "fixed_height": true
    },
    {
      "label": "novela",
      "count": 4,
      "min_clear_height_mm": 230,
      "preferred_clear_height_mm": 255,
      "max_clear_height_mm": 270,
      "min_clear_width_mm": 0,
      "priority": 4,
      "fixed_height": false
    }
  ]
}
"""
