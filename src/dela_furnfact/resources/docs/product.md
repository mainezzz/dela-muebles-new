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
