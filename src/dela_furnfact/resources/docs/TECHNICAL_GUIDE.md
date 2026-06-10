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
