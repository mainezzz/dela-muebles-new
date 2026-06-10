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
