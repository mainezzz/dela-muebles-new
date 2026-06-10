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
