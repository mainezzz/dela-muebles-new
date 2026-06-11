# Arquitectura de `dela-muebles-new`

## Objetivo

`dela-muebles-new` es la arquitectura final del producto DELA y resulta de fusionar:

- la capacidad real de render y fabricaciÃ³n del repo original de Blender
- la arquitectura de dominio/solver del repo orientado a producto

El resultado es una base Ãºnica para:
- CLI
- GUI de escritorio
- generaciÃ³n de bundles JSON
- fabricaciÃ³n con kerf
- integraciÃ³n opcional con Blender legacy
- empaquetado como `.exe`

## Pipeline principal

```text
ShelfRequest
â†“
parse_request_dict / load_request
â†“
validate_request
â†“
get_profile
â†“
ShelfPlanner.solve
â†“
ShelfPlan
â†“
ManufacturingGenerator.build_parts
â†“
SimpleBoardLayouter.layout
â†“
ManufacturingPlan
â†“
ProjectBundle
â†“
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

Es la fuente Ãºnica de verdad del sistema.

### ValidaciÃ³n
Archivo: `src/dela_furnfact/validation.py`

Responsabilidades:
- parsear JSON/dict
- convertir strings a enums
- validar magnitudes
- validar coherencia semÃ¡ntica mÃ­nima
- bloquear requests fÃ­sicamente inviables
- devolver errores agregados y warnings

### Reglas de perfil
Archivo: `src/dela_furnfact/profiles.py`

Define perfiles de almacenamiento:
- `books`
- `dvd`

Cada perfil modela:
- profundidad mÃ­nima e ideal
- altura mÃ­nima e ideal
- ancho por unidad
- nÃºmero de columnas/filas candidatas
- luz mÃ¡xima recomendada

### Solver
Archivo: `src/dela_furnfact/solver.py`

Responsabilidades:
- expandir huecos solicitados
- completar huecos automÃ¡ticos cuando procede
- generar candidatos por filas/columnas
- respetar restricciones fijas
- reducir alturas primero en huecos menos prioritarios
- respetar `fixed_height` y `max_clear_height_mm`
- hacer scoring y elegir la mejor soluciÃ³n

### FabricaciÃ³n
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
- expansiÃ³n por cantidad
- agrupaciÃ³n por material
- elecciÃ³n de stock board segÃºn material y longitud mÃ¡xima
- colocaciÃ³n con kerf
- rotaciÃ³n opcional cuando ayuda a encajar la pieza

### OrquestaciÃ³n
Archivo: `src/dela_furnfact/application.py`

Une:
- validaciÃ³n
- solver
- fabricaciÃ³n
- layout

y devuelve un Ãºnico `ProjectBundle`.

### ExportaciÃ³n
Archivo: `src/dela_furnfact/exporters.py`

Exporta el `ProjectBundle` a JSON.

### IntegraciÃ³n Blender
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

La GUI principal es PySide6. La implementación de Tkinter queda como legacy y no forma parte del entrypoint soportado.

## IntegraciÃ³n con legado

La carpeta `legacy/` conserva:
- scripts Blender originales
- scripts de kerf por variante
- ejemplos histÃ³ricos

Esos archivos no son el nÃºcleo del producto. Se conservan como:
- referencia
- compatibilidad
- transiciÃ³n controlada

## Datos de apoyo

- `schemas/shelf_request.schema.json`: contrato JSON de entrada.
- `examples/`: ejemplos del modelo nuevo.
- `assets/`: materiales e imÃ¡genes.
- `docs/`: documentaciÃ³n tÃ©cnica y de producto.

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
- ediciÃ³n de request
- tabla de huecos
- resumen del bundle
- preview esquemÃ¡tica
- piezas y tableros
- ayuda integrada
- render Blender con logs

## Estado de madurez

Cerrado:
- fase 1: bridge legacy robusto
- fase 2: solver con prioridades/fijos/mÃ¡ximos
- fase 3: docs, request final documentado, ayuda integrada y repo listo para GitHub

Pendiente:
- validaciÃ³n de builds Windows reales
- refinamiento de solver en casos comerciales nuevos
- ampliaciÃ³n del bridge legacy si se soportan topologÃ­as no clÃ¡sicas
