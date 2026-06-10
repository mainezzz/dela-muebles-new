@echo off
setlocal
cd /d "%~dp0\.."
python -m pip install -e .[desktop,build]
pyinstaller --clean dela-furnfact.spec
echo.
echo Build completada.
echo Salida: dist\dela-furnfact\dela-furnfact.exe
