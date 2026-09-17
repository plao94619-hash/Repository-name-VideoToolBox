from pathlib import Path

root = Path(SPECPATH)

a = Analysis(
    [str(root / "src" / "main.py")],
    pathex=[str(root / "src")],
    binaries=[
        (str(root / "tools" / "ffmpeg.exe"), "tools"),
        (str(root / "tools" / "ffprobe.exe"), "tools"),
        (str(root / "tools" / "um.exe"), "tools"),
    ],
    datas=[
        (str(root / "LICENSE"), "."),
        (str(root / "THIRD_PARTY_NOTICES.md"), "."),
        (str(root / "tools" / "FFmpeg-GPL-3.0.txt"), "tools"),
        (str(root / "licenses" / "Unlock-Music-MIT.txt"), "licenses"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "unittest"],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="万能音视频工具箱",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(root / "assets" / "app.ico"),
    version=str(root / "packaging" / "version_info.txt"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="万能音视频工具箱",
)
