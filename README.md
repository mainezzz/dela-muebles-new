# dela-muebles-new

`dela-muebles-new` es el repositorio final del producto DELA: un configurador de estanterías que transforma **medidas + tipo de contenido + reglas de huecos** en una solución **fabricable**, con **despiece**, **layout de corte con kerf**, **export JSON**, **GUI PySide6** e integración opcional con **Blender legacy**.

> **Nota de naming**
> - **Repositorio GitHub:** `dela-muebles-new`
> - **Paquete Python / comando / ejecutable actual:** `dela-furnfact`, `dela_furnfact`, `furnfact`
>
> El nombre público del repositorio es `dela-muebles-new`, pero el paquete y algunos artefactos técnicos mantienen de momento el naming `dela-furnfact` para preservar compatibilidad con la build, la CLI y la documentación existente.

## Qué hace

El usuario define:

- ancho, alto y fondo
- grosor de tablero y trasera
- tipo de contenido: `books` o `dvd`
- cantidad estimada
- modo de layout: `auto`, `balanced`, `dense`
- cómo repartir la altura sobrante
- restricciones opcionales: columnas fijas, filas fijas, divisor central, trasera, autollenado
- huecos concretos con:
  - `label`
  - `count`
  - `min_clear_height_mm`
  - `preferred_clear_height_mm`
  - `max_clear_height_mm`
  - `min_clear_width_mm`
  - `priority`
  - `fixed_height`

Y el sistema devuelve:

- una propuesta geométrica válida
- huecos resueltos con medidas útiles
- capacidad estimada
- piezas de fabricación
- tableros y layout de corte con kerf
- bundle JSON completo
- payloads de compatibilidad para Blender legacy
- GUI para escritorio y CLI para automatización

## Qué conserva de cada repositorio original

### De `dela-muebles-main`
- pipeline Blender real
- conocimiento práctico de fabricación
- lógica y ejemplos ligados a kerf
- materiales y nomenclatura del proyecto original
- scripts heredados guardados en `legacy/`

### De `dela-muebles-generator-main`
- arquitectura de producto orientada a dominio
- separación entre intención, solver, solución y fabricación
- enfoque de solver paramétrico
- documentación y visión de roadmap

## Estado del proyecto

Cerrado hasta fase 4:

- fase 1: puente real entre modelo nuevo y Blender legacy
- fase 2: solver con huecos fijos, máximos y prioridades
- fase 3: documentación técnica completa, formato JSON documentado, ayuda integrada en CLI/GUI y repo listo para GitHub
- fase 4: release real, CI, plantillas de GitHub, checklist de publicación y documentación final combinada

Lo pendiente es principalmente:

- validar builds de Windows reales
- refinar el solver si aparecen nuevos casos comerciales
- mejorar la adaptación al legacy si se amplían topologías fuera del caso clásico

## Arquitectura resumida

```text
ShelfRequest
↓
validation.py
↓
profiles.py
↓
solver.py
↓
ShelfPlan
↓
manufacturing.py
↓
layout.py
↓
ProjectBundle
↓
exporters.py / cli.py / ui/pyside_app.py / blender_adapter.py