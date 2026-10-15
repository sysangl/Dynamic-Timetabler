Mostly for myself so I don't forget.

---

Requires pyinstaller

This `run.spec` file should be in the same folder as `run.py`
```
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates','templates'),
        ('static','static'),
        ('routes','routes'),
        ('config','config'),
    ],
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
    name='run',
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
```

Make sure any folders that may be accessed by the program are in `datas`

Then in the same folder of `run.spec`, run this command
`pyinstaller run.spec`

A file named `run.exe` should have been created in the `dist\` folder.