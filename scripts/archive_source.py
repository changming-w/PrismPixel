from pathlib import Path
import zipfile
root=Path(__file__).resolve().parents[1]
out=root/'releases';out.mkdir(exist_ok=True);target=out/'PrismPixel-source-0.1.0.zip'
excluded={'.venv','.tools','build','dist','validation','__pycache__','.git','releases'}
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
    for p in root.rglob('*'):
        rel=p.relative_to(root)
        if p.is_file() and not any(part in excluded for part in rel.parts) and p.suffix!='.pyc':z.write(p,Path('PrismPixel')/rel)
print(target)
