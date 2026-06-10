dela-muebles-factory
=====================
dela-furnfact es el repositorio final del producto DELA: un configurador de
estanterías que transforma medidas + tipo de contenido + reglas de huecos en
una solución fabricable, con despiece, layout de corte con kerf, export JSON,
GUI PySide6 e integración opcional con Blender legacy.


NOTA DE NAMING
--------------
- Repositorio GitHub: dela-muebles-factory
- Paquete Python / comando / ejecutable actual: dela-furnfact, dela_furnfact, furnfact

El repositorio ya usa el nombre dela-muebles-factory, pero el paquete y varios
artefactos técnicos conservan de momento el naming dela-furnfact para mantener
compatibilidad con la build, la CLI y el ejecutable.

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