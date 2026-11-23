# Rebuild with .venv\Scripts\python -m PyInstaller --noconfirm PrismPixel.spec
from pathlib import Path
import os
root=Path(SPECPATH)
a=Analysis([str(root/'src'/'app.py')],pathex=[str(root/'src')],binaries=[],
    datas=[(str(p),'assets') for p in (root/'assets').glob('*.png')],
    hiddenimports=['smoke'],
    excludes=['PySide6.QtWebEngineCore','PySide6.QtWebEngineWidgets','PySide6.QtQml','PySide6.QtQuick','tkinter','matplotlib','scipy','pandas'],
    noarchive=False)
# Qt uses Windows' unversioned ICU ABI. Never bundle a same-named ICU DLL
# discovered in unrelated tools on PATH (e.g. Poppler's versioned ICU ABI).
a.binaries=[entry for entry in a.binaries if Path(entry[0]).name.lower() not in {'icuuc.dll','icuin.dll','icudt78.dll'}]
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,[],exclude_binaries=True,name='PrismPixel',debug=False,
    bootloader_ignore_signals=False,strip=False,upx=False,console=bool(os.environ.get('PRISM_DEBUG_CONSOLE')),
    icon=str(root/'assets'/'pixel.ico'))
coll=COLLECT(exe,a.binaries,a.datas,strip=False,upx=False,name='PrismPixel')
