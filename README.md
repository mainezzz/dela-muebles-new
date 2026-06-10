# dela-muebles-factory

`dela-furnfact` es el repositorio final del producto DELA: un configurador de estanterías que transforma **medidas + tipo de contenido + reglas de huecos** en una solución **fabricable**, con **despiece**, **layout de corte con kerf**, **export JSON**, **GUI PySide6** e integración opcional con **Blender legacy**.

> **Nota de naming**
> - **Repositorio GitHub:** `dela-muebles-factory`
> - **Paquete Python / comando / ejecutable actual:** `dela-furnfact`, `dela_furnfact`, `furnfact`
>
> El nombre público del repositorio ya es `dela-muebles-factory`, pero el paquete y algunos artefactos técnicos mantienen de momento el naming `dela-furnfact` para preservar compatibilidad con la build, la CLI y la documentación existente.

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

- fase 4: release real, CI, plantillas de GitHub, checklist de publicación y documentación final combinada

Cerrado hasta fase 3:

- fase 1: puente real entre modelo nuevo y Blender legacy
- fase 2: solver con huecos fijos, máximos y prioridades
- fase 3: documentación técnica completa, formato JSON documentado, ayuda integrada en CLI/GUI y repo listo para GitHub

Lo que queda ya es principalmente:
- validar builds de Windows reales
- refinar todavía más el solver si aparecen nuevos casos comerciales
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
```

## Estructura del repo

```text
dela-furnfact/
  README.md
  README.txt
  ARCHITECTURE.md
  docs/
  schemas/
  examples/
  assets/
  legacy/
  src/dela_furnfact/
  tests/
  scripts/
  dela-furnfact.spec
```

## Documentación principal

- `ARCHITECTURE.md`: arquitectura final del producto.
- `docs/TECHNICAL_GUIDE.md`: guía técnica completa.
- `docs/REQUEST_FORMAT.md`: contrato del request JSON final.
- `docs/SOLVER_RULES.md`: cómo interpreta el solver prioridades, huecos fijos y máximos.
- `docs/BLENDER_LEGACY.md`: compatibilidad y límites del pipeline heredado.
- `docs/kerf.md`: tratamiento del kerf.
- `docs/GITHUB_PUBLISH.md`: cómo subir el repo a GitHub.
- `docs/PROJECT_STATUS.md`: estado actual, fases cerradas y siguiente foco.

También existen versiones en texto plano:
- `README.txt`
- `docs/REQUEST_FORMAT.txt`
- `docs/SOLVER_RULES.txt`
- `docs/BLENDER_LEGACY.txt`
- `docs/TECHNICAL_GUIDE.txt`
- `docs/PROJECT_STATUS.txt`
- `docs/GITHUB_PUBLISH.txt`

## Instalación

```bash
pip install -e .[desktop,build,dev]
```

## Comandos principales

```bash
furnfact demo --content books
furnfact generate --input examples/books_balanced.json --output outputs/books_bundle.json
furnfact render --input examples/books_balanced.json --output-dir outputs/render_books --mode all
furnfact schema
furnfact docs
furnfact template
furnfact helptext
furnfact gui
```

## Build Windows con PyInstaller

```bash
pyinstaller --clean dela-furnfact.spec

El empaquetado usa `run_gui.py` como lanzador de escritorio y `dela-furnfact.spec` resuelve rutas relativas a la raíz del proyecto.
```

Scripts auxiliares:
- `scripts/build_windows.ps1`
- `scripts/build_windows.bat`

## Tests

```bash
pytest
```

## Compatibilidad Blender legacy

El bridge legacy no intenta “forzar” cualquier topología.

Reglas actuales:
- render visual legacy: soporta sobre todo estanterías de 1 o 2 columnas
- render de fabricación legacy: soporta el caso clásico de 2 columnas, divisor central y trasera partida

Si el proyecto no encaja, la CLI y la GUI lo bloquean antes de lanzar Blender.

## Licencia / publicación

Antes de publicar el repo conviene revisar:
- licencia definitiva
- autoría
- naming comercial
- icono/branding final si se empaqueta como `.exe`

## Resumen corto

`dela-furnfact` ya no es un conjunto de scripts aislados. Es una base de producto:
- con dominio único
- con solver real
- con fabricación y kerf
- con GUI y CLI
- con salida a Blender legacy cuando procede
- preparada para evolucionar hacia una app comercial de escritorio


## Release y publicación

El repositorio ya incluye:

- `CHANGELOG.md`
- `RELEASE_NOTES_v0.4.0.md`
- `LICENSE.txt`
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- `SECURITY.md`
- `.github/workflows/ci.yml`
- plantillas de issues y pull requests
- `docs/RELEASE_PLAYBOOK.md`
- `docs/RELEASE_CHECKLIST.md`
- `docs/INSTALL_WINDOWS.md`
- `docs/TEST_MATRIX.md`
- `ALL_DOCS.md` y `ALL_DOCS.txt`

Nota honesta:
- la build Windows real y la validación final con Blender siguen siendo pasos manuales fuera de este entorno.


## V13 integration status

This repository includes the integrated v13 architecture work:

- explicit opening-type catalog
- visual distribution in the solver
- presentation helpers and preview mapper
- UI architecture modules for state, controllers, preview, actions and carpentry
- release/readiness docs and CI workflow

The shipping GUI remains on the stable application path while the v13 modules provide the refactoring foundation for continued work.
