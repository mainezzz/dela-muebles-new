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
