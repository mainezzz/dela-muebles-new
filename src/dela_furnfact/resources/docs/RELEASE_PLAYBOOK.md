# Release playbook

## Goal
Publish a clean GitHub repository and create a first usable Windows build.

## Pre-release checks
1. Run `pytest`.
2. Run `furnfact demo --content books`.
3. Run `furnfact demo --content dvd`.
4. Run `furnfact doctor`.
5. If Blender is installed, run:
   - `furnfact render --input examples/books_balanced.json --mode visual`
   - `furnfact render --input examples/dvd_dense.json --mode manufacturing`

## Windows packaging
1. Use a real Windows machine.
2. Install Python 3.11 or 3.12.
3. Run:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -e .[desktop,build,dev]
   pytest
   pyinstaller --clean dela-furnfact.spec
   ```
4. Test `dist\dela-furnfact\dela-furnfact.exe`.
5. Confirm:
   - GUI starts
   - docs open
   - bundle generation works
   - Blender path can be configured
   - output folders are created

## GitHub release
1. Push `main`.
2. Create tag `v0.4.0`.
3. Draft release notes from `RELEASE_NOTES_v0.4.0.md`.
4. Upload the Windows zip build.
5. Add screenshots and a short demo GIF if available.
