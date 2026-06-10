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
