# DELA FurnFact - Combined Documentation Pack


---

## File: `README.md`


# dela-furnfact

`dela-furnfact` es el repositorio final del producto DELA: un configurador de estanterías que transforma **medidas + tipo de contenido + reglas de huecos** en una solución **fabricable**, con **despiece**, **layout de corte con kerf**, **export JSON**, **GUI PySide6** e integración opcional con **Blender legacy**.

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



---

## File: `README.txt`


dela-furnfact
===============

dela-furnfact es el repositorio final del producto DELA: un configurador de
estanterías que transforma medidas + tipo de contenido + reglas de huecos en
una solución fabricable, con despiece, layout de corte con kerf, export JSON,
GUI PySide6 e integración opcional con Blender legacy.

QUE HACE
--------
El usuario define:
- ancho, alto y fondo
- grosor de tablero y trasera
- tipo de contenido: books o dvd
- cantidad estimada
- modo de layout
- reparto de altura sobrante
- restricciones opcionales
- huecos con:
  - label
  - count
  - min_clear_height_mm
  - preferred_clear_height_mm
  - max_clear_height_mm
  - min_clear_width_mm
  - priority
  - fixed_height

El sistema devuelve:
- propuesta geométrica válida
- huecos resueltos
- capacidad estimada
- piezas de fabricación
- tableros y layout con kerf
- bundle JSON
- payloads para Blender legacy
- GUI y CLI

ESTADO
------
Fase 1 cerrada:
- puente real con Blender legacy

Fase 2 cerrada:
- solver con huecos fijos, máximos y prioridades

Fase 3 cerrada:
- documentación técnica completa
- formato JSON documentado
- ayuda integrada en CLI y GUI
- repo preparado para GitHub

DOCUMENTACION PRINCIPAL
-----------------------
- ARCHITECTURE.md
- docs/TECHNICAL_GUIDE.md
- docs/REQUEST_FORMAT.md
- docs/SOLVER_RULES.md
- docs/BLENDER_LEGACY.md
- docs/kerf.md
- docs/PROJECT_STATUS.md
- docs/GITHUB_PUBLISH.md

Versiones en texto plano:
- README.txt
- docs/REQUEST_FORMAT.txt
- docs/SOLVER_RULES.txt
- docs/BLENDER_LEGACY.txt
- docs/TECHNICAL_GUIDE.txt
- docs/PROJECT_STATUS.txt
- docs/GITHUB_PUBLISH.txt

COMANDOS
--------
furnfact demo --content books
furnfact generate --input examples/books_balanced.json --output outputs/books_bundle.json
furnfact render --input examples/books_balanced.json --output-dir outputs/render_books --mode all
furnfact schema
furnfact docs
furnfact template
furnfact helptext
furnfact gui

BUILD
-----
pip install -e .[desktop,build,dev]
pytest
pyinstaller --clean dela-furnfact.spec

COMPATIBILIDAD LEGACY
---------------------
Visual legacy:
- sobre todo 1 o 2 columnas

Fabricación legacy:
- caso clásico de 2 columnas
- divisor central
- trasera partida

Si el proyecto no encaja, la app lo bloquea antes de lanzar Blender.

RESUMEN
-------
dela-furnfact ya no es un conjunto de scripts sueltos. Es una base de producto
con dominio único, solver, fabricación, kerf, GUI, CLI y salida a Blender
legacy cuando procede.


RELEASE Y PUBLICACION

El repositorio incluye:
- CHANGELOG.md
- RELEASE_NOTES_v0.4.0.md
- LICENSE.txt
- CONTRIBUTING.md
- CODE_OF_CONDUCT.md
- SECURITY.md
- .github/workflows/ci.yml
- docs/RELEASE_PLAYBOOK.md
- docs/RELEASE_CHECKLIST.md
- docs/INSTALL_WINDOWS.md
- docs/TEST_MATRIX.md
- ALL_DOCS.md
- ALL_DOCS.txt

Nota:
La build Windows real y la validacion final con Blender siguen siendo pasos manuales.



---

## File: `ARCHITECTURE.md`


# Arquitectura de `dela-furnfact`

## Objetivo

`dela-furnfact` es la arquitectura final resultante de fusionar:

- la capacidad real de render y fabricación del repo original de Blender
- la arquitectura de dominio/solver del repo orientado a producto

El resultado es una base única para:
- CLI
- GUI de escritorio
- generación de bundles JSON
- fabricación con kerf
- integración opcional con Blender legacy
- empaquetado como `.exe`

## Pipeline principal

```text
ShelfRequest
↓
parse_request_dict / load_request
↓
validate_request
↓
get_profile
↓
ShelfPlanner.solve
↓
ShelfPlan
↓
ManufacturingGenerator.build_parts
↓
SimpleBoardLayouter.layout
↓
ManufacturingPlan
↓
ProjectBundle
↓
JsonExporter / CLI / GUI / LegacyBlenderBridge
```

## Capas

### Dominio
Archivo: `src/dela_furnfact/models.py`

Contiene los value objects y modelos principales:
- `OpeningRequest`
- `ValidationIssue`
- `StorageProfile`
- `LayoutCandidate`
- `OpeningPlan`
- `ShelfPlan`
- `ManufacturingPart`
- `CutPlacement`
- `BoardLayout`
- `ManufacturingPlan`
- `ProjectBundle`

Es la fuente única de verdad del sistema.

### Validación
Archivo: `src/dela_furnfact/validation.py`

Responsabilidades:
- parsear JSON/dict
- convertir strings a enums
- validar magnitudes
- validar coherencia semántica mínima
- bloquear requests físicamente inviables
- devolver errores agregados y warnings

### Reglas de perfil
Archivo: `src/dela_furnfact/profiles.py`

Define perfiles de almacenamiento:
- `books`
- `dvd`

Cada perfil modela:
- profundidad mínima e ideal
- altura mínima e ideal
- ancho por unidad
- número de columnas/filas candidatas
- luz máxima recomendada

### Solver
Archivo: `src/dela_furnfact/solver.py`

Responsabilidades:
- expandir huecos solicitados
- completar huecos automáticos cuando procede
- generar candidatos por filas/columnas
- respetar restricciones fijas
- reducir alturas primero en huecos menos prioritarios
- respetar `fixed_height` y `max_clear_height_mm`
- hacer scoring y elegir la mejor solución

### Fabricación
Archivo: `src/dela_furnfact/manufacturing.py`

Convierte un `ShelfPlan` en piezas fabricables:
- laterales
- tapa superior
- base inferior
- divisor(es)
- baldas
- trasera(s)

### Layout de corte
Archivo: `src/dela_furnfact/layout.py`

Implementa un shelf packing estable:
- expansión por cantidad
- agrupación por material
- elección de stock board según material y longitud máxima
- colocación con kerf
- rotación opcional cuando ayuda a encajar la pieza

### Orquestación
Archivo: `src/dela_furnfact/application.py`

Une:
- validación
- solver
- fabricación
- layout

y devuelve un único `ProjectBundle`.

### Exportación
Archivo: `src/dela_furnfact/exporters.py`

Exporta el `ProjectBundle` a JSON.

### Integración Blender
Archivo: `src/dela_furnfact/blender_adapter.py`

Responsabilidades:
- detectar Blender
- construir payloads compatibles con scripts legacy
- validar compatibilidad antes de renderizar
- lanzar Blender por subprocess
- recopilar archivos generados

### Interfaz
Archivos:
- `src/dela_furnfact/cli.py`
- `src/dela_furnfact/ui/pyside_app.py`
- `src/dela_furnfact/ui/tk_app.py`

La GUI principal es PySide6. La de Tkinter queda como fallback ligero.

## Integración con legado

La carpeta `legacy/` conserva:
- scripts Blender originales
- scripts de kerf por variante
- ejemplos históricos

Esos archivos no son el núcleo del producto. Se conservan como:
- referencia
- compatibilidad
- transición controlada

## Datos de apoyo

- `schemas/shelf_request.schema.json`: contrato JSON de entrada.
- `examples/`: ejemplos del modelo nuevo.
- `assets/`: materiales e imágenes.
- `docs/`: documentación técnica y de producto.

## Flujo GUI/CLI

### CLI
- `demo`
- `generate`
- `render`
- `schema`
- `docs`
- `template`
- `helptext`
- `gui`

