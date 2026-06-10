# Windows installation

## Source mode
1. Install Python 3.11 or 3.12.
2. Open PowerShell in the repository root.
3. Run:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install --upgrade pip
   pip install -e .[desktop,build,dev]
   ```
4. Start the GUI:
   ```powershell
   furnfact gui
   ```

## EXE mode
1. Download the release zip from GitHub Releases.
2. Extract it.
3. Open `dela-furnfact.exe`.
4. If you want Blender rendering, configure the Blender path in the GUI.

## Troubleshooting
- If the GUI does not start, confirm PySide6 is installed in source mode.
- If Blender cannot be found, set its path manually.
- If writing files fails, verify the output folder is writable.
