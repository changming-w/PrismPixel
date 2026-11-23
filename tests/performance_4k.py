import sys,time,json,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from engine import *
from colour import Color

w,h=3840,2160
a=np.empty((h,w,3),np.float32);a[:,:,0]=np.linspace(0,1,w);a[:,:,1]=np.linspace(0,1,h)[:,None];a[:,:,2]=.25
s=Spec('BGR10_TIGHT_LSB',w,h);c=Color('BT.2020','Gamma 2.2','BT.2020 NCL');results={}
def timed(name,fn):
    start=time.perf_counter();v=fn();results[name]=round(time.perf_counter()-start,3);return v
raw=timed('pack_bgr10_seconds',lambda:encode_raw(a,None,s,c));assert len(raw)==31_104_000
rgb,alpha=timed('unpack_bgr10_seconds',lambda:decode_raw(raw,s,c));np.testing.assert_allclose(rgb,a,atol=1/1023)
target=Spec('P010',w,h);dst=Color('BT.709','BT.709 OETF','BT.709','Limited')
payload,decoded,report=timed('color_convert_p010_encode_decode_seconds',lambda:result(rgb,None,c,dst,target,'P010'))
display=timed('full_resolution_srgb_preview_seconds',lambda:preview(decoded,dst));assert display.shape==(h,w,3)
results.update(resolution=[w,h],raw_bytes=len(raw),p010_bytes=len(payload),full_resolution_preview=True)
Path('validation/performance_4k.json').write_text(json.dumps(results,indent=2));print(json.dumps(results))