### GUI
- edición de request
- tabla de huecos
- resumen del bundle
- preview esquemática
- piezas y tableros
- ayuda integrada
- render Blender con logs

## Estado de madurez

Cerrado:
- fase 1: bridge legacy robusto
- fase 2: solver con prioridades/fijos/máximos
- fase 3: docs, request final documentado, ayuda integrada y repo listo para GitHub

Pendiente:
- validación de builds Windows reales
- refinamiento de solver en casos comerciales nuevos
- ampliación del bridge legacy si se soportan topologías no clásicas



---

## File: `CHANGELOG.md`


# Changelog

## 0.4.0 - Release preparation
- Added release-oriented documentation bundle.
- Added GitHub templates, CI workflow, and release checklist.
- Added CLI commands `version` and `doctor`.
- Added Windows installation and release playbook docs.
- Added combined documentation files `ALL_DOCS.md` and `ALL_DOCS.txt`.
- Updated project metadata for release packaging.

## 0.3.0 - Phase 3
- Completed technical and functional documentation.
- Added CLI and GUI embedded help.
- Fixed request saving for advanced opening fields.

## 0.2.0 - Phase 2
- Added fixed-height openings, max height constraints, and priorities.

## 0.1.0 - Phase 1
- Added Blender legacy bridge and compatibility checks.



---

## File: `RELEASE_NOTES_v0.4.0.md`


# Release notes - v0.4.0

This release turns `dela-furnfact` from a development scaffold into a publishable repository package.

## Included
- Domain model, validation, solver, manufacturing, kerf layout and exporters.
- GUI in PySide6 and CLI.
- Legacy Blender bridge with compatibility reports.
- GitHub publication docs, CI workflow, issue templates and release checklist.
- Combined documentation pack for handoff.

## Still manual
- Final Windows build validation on a real Windows machine.
- Final Blender end-to-end validation on a machine with Blender installed.
- Final license choice by the project owner.



---

## File: `CONTRIBUTING.md`


# Contributing

## Workflow
1. Create a branch from `main`.
2. Make one focused change.
3. Run tests.
4. Update docs when behavior changes.
5. Open a pull request.

## Setup
```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .[desktop,build,dev]
pytest
```

## Coding rules
- Keep domain logic out of Blender scripts.
- Keep the request model as the single source of truth.
- Add tests for solver, validation, or manufacturing changes.
- Do not add hardcoded variant scripts back into the main engine.



---

## File: `CODE_OF_CONDUCT.md`


# Code of Conduct

## Our standard
Be respectful, direct, and constructive.

## Expected behavior
- Give technical feedback without personal attacks.
- Explain trade-offs clearly.
- Keep issue reports reproducible and specific.

## Unacceptable behavior
- Harassment
- Discrimination
- Sharing private or sensitive material without permission

## Enforcement
Project maintainers may edit, lock, or close discussions that break these rules.



---

## File: `SECURITY.md`


# Security Policy

## Supported versions
Only the latest tagged release is supported for fixes.

## Reporting a vulnerability
Do not open a public issue for security-sensitive findings.
Report privately to the project owner with:
- summary
- impact
- reproduction steps
- suggested mitigation

## Scope
This application does not ship cloud services. The main risks are:
- unsafe local file handling
- subprocess execution paths
- packaging or dependency issues
- malicious input files



---

## File: `LICENSE.txt`


DELA FurnFact License Status

Copyright (c) 2026

All rights reserved.

This repository is delivered with a default "all rights reserved" status until the owner
replaces this file with the final license choice.

What this means:
- You may read the source code hosted in the repository.
- You may not copy, redistribute, sublicense, or commercialize the code unless the owner grants permission.
- If you want an open-source release, replace this file before publishing with the chosen license text
  such as MIT, Apache-2.0, or GPL-3.0.

Important:
This file is intentionally conservative so the project can be uploaded to GitHub without making
an accidental legal choice on behalf of the owner.



---

## File: `docs/README.md`


# Índice de documentación

