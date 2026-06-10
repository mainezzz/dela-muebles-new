# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

block_cipher = None

project_root = Path.cwd().resolve()
resources_root = project_root / "src" / "dela_furnfact" / "resources"

datas = [
    (str(resources_root / "schemas"), "schemas"),
    (str(resources_root / "examples"), "examples"),
    (str(resources_root / "assets"), "assets"),
    (str(resources_root / "docs"), "docs"),
    (str(resources_root / "legacy"), "legacy"),
]

a = Analysis(
    ["run_gui.py"],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="dela-furnfact",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="dela-furnfact",
)
