# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

import os
import site

# Find llama_cpp lib directory
site_packages = site.getsitepackages()[0]
llama_cpp_lib = os.path.join(site_packages, 'llama_cpp', 'lib')

a = Analysis(
    ['tinyowl_app.py'],
    pathex=[],
    binaries=[
        # Include llama_cpp shared libraries
        (os.path.join(llama_cpp_lib, '*.so'), 'llama_cpp/lib'),
    ],
    datas=[
        ('models/tinyowl-q4.gguf', 'models'),  # Include the model file
    ],
    hiddenimports=['llama_cpp', 'tkinter'],
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
    name='TinyOwl',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TinyOwl',
)