- `TECHNICAL_GUIDE.md`: guía técnica completa del proyecto.
- `REQUEST_FORMAT.md`: contrato JSON final.
- `SOLVER_RULES.md`: cómo toma decisiones el solver.
- `BLENDER_LEGACY.md`: integración y límites del pipeline heredado.
- `kerf.md`: kerf como parte del dominio.
- `product.md`: definición de producto y origen de la fusión.
- `migration.md`: visión de migración desde los repos fuente.
- `PROJECT_STATUS.md`: estado actual por fases.
- `BUILD_WINDOWS.md`: build `.exe`.
- `GITHUB_PUBLISH.md`: publicación en GitHub.


## Release docs
- `RELEASE_PLAYBOOK.md`
- `RELEASE_CHECKLIST.md`
- `INSTALL_WINDOWS.md`
- `TEST_MATRIX.md`

## Combined pack
- `../ALL_DOCS.md`
- `../ALL_DOCS.txt`



---

## File: `docs/TECHNICAL_GUIDE.md`


# Guía técnica de `dela-furnfact`

## 1. Resumen técnico

`dela-furnfact` es un generador paramétrico de estanterías con cuatro capas:
- entrada (`ShelfRequest`)
- resolución geométrica (`ShelfPlanner`)
- fabricación (`ManufacturingGenerator`)
- layout de corte (`SimpleBoardLayouter`)

El resultado es un `ProjectBundle` que sirve a la vez para:
- export JSON
- GUI/CLI
- bridge hacia Blender legacy

## 2. Fuente única de verdad

La fuente única del sistema es `ShelfRequest`.
Todo sale de ahí:
- validación
- solver
- fabricación
- kerf
- render legacy

Esto evita el problema original de tener:
- un spec visual por un lado
- scripts kerf hardcodeados por otro

## 3. Modelos principales

### `OpeningRequest`
Describe una necesidad de hueco:
- etiqueta
- cantidad
- altura mínima
- altura preferida
- altura máxima opcional
- anchura mínima opcional
- prioridad
- altura fija sí/no

### `ShelfRequest`
Describe todo el mueble:
- dimensiones exteriores
- espesores
- perfil de contenido
- modo de layout
- restricciones globales
- kerf
- lista de `requested_openings`

### `ShelfPlan`
Solución geométrica elegida por el solver:
- columnas
- filas
- ancho útil por sección
- alto útil por fila
- huecos resueltos
- capacidad estimada
- warnings

### `ManufacturingPlan`
Resultado de fabricación:
- piezas
- tableros
- placements
- kerf usado

### `ProjectBundle`
Estructura final exportable del proyecto.

## 4. Módulos

### `models.py`
Dominio y dataclasses.

### `validation.py`
Parsing y validación del request.
También construye errores agregados amigables para GUI/CLI.

### `profiles.py`
Reglas de negocio por tipo de almacenamiento.

### `solver.py`
- genera candidatos
- rellena huecos automáticos si procede
- respeta restricciones
- calcula score
- elige mejor solución

### `manufacturing.py`
Convierte el plan geométrico en piezas reales.

### `layout.py`
Hace el packing en tableros con kerf.

### `blender_adapter.py`
Puente con scripts legacy:
- detección de Blender
- compatibilidad previa
- payloads
- ejecución

## 5. Reglas prácticas del solver

El solver trabaja por candidatos `columnas x filas`.

Para cada candidato:
1. expande huecos pedidos
2. completa huecos si falta y `allow_auto_fill` es `true`
3. comprueba anchura útil
4. calcula altura útil disponible
5. asigna alturas objetivo
6. si no cabe, reduce primero huecos menos prioritarios
7. respeta límites fijos y máximos
8. reparte sobrante según `remaining_distribution`
9. calcula score

## 6. Kerf

El kerf forma parte del núcleo:
- entra desde `ShelfRequest.kerf_mm`
- se usa en `SimpleBoardLayouter`
- afecta al espacio entre piezas
- altera el aprovechamiento total del tablero

## 7. Legacy

Los scripts en `legacy/` no son el motor principal.
Se conservan para:
- compatibilidad
- comparación
- soporte de render

El producto nuevo no depende conceptualmente de esos scripts para definir el mueble.

## 8. Build de escritorio

