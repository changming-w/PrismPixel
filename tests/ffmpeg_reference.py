"""Independent FFmpeg decoder cross-check on neutral ramps (no chroma siting ambiguity)."""
import sys,subprocess,tempfile,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from engine import *
ffmpeg=shutil.which('ffmpeg')
if not ffmpeg:raise SystemExit('FFmpeg required for this optional reference test')
formats={'NV12':'nv12','NV21':'nv21','I420':'yuv420p','YV12':None,'I422':'yuv422p','I444':'yuv444p','YUYV':'yuyv422','UYVY':'uyvy422','P010':'p010le','P016':'p016le','YUV420P10LE':'yuv420p10le'}
with tempfile.TemporaryDirectory() as t:
    a=np.repeat(np.linspace(0,1,64,dtype=np.float32)[None,:,None],32,axis=0);a=np.repeat(a,3,axis=2)
    for fmt,pix in formats.items():
        if pix is None:continue
        s=Spec(fmt,64,32);color=Color(range='Limited');p=Path(t)/'in.raw';p.write_bytes(encode_raw(a,None,s,color))
        out=Path(t)/'out.raw'
        subprocess.run([ffmpeg,'-v','error','-y','-f','rawvideo','-pixel_format',pix,'-video_size','64x32','-i',str(p),'-vf','scale=flags=accurate_rnd+bitexact+full_chroma_int:in_range=limited:out_range=full:in_color_matrix=bt709:out_color_matrix=bt709','-frames:v','1','-pix_fmt','rgb48le','-f','rawvideo',str(out)],check=True)
        reference=np.fromfile(out,'<u2').reshape(32,64,3)/65535
        ours=read(p,s,color)[0];np.testing.assert_allclose(reference,ours,atol=.006,err_msg=fmt)
print('FFmpeg independent decoder: 10 formats passed')
