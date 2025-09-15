# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src\\__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/config', 'src/config'),
        ('yolo12n.pt', '.'),       # PyTorch model
        ('yolo12n.onnx', '.'),     # ONNX model
    ],
    hiddenimports=['src.gui.window', 'src.gui.GmailCard', 'src.config.utils'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tensorboard', 'tensorrt', 'tensorrt_bindings', 'tensorrt_dispatch'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ParkingSystem_v2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ParkingSystem_v2',
)