- GUI principal: PySide6
- empaquetado: PyInstaller
- recursos incluidos: `schemas`, `examples`, `assets`, `docs`, `legacy`

## 9. Testing

Los tests actuales cubren:
- pipeline books
- pipeline dvd
- huecos personalizados
- validación
- payloads legacy
- restricciones `fixed_height`
- prioridades
- carga de requests JSON

## 10. Siguiente foco técnico

Lo pendiente ya no es rehacer arquitectura. Lo pendiente es:
- validar en Windows real
- ampliar casos comerciales
- decidir si el legado sigue o se sustituye por render nativo nuevo



---

## File: `docs/REQUEST_FORMAT.md`


# Formato del request JSON

## Estructura general

```json
{
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
  "requested_openings": []
}
```

## Campos de raíz

- `name`: nombre del proyecto.
- `width_mm`: ancho exterior total.
- `height_mm`: alto exterior total.
- `depth_mm`: fondo exterior total.
- `board_thickness_mm`: grosor del tablero principal.
- `back_panel_thickness_mm`: grosor de la trasera.
- `content_type`: `books` o `dvd`.
- `content_quantity`: cantidad objetivo aproximada.
- `layout_mode`: `auto`, `balanced`, `dense`.
- `remaining_distribution`: `auto`, `uniform`, `top_bottom_large`, `largest_openings`, `none`.
- `has_back_panel`: incluye trasera.
- `split_back_panel`: parte la trasera.
- `has_center_divider`: permite divisor central.
- `kerf_mm`: pérdida de corte.
- `units`: actualmente solo `mm`.
- `fixed_columns`: bloquea número de columnas.
- `fixed_rows`: bloquea número de filas.
- `allow_auto_fill`: deja al solver completar huecos faltantes.
- `requested_openings`: lista de huecos específicos.

## Campos de `requested_openings`

- `label`: nombre del hueco.
- `count`: cuántas veces se repite.
- `min_clear_height_mm`: altura útil mínima obligatoria.
- `preferred_clear_height_mm`: altura objetivo preferida.
- `max_clear_height_mm`: altura útil máxima opcional.
- `min_clear_width_mm`: anchura útil mínima.
- `priority`: `1` más importante, `5` menos importante.
- `fixed_height`: si es `true`, el solver trata esa altura como fija.

## Interpretación práctica

### Caso 1: hueco flexible
```json
{
  "label": "novela",
  "count": 4,
  "min_clear_height_mm": 230,
  "preferred_clear_height_mm": 255,
  "max_clear_height_mm": 270,
  "priority": 4,
  "fixed_height": false
}
```

### Caso 2: hueco fijo
```json
{
  "label": "arte_grande",
  "count": 1,
  "min_clear_height_mm": 360,
  "preferred_clear_height_mm": 390,
  "max_clear_height_mm": 390,
  "priority": 1,
  "fixed_height": true
}
```

## Recomendaciones

- usa `preferred_clear_height_mm` siempre que quieras guiar al solver
- usa `fixed_height` solo para huecos realmente rígidos
- usa `fixed_columns` y `fixed_rows` solo cuando necesites bloquear la solución
- si el usuario no define todos los huecos, deja `allow_auto_fill = true`

## Ejemplos

- `examples/books_balanced.json`
- `examples/dvd_dense.json`
- `examples/custom_spaces.json`



---

## File: `docs/SOLVER_RULES.md`


# Reglas del solver

## Prioridad

La prioridad se interpreta así:
- `1`: máxima prioridad
- `5`: mínima prioridad

Cuando no caben todas las alturas preferidas:
- el solver reduce antes los huecos de prioridad alta numérica
- intenta preservar primero `priority=1`, luego `2`, etc.

## `fixed_height`

Si `fixed_height` es `true`:
- el hueco exige una altura fija efectiva
- normalmente debe venir acompañada de `preferred_clear_height_mm`
- el solver intenta mantener esa altura exacta

Si la geometría no lo permite:
- el request puede fallar
- o el candidato se descarta

## `max_clear_height_mm`

Limita el crecimiento del hueco.
Se usa sobre todo cuando:
- quieres que un hueco no absorba todo el sobrante
- quieres mantener una estética o uso concreto

## `allow_auto_fill`

Si es `true`:
- el solver puede crear huecos automáticos cuando faltan huecos para completar filas x columnas

Si es `false`:
- el número de huecos pedidos debe cuadrar con la topología resuelta o con las restricciones fijas

## `fixed_columns` y `fixed_rows`

- bloquean el espacio de búsqueda del solver
- hacen la solución más predecible
- también aumentan el riesgo de incompatibilidad si el usuario pide algo que no cabe

## `remaining_distribution`

Controla cómo se reparte el sobrante una vez respetados mínimos y objetivos:
- `uniform`: reparte homogéneamente
- `top_bottom_large`: favorece extremos
- `largest_openings`: empuja más a los huecos mayores
- `none`: no reparte sobrante adicional

## Casos típicos

### Biblioteca con hueco protagonista
- un hueco grande fijo para arte o atlas
- varios huecos flexibles para novela
- prioridad alta en el hueco protagonista

### DVD denso
- muchas filas
- alturas bajas
- layout mode `dense`

### Mixto con reglas del usuario
- unas filas fijas
- otras automáticas
- alturas máximas para controlar crecimiento

## Qué no hace todavía

El solver actual no intenta:
- optimización multiobjetivo avanzada
- coste económico real
- deformación estructural detallada por carga
- CNC/toolpath



---

## File: `docs/BLENDER_LEGACY.md`


# Blender legacy

## Qué es

`dela-furnfact` puede seguir usando los scripts heredados de Blender para:
- render visual
- render técnico de fabricación

Esa integración vive en `src/dela_furnfact/blender_adapter.py`.

## Qué se valida antes de renderizar

El bridge no lanza Blender a ciegas.
Antes genera un `LegacyCompatibilityReport`.

Hay dos chequeos:
- compatibilidad visual
- compatibilidad de fabricación

## Compatibilidad visual

Soporta mejor:
- 1 columna
- 2 columnas
- huecos mapeables a tipos legacy

Los labels nuevos pueden mapearse a:
- `books_small`
- `books_large`
- `books_standard`
- `books_general`
- `dvds`
- `dvd_boxsets`

## Compatibilidad de fabricación

El pipeline heredado de fabricación sigue ligado a la topología clásica:
- 2 columnas
- divisor central
- trasera partida
- layout simétrico de estantería

Si el proyecto no encaja, se bloquea el render de fabricación legacy.

## Archivos legacy conservados

- `legacy/blender/generate_bookshelf.py`
- `legacy/blender/generate_kerf_layout.py`
- `legacy/scripts/kerf_estanteria_dvds.py`
- `legacy/scripts/kerf_estanteria_libros_4_4.py`
- `legacy/scripts/kerf_estanteria_libros_5_3.py`

## Cuándo usar Blender legacy

Úsalo cuando quieras:
- render rápido reutilizando lo existente
- comprobar continuidad con el proyecto anterior
- mantener outputs conocidos

## Cuándo no usarlo como núcleo

No debe ser el motor principal para:
- definir la lógica del mueble
- decidir topologías nuevas
- modelar casos que el legado no soporta



---

## File: `docs/kerf.md`


# Kerf

El kerf representa el material perdido durante el corte.

## Dónde se usa

- `ShelfRequest.kerf_mm`
- `SimpleBoardLayouter`
- cálculo de colocación entre piezas
- cálculo de aprovechamiento de tablero
- bundle exportado
- compatibilidad indirecta con el flujo legacy de fabricación

## Valor por defecto

`3.0 mm`

## Por qué es importante

En este proyecto el kerf no es un detalle decorativo.
Afecta a:
- si una pieza cabe o no en el tablero
- cuántos tableros hacen falta
- cuánto desperdicio queda
- la coherencia entre despiece y plano de corte

## Decisión de arquitectura

El kerf se trata como dato del dominio, no como parche local.
Eso evita la situación del proyecto antiguo donde la lógica de corte vivía dispersa en scripts específicos.



---

## File: `docs/product.md`


# Producto

## Qué es

`dela-furnfact` es un configurador de estanterías a medida orientado a pasar de:
- necesidades de almacenamiento
- medidas del mueble
- restricciones de huecos

a:
- una solución válida
- un despiece
- un layout de corte con kerf
- una salida visual / legacy opcional

## Qué hacían los repos originales

### Repo 1: `dela-muebles-main`
- render real con Blender
- scripts de kerf por variante
- outputs técnicos y visuales
- ejemplos y materiales reales

### Repo 2: `dela-muebles-generator-main`
- modelo de dominio
- arquitectura de solver
- separación conceptual de capas
- documentación de producto

## Qué producto sale al fusionarlos

Un programa de escritorio donde el usuario puede:
- meter medidas
- elegir `books` o `dvd`
- pedir huecos concretos
- fijar o limitar alturas
- dejar que el solver complete el resto

y recibir:
- layout resuelto
- capacidad estimada
- piezas
- tableros
- export JSON
- render legacy cuando la topología lo permite



---

## File: `docs/migration.md`


# Mapa de migración

## Base elegida
La base del proyecto nuevo es la arquitectura del repo 2.

## Qué se absorbió del repo 1
- ejemplos
- lógica de piezas
- obsesión por kerf
- Blender scripts legacy
- materiales

## Qué se absorbió del repo 2
- dominio
- solver por candidatos
- separación de capas
- documentación de producto

## Estructura destino

```text
legacy/               # scripts originales conservados
src/dela_furnfact/    # motor nuevo
assets/               # materiales reutilizados
examples/             # requests nuevos
schemas/              # contrato JSON del request
tests/                # pruebas del núcleo
```



---

## File: `docs/BUILD_WINDOWS.md`


# Build Windows

## Requisitos

- Python 3.11+
- Windows 10/11
- PowerShell o CMD

## Preparación

```powershell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -e .[desktop,build]
```

## Generación del ejecutable

```powershell
pyinstaller --clean dela-furnfact.spec
```

La salida queda en:

```text
dist/dela-furnfact/
```

## Scripts listos

PowerShell:

```powershell
.\scripts\build_windows.ps1
```

CMD:

```cmd
scripts\build_windows.bat
```

## Notas

- El `spec` incluye `schemas/`, `examples/`, `assets/` y `legacy/`.
- La GUI se lanza sin consola (`console=False`).
- El ejecutable se apoya en `paths.py` para localizar recursos en modo empaquetado.



---

## File: `docs/INSTALL_WINDOWS.md`


# Windows installation

## Source mode
1. Install Python 3.11 or 3.12.
2. Open PowerShell in the repository root.
3. Run:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install --upgrade pip
   pip install -e .[desktop,build,dev]
   ```
4. Start the GUI:
   ```powershell
   furnfact gui
   ```

## EXE mode
1. Download the release zip from GitHub Releases.
2. Extract it.
3. Open `dela-furnfact.exe`.
4. If you want Blender rendering, configure the Blender path in the GUI.

## Troubleshooting
- If the GUI does not start, confirm PySide6 is installed in source mode.
- If Blender cannot be found, set its path manually.
- If writing files fails, verify the output folder is writable.



---

## File: `docs/GITHUB_PUBLISH.md`


# Publicar `dela-furnfact` en GitHub

## 1. Crear el repositorio remoto

En GitHub crea un repositorio nuevo llamado:

```text
dela-furnfact
```

No añadas README ni `.gitignore` desde la web si ya vas a subir este proyecto completo.

## 2. Inicializar Git en local

Desde la raíz del proyecto:

```bash
git init
git add .
git commit -m "Initial commit: dela-furnfact"
git branch -M main
```

## 3. Conectar con GitHub

Sustituye `TU_USUARIO` por tu cuenta:

```bash
git remote add origin https://github.com/TU_USUARIO/dela-furnfact.git
git push -u origin main
```

## 4. Comprobar `.gitignore`

Asegúrate de no subir:

- `.venv/`
- `dist/`
- `build/`
- `outputs/`
- `__pycache__/`
- `.pytest_cache/`

## 5. Crear etiquetas y releases

Ejemplo:

```bash
git tag v0.2.0
git push origin v0.2.0
```

Después puedes crear una Release en GitHub y adjuntar el `.zip` o la carpeta `dist/` comprimida.

## 6. Flujo recomendado

Cada cambio:

```bash
git add .
git commit -m "Describe el cambio"
git push
```

## 7. Primera release Windows

1. Ejecuta `scripts/build_windows.ps1`
2. Comprime `dist/dela-furnfact/`
3. Sube el `.zip` como Release en GitHub
4. Añade notas de versión:
   - GUI PySide6
   - solver inicial
   - despiece
   - kerf
   - legacy Blender bridge


## Archivos que conviene revisar antes del primer push

- `README.md`
- `README.txt`
- `ARCHITECTURE.md`
- `docs/REQUEST_FORMAT.md`
- `docs/SOLVER_RULES.md`
- `docs/BLENDER_LEGACY.md`
- `docs/PROJECT_STATUS.md`


## Lo que ya va incluido en el repo final

- `.github/workflows/ci.yml`
- `.github/ISSUE_TEMPLATE/*`
- `.github/pull_request_template.md`
- `CHANGELOG.md`
- `RELEASE_NOTES_v0.4.0.md`
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- `SECURITY.md`



---

## File: `docs/RELEASE_PLAYBOOK.md`


# Release playbook

## Goal
Publish a clean GitHub repository and create a first usable Windows build.

## Pre-release checks
1. Run `pytest`.
2. Run `furnfact demo --content books`.
3. Run `furnfact demo --content dvd`.
4. Run `furnfact doctor`.
5. If Blender is installed, run:
   - `furnfact render --input examples/books_balanced.json --mode visual`
   - `furnfact render --input examples/dvd_dense.json --mode manufacturing`

## Windows packaging
1. Use a real Windows machine.
2. Install Python 3.11 or 3.12.
3. Run:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -e .[desktop,build,dev]
   pytest
   pyinstaller --clean dela-furnfact.spec
   ```
4. Test `dist\dela-furnfact\dela-furnfact.exe`.
5. Confirm:
   - GUI starts
   - docs open
   - bundle generation works
   - Blender path can be configured
   - output folders are created

## GitHub release
1. Push `main`.
2. Create tag `v0.4.0`.
3. Draft release notes from `RELEASE_NOTES_v0.4.0.md`.
4. Upload the Windows zip build.
5. Add screenshots and a short demo GIF if available.



---

## File: `docs/RELEASE_CHECKLIST.md`


# Release checklist

- [ ] `pytest` passes locally
- [ ] `furnfact doctor` passes
- [ ] examples generate bundles
- [ ] docs reviewed
- [ ] version updated in `pyproject.toml` and `src/dela_furnfact/__init__.py`
- [ ] `CHANGELOG.md` updated
- [ ] `RELEASE_NOTES_v0.4.0.md` reviewed
- [ ] Windows build tested manually
- [ ] Blender tested manually on a machine with Blender installed
- [ ] GitHub repository created
- [ ] secrets and private files removed
- [ ] license choice confirmed
- [ ] tag created
- [ ] release uploaded



---

## File: `docs/TEST_MATRIX.md`


# Test matrix

## Automated here
- Unit and smoke tests with `pytest`
- Bundle generation
- JSON load/save
- Blender compatibility checks
- CLI smoke commands

## Manual on Windows
- PySide6 GUI startup
- PyInstaller executable startup
- docs opening from packaged app
- render output directory creation

## Manual with Blender installed
- visual render from example
- manufacturing render from example
- full render batch
- generated file collection and display



---

## File: `docs/PROJECT_STATUS.md`


# Estado del proyecto

## Fase 1 cerrada
- bridge entre modelo nuevo y Blender legacy
- compatibilidad visual y de fabricación
- bloqueo preventivo de renders engañosos

## Fase 2 cerrada
- `fixed_height`
- `max_clear_height_mm`
- prioridades reales
- validación reforzada
- soporte en GUI y schema

## Fase 3 cerrada
- documentación técnica completa
- formato JSON explicado
- reglas del solver documentadas
- bridge legacy documentado
- ayuda integrada en CLI y GUI
- repo limpio para GitHub

## Qué queda ahora

Lo que queda ya no es rehacer la base. Lo que queda es:
- validar build Windows en máquina real
- probar con usuarios/casos comerciales reales
- ampliar compatibilidad Blender si hace falta
- decidir branding y release pública
