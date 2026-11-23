from pathlib import Path
from importlib.metadata import distributions
import shutil
root=Path(__file__).resolve().parents[1];target=root/'dist'/'PrismPixel'/'licenses';target.mkdir(parents=True,exist_ok=True)
for d in distributions():
    name=d.metadata.get('Name','unknown')
    for f in d.files or []:
        if any(x in str(f).lower() for x in ['license','copying','notice']) and not str(f).endswith('.py'):
            p=Path(d.locate_file(f))
            if p.is_file() and p.stat().st_size<10_000_000:
                dest=target/name/str(f).replace('..','_');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
print(target)
