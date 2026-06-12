# GUI v14 plan

## Objetivo
Pulir la GUI principal PySide6 sin tocar el core del dominio.

## Base actual
- GUI principal: src/dela_furnfact/ui/pyside_app.py
- Controladores: src/dela_furnfact/ui/controllers.py
- Servicio de aplicación: src/dela_furnfact/application.py
- Tkinter: legacy, no base de v14

## Alcance v14
- limpiar layout visual
- mejorar jerarquía y espaciado
- simplificar flujo de entrada
- mejorar preview y feedback de errores
- mantener compatibilidad con CLI y dominio actual

## No hacer en v14
- reescribir solver
- cambiar modelo de datos
- revivir tk_app.py como fallback principal