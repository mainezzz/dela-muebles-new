# Arquitectura de `dela-muebles-new`

## Objetivo

`dela-muebles-new` es la arquitectura final del producto DELA y resulta de fusionar:

- la capacidad real de render y fabricaciÃƒÂ³n del repo original de Blender
- la arquitectura de dominio/solver del repo orientado a producto

El resultado es una base ÃƒÂºnica para:
- CLI
- GUI de escritorio
- generaciÃƒÂ³n de bundles JSON
- fabricaciÃƒÂ³n con kerf
- integraciÃƒÂ³n opcional con Blender legacy
- empaquetado como `.exe`

## Pipeline principal

```text
ShelfRequest
Ã¢â€ â€œ
parse_request_dict / load_request
Ã¢â€ â€œ
validate_request
Ã¢â€ â€œ
get_profile
Ã¢â€ â€œ
ShelfPlanner.solve
Ã¢â€ â€œ
ShelfPlan
Ã¢â€ â€œ
ManufacturingGenerator.build_parts
Ã¢â€ â€œ
SimpleBoardLayouter.layout
Ã¢â€ â€œ
ManufacturingPlan
Ã¢â€ â€œ
ProjectBundle
Ã¢â€ â€œ
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

Es la fuente ÃƒÂºnica de verdad del sistema.

### ValidaciÃƒÂ³n
Archivo: `src/dela_furnfact/validation.py`

Responsabilidades:
- parsear JSON/dict
- convertir strings a enums
- validar magnitudes
- validar coherencia semÃƒÂ¡ntica mÃƒÂ­nima
- bloquear requests fÃƒÂ­sicamente inviables
- devolver errores agregados y warnings

### Reglas de perfil
Archivo: `src/dela_furnfact/profiles.py`

Define perfiles de almacenamiento:
- `books`
- `dvd`

Cada perfil modela:
- profundidad mÃƒÂ­nima e ideal
- altura mÃƒÂ­nima e ideal
- ancho por unidad
- nÃƒÂºmero de columnas/filas candidatas
- luz mÃƒÂ¡xima recomendada

### Solver
Archivo: `src/dela_furnfact/solver.py`

Responsabilidades:
- expandir huecos solicitados
- completar huecos automÃƒÂ¡ticos cuando procede
- generar candidatos por filas/columnas
- respetar restricciones fijas
- reducir alturas primero en huecos menos prioritarios
- respetar `fixed_height` y `max_clear_height_mm`
- hacer scoring y elegir la mejor soluciÃƒÂ³n

### FabricaciÃƒÂ³n
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
- expansiÃƒÂ³n por cantidad
- agrupaciÃƒÂ³n por material
- elecciÃƒÂ³n de stock board segÃƒÂºn material y longitud mÃƒÂ¡xima
- colocaciÃƒÂ³n con kerf
- rotaciÃƒÂ³n opcional cuando ayuda a encajar la pieza

### OrquestaciÃƒÂ³n
Archivo: `src/dela_furnfact/application.py`

Une:
- validaciÃƒÂ³n
- solver
- fabricaciÃƒÂ³n
- layout

y devuelve un ÃƒÂºnico `ProjectBundle`.

### ExportaciÃƒÂ³n
Archivo: `src/dela_furnfact/exporters.py`

Exporta el `ProjectBundle` a JSON.

### IntegraciÃƒÂ³n Blender
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
- `src/dela_furnfact/ui/tk_app.py` (legacy, no usado por el entrypoint principal)

La GUI principal es PySide6. La implementaciÃ³n de Tkinter queda como legacy y no forma parte del entrypoint soportado.

## IntegraciÃƒÂ³n con legado

La carpeta `legacy/` conserva:
- scripts Blender originales
- scripts de kerf por variante
- ejemplos histÃƒÂ³ricos

Esos archivos no son el nÃƒÂºcleo del producto. Se conservan como:
- referencia
- compatibilidad
- transiciÃƒÂ³n controlada

## Datos de apoyo

- `schemas/shelf_request.schema.json`: contrato JSON de entrada.
- `examples/`: ejemplos del modelo nuevo.
- `assets/`: materiales e imÃƒÂ¡genes.
- `docs/`: documentaciÃƒÂ³n tÃƒÂ©cnica y de producto.

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
- ediciÃƒÂ³n de request
- tabla de huecos
- resumen del bundle
- preview esquemÃƒÂ¡tica
- piezas y tableros
- ayuda integrada
- render Blender con logs

## Estado de madurez

Cerrado:
- fase 1: bridge legacy robusto
- fase 2: solver con prioridades/fijos/mÃƒÂ¡ximos
- fase 3: docs, request final documentado, ayuda integrada y repo listo para GitHub

Pendiente:
- validaciÃƒÂ³n de builds Windows reales
- refinamiento de solver en casos comerciales nuevos
- ampliaciÃƒÂ³n del bridge legacy si se soportan topologÃƒÂ­as no clÃƒÂ¡sicas
