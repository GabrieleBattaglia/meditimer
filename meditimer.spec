# -*- mode: python ; coding: utf-8 -*-
# Meditimer, il file di compilazione per PyInstaller: un eseguibile in un file unico.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).
# 11/09/2026: revisione 1. La collezione dei suoni e il manuale viaggiano
# dentro l'eseguibile, altrimenti Acusticator non troverebbe i preset e il
# tasto m non avrebbe niente da mostrare.

import os

import GBUtils

COLLEZIONE = os.path.join(os.path.dirname(GBUtils.__file__), 'Acu_Collection.json')

a = Analysis(
    ['meditimer.py'],
    pathex=[],
    binaries=[],
    datas=[(COLLEZIONE, '.'), ('manuale.txt', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='meditimer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
