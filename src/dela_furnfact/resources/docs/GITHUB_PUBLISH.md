# Publicar `dela-muebles-new` en GitHub

## 1. Crear el repositorio remoto

En GitHub crea un repositorio nuevo llamado:

```text
dela-muebles-new
```

No añadas README ni `.gitignore` desde la web si ya vas a subir este proyecto completo.

## 2. Inicializar Git en local

Desde la raíz del proyecto:

```bash
git init
git add .
git commit -m "Initial commit: dela-muebles-new"
git branch -M main
```

## 3. Conectar con GitHub

Sustituye `TU_USUARIO` por tu cuenta:

```bash
git remote add origin https://github.com/TU_USUARIO/dela-muebles-new.git
git push -u origin main
```

## 4. Comprobar `.gitignore`

Asegúrate de no subir:

- `.venv/`
- `dist/`
- `build/`
- `outputs/`
- `__pycache__/`
- `.pytest_cache/`

## 5. Crear etiquetas y releases

Ejemplo:

```bash
git tag v0.2.0
git push origin v0.2.0
```

Después puedes crear una Release en GitHub y adjuntar el `.zip` o la carpeta `dist/` comprimida.

## 6. Flujo recomendado

Cada cambio:

```bash
git add .
git commit -m "Describe el cambio"
git push
```

## 7. Primera release Windows

1. Ejecuta `scripts/build_windows.ps1`
2. Comprime `dist/dela-muebles-new/`
3. Sube el `.zip` como Release en GitHub
4. Añade notas de versión:
   - GUI PySide6
   - solver inicial
   - despiece
   - kerf
   - legacy Blender bridge


## Archivos que conviene revisar antes del primer push

- `README.md`
- `README.txt`
- `ARCHITECTURE.md`
- `docs/REQUEST_FORMAT.md`
- `docs/SOLVER_RULES.md`
- `docs/BLENDER_LEGACY.md`
- `docs/PROJECT_STATUS.md`


## Lo que ya va incluido en el repo final

- `.github/workflows/ci.yml`
- `.github/ISSUE_TEMPLATE/*`
- `.github/pull_request_template.md`
- `CHANGELOG.md`
- `RELEASE_NOTES_v0.4.0.md`
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- `SECURITY.md`

