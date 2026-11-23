"""Native precision raw I/O, frame addressing and explicit color pipeline."""
from dataclasses import dataclass, asdict, replace
from pathlib import Path
import json, os, tempfile
import cv2
import numpy as np
from formats import FORMATS, CONTAINERS, IMAGE_EXTS
from colour import Color, convert, from_yuv, to_yuv
cv2.setNumThreads(1)

@dataclass(frozen=True)
class Spec:
    format: str = 'RGB8'
    width: int = 1920
    height: int = 1080
    stride: int = 0
    chroma_stride: int = 0
    offset: int = 0
    frame_stride: int = 0
    chroma: str = 'Centered'

def check(cancel):
    if cancel and cancel.is_set(): raise InterruptedError('已取消')

def layout(s):
    f=FORMATS[s.format];w,h=s.width,s.height
    if w<1 or h<1 or w*h>40_000_000:raise ValueError('尺寸必须为正数，单帧上限 4000 万像素')
    if w%f.sx or h%f.sy:raise ValueError(f'{s.format} 要求宽度为 {f.sx} 的倍数、高度为 {f.sy} 的倍数')
    if min(s.stride,s.chroma_stride,s.offset,s.frame_stride)<0:raise ValueError('步长和偏移不能为负')
    unit={'u8':1,'u16':2,'u32':4,'tight':0}[f.storage]
    planes=[]
    if f.family=='rgb':
        row=(w*len(f.order)*10+7)//8 if f.storage=='tight' else w*len(f.order)*unit
        planes=[(h,row,s.stride or row)]
    elif f.family=='rgbp':planes=[(h,w*unit,s.stride or w*unit)]*len(f.order)
    elif f.family in ('565','1010102'):planes=[(h,w*unit,s.stride or w*unit)]
    elif f.family=='yuvpack':planes=[(h,w*2*unit,s.stride or w*2*unit)]
    else:
        planes=[(h,w*unit,s.stride or w*unit)]
        cw=w//f.sx;ch=h//f.sy
        if f.family=='yuvsp':planes.append((ch,cw*2*unit,s.chroma_stride or cw*2*unit))
        else:planes.extend([(ch,cw*unit,s.chroma_stride or cw*unit)]*2)
    if any(stride<row for _,row,stride in planes):raise ValueError('行步长小于有效像素字节数')
    size=sum(h*stride for h,_,stride in planes)
    if s.frame_stride and s.frame_stride<size:raise ValueError('帧步长小于一帧所需字节数')
    if size>1024**3:raise ValueError('单帧跨度超过 1 GiB，请检查步长')
    return planes,size

def frame_info(path,s):
    _,size=layout(s);available=Path(path).stat().st_size-s.offset;step=s.frame_stride or size
    count=0 if available<size else 1+(available-size)//step
    tail=max(0,available-(count-1)*step-size) if count else max(0,available)
    return {'frames':count,'payload_bytes':size,'frame_stride':step,'tail_bytes':tail}

def unpack_tight(rows,count):
    # Gather only the three bytes needed by each sample, avoiding unpackbits expansion.
    start=np.arange(count,dtype=np.int64)*10;byte=start//8;shift=start%8
    padded=np.pad(rows,((0,0),(0,2))).astype(np.uint32)
    words=padded[:,byte]|(padded[:,byte+1]<<8)|(padded[:,byte+2]<<16)
    return ((words>>shift)&1023).astype(np.uint16)

def pack_tight(values):
    h,n=values.shape;out=np.zeros((h,(n*10+7)//8),np.uint8)
    # Each lane within groups of four samples has distinct destination byte indices.
    for lane in range(4):
        idx=np.arange(lane,n,4);bit=idx*10;byte=bit//8;shift=bit%8
        word=values[:,idx].astype(np.uint32)<<shift
        out[:,byte]|=(word&255).astype(np.uint8)
        valid=byte+1<out.shape[1]
        out[:,byte[valid]+1]|=((word[:,valid]>>8)&255).astype(np.uint8)
    return out

def upsample(a,w,h,s):
    if a.shape==(h,w):return a
    if s.chroma=='Centered':return cv2.resize(a,(w,h),interpolation=cv2.INTER_LINEAR)
    if s.chroma!='Cosited':raise ValueError('未知色度位置')
    xx,yy=np.meshgrid(np.arange(w,dtype=np.float32)*a.shape[1]/w,np.arange(h,dtype=np.float32)*a.shape[0]/h)
    return cv2.remap(a,xx,yy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)

def decode_raw(data,s,color):
    f=FORMATS[s.format];planes,size=layout(s)
    if len(data)<size:raise ValueError(f'数据不足：需要 {size} 字节，实际 {len(data)} 字节')
    arrays=[];pos=0;w,h=s.width,s.height
    dtype=np.dtype(f.endian+{'u8':'u1','u16':'u2','u32':'u4','tight':'u1'}[f.storage])
    for rows,row,stride in planes:
        a=np.frombuffer(data,dtype=np.uint8,count=rows*stride,offset=pos).reshape(rows,stride)[:,:row].copy();pos+=rows*stride
        if f.storage=='tight':a=unpack_tight(a,w*len(f.order))
        else:a=a.view(dtype).reshape(rows,-1)
        arrays.append(a)
    maxcode=(1<<f.bits)-1
    def codes(a):return (a.astype(np.uint32)>>f.shift).astype(np.float32)
    alpha=None
    if f.family in ('rgb','rgbp','565','1010102'):
        if f.family=='565':
            x=arrays[0].astype(np.uint32);raw=np.stack(((x>>11)/31,((x>>5)&63)/63,(x&31)/31),axis=2).astype(np.float32)
        elif f.family=='1010102':
            x=arrays[0].astype(np.uint32);raw=np.stack(((x&1023)/1023,((x>>10)&1023)/1023,((x>>20)&1023)/1023,((x>>30)&3)/3),axis=2).astype(np.float32)
        else:
            raw=np.stack([codes(a) for a in arrays],axis=2)/maxcode if f.family=='rgbp' else codes(arrays[0]).reshape(h,w,len(f.order))/maxcode
        rgb=raw[:,:,[f.order.index(x) for x in 'RGB']]
        if 'A' in f.order:alpha=raw[:,:,f.order.index('A')]
        if color.range=='Limited':
            if f.family=='565':raise ValueError('RGB565 仅支持 Full 范围')
            scale=2**(f.bits-8);rgb=(rgb*maxcode-16*scale)/(219*scale)
    else:
        if f.family=='yuvpack':
            a=codes(arrays[0]).reshape(h,w//2,4);yi=[i for i,c in enumerate(f.order) if c=='Y'];y=a[:,:,yi].reshape(h,w);u=a[:,:,f.order.index('U')];v=a[:,:,f.order.index('V')]
        else:
            y=codes(arrays[0]);ch=h//f.sy;cw=w//f.sx
            if f.family=='yuvsp':uv=codes(arrays[1]).reshape(ch,cw,2);a,b=uv[:,:,0],uv[:,:,1]
            else:a,b=codes(arrays[1]),codes(arrays[2])
            u,v=(a,b) if f.order=='YUV' else (b,a)
        scale=2**(f.bits-8)
        if color.range=='Limited':y=(y-16*scale)/(219*scale);u=(u-128*scale)/(224*scale);v=(v-128*scale)/(224*scale)
        else:y=y/maxcode;u=(u-2**(f.bits-1))/maxcode;v=(v-2**(f.bits-1))/maxcode
        rgb=from_yuv(y,upsample(u,w,h,s),upsample(v,w,h,s),color.matrix)
    return rgb.astype(np.float32),alpha

def encode_raw(rgb,alpha,s,color):
    f=FORMATS[s.format];planes,size=layout(s);h,w=rgb.shape[:2]
    if (w,h)!=(s.width,s.height):raise ValueError('输出尺寸必须与图片尺寸一致，本版本不隐式缩放')
    maxcode=(1<<f.bits)-1
    def quant(x):return np.rint(np.clip(x,0,maxcode)).astype(np.uint32)
    def store(a):return (a.astype(np.uint32)<<f.shift).astype(np.dtype(f.endian+('u1' if f.storage=='u8' else 'u2')))
    if f.family in ('rgb','rgbp','565','1010102'):
        c=np.clip(rgb,0,1)
        if color.range=='Limited':
            if f.family=='565':raise ValueError('RGB565 仅支持 Full 范围')
            c=(c*(219*2**(f.bits-8))+16*2**(f.bits-8))/maxcode
        channels={name:c[:,:,i] for i,name in enumerate('RGB')};channels['A']=np.ones((h,w),np.float32) if alpha is None else np.clip(alpha,0,1)
        if f.family=='565':
            a,b,c=[channels[x] for x in f.order];values=np.rint(a*31).astype(np.uint32)<<11|np.rint(b*63).astype(np.uint32)<<5|np.rint(c*31).astype(np.uint32);arrays=[values.astype(f.endian+'u2')]
        elif f.family=='1010102':
            a,b,c=[quant(channels[x]*1023) for x in f.order[:3]];arrays=[(a|(b<<10)|(c<<20)|(np.rint(channels['A']*3).astype(np.uint32)<<30)).astype('<u4')]
        elif f.family=='rgbp':arrays=[store(quant(channels[x]*maxcode)) for x in f.order]
        else:
            a=np.stack([quant(channels[x]*maxcode) for x in f.order],axis=2).reshape(h,-1)
            arrays=[pack_tight(a) if f.storage=='tight' else store(a)]
    else:
        y,u,v=to_yuv(np.clip(rgb,0,1),color.matrix)
        if f.sx!=1 or f.sy!=1:
            if s.chroma=='Cosited':u=u[::f.sy,::f.sx];v=v[::f.sy,::f.sx]
            else:u=cv2.resize(u,(w//f.sx,h//f.sy),interpolation=cv2.INTER_AREA);v=cv2.resize(v,(w//f.sx,h//f.sy),interpolation=cv2.INTER_AREA)
        scale=2**(f.bits-8)
        if color.range=='Limited':y=quant(y*219*scale+16*scale);u=quant(u*224*scale+128*scale);v=quant(v*224*scale+128*scale)
        else:y=quant(y*maxcode);u=quant(u*maxcode+2**(f.bits-1));v=quant(v*maxcode+2**(f.bits-1))
        if f.family=='yuvp':arrays=[store(y)]+[store(a) for a in ((u,v) if f.order=='YUV' else (v,u))]
        elif f.family=='yuvsp':arrays=[store(y),store(np.stack((u,v) if f.order=='YUV' else (v,u),axis=2).reshape(h//f.sy,-1))]
        else:
            yi=iter((y[:,::2],y[:,1::2]));lookup={'U':u,'V':v};a=[next(yi) if x=='Y' else lookup[x] for x in f.order];arrays=[store(np.stack(a,axis=2).reshape(h,-1))]
    out=bytearray(size);pos=0
    for a,(rows,row,stride) in zip(arrays,planes):
        dest=np.frombuffer(out,dtype=np.uint8,count=rows*stride,offset=pos).reshape(rows,stride);dest[:,:row]=np.ascontiguousarray(a).view(np.uint8).reshape(rows,row);pos+=rows*stride
    return bytes(out)

def read(path,s,color,frame=0,cancel=None):
    check(cancel);p=Path(path)
    if p.suffix.lower() in IMAGE_EXTS:
        if frame!=0:raise ValueError('图片文件仅打开首帧/首个页面')
        # IMREAD_UNCHANGED retains integer bit depth and ignores EXIF orientation.
        raw=cv2.imdecode(np.fromfile(p,np.uint8),cv2.IMREAD_UNCHANGED)
        if raw is None:raise ValueError('图片解码失败')
        if raw.dtype not in (np.uint8,np.uint16):raise ValueError('首版仅支持 8/16bit 整数容器图片')
        if raw.shape[0]*raw.shape[1]>40_000_000:raise ValueError('单图超过 4000 万像素')
        if raw.ndim==2:raw=np.repeat(raw[:,:,None],3,axis=2)
        if raw.shape[2] not in (3,4):raise ValueError('不支持的通道数量')
        a=raw.astype(np.float32)/np.iinfo(raw.dtype).max;rgb=a[:,:,[2,1,0]];alpha=a[:,:,3] if a.shape[2]==4 else None
        if color.range=='Limited':
            bits=8 if raw.dtype==np.uint8 else 16;scale=2**(bits-8);rgb=(rgb*((1<<bits)-1)-16*scale)/(219*scale)
        return rgb,alpha,{'frames':1,'tail_bytes':0,'bit_depth':raw.dtype.itemsize*8,'container':True}
    info=frame_info(p,s)
    if frame<0 or frame>=info['frames']:raise ValueError(f'帧号超出范围：共 {info["frames"]} 个完整帧；需要 {info["payload_bytes"]:,} 字节/帧')
    with p.open('rb') as handle:handle.seek(s.offset+frame*info['frame_stride']);data=handle.read(info['payload_bytes'])
    check(cancel);rgb,alpha=decode_raw(data,s,color);info['bit_depth']=FORMATS[s.format].bits;info['container']=False
    if FORMATS[s.format].family.startswith('yuv'):info['raw_payload']=data
    return rgb,alpha,info

def transcode_yuv(data,source,target,src,dst):
    """Lossless same-sampling layout change; no YUV->RGB clipping or resampling."""
    a=FORMATS.get(source.format);b=FORMATS.get(target.format)
    if not a or not b or not a.family.startswith('yuv') or not b.family.startswith('yuv'):return None
    if (a.sx,a.sy,source.chroma)!=(b.sx,b.sy,target.chroma):return None
    if (src.primaries,src.transfer,src.matrix,src.white)!=(dst.primaries,dst.transfer,dst.matrix,dst.white):return None
    if (source.width,source.height)!=(target.width,target.height):return None
    planes,size=layout(source);arrays=[];pos=0;w,h=source.width,source.height
    if len(data)<size:raise ValueError('源帧字节不足')
    for rows,row,stride in planes:
        raw=np.frombuffer(data,np.uint8,count=rows*stride,offset=pos).reshape(rows,stride)[:,:row].copy();pos+=rows*stride
        arrays.append((raw.view(a.endian+('u1' if a.storage=='u8' else 'u2')).reshape(rows,-1).astype(np.uint32)>>a.shift).astype(np.float64))
    if a.family=='yuvpack':
        packed=arrays[0].reshape(h,w//2,4);y=packed[:,:,[i for i,v in enumerate(a.order) if v=='Y']].reshape(h,w);u=packed[:,:,a.order.index('U')];v=packed[:,:,a.order.index('V')]
    else:
        y=arrays[0]
        if a.family=='yuvsp':uv=arrays[1].reshape(h//a.sy,w//a.sx,2);u,v=uv[:,:,0],uv[:,:,1]
        else:u,v=arrays[1:]
        if a.order=='YVU':u,v=v,u
    scale=2**(a.bits-8);maximum=(1<<a.bits)-1
    if src.range=='Limited':y=(y-16*scale)/(219*scale);u=(u-128*scale)/(224*scale);v=(v-128*scale)/(224*scale)
    else:y=y/maximum;u=(u-2**(a.bits-1))/maximum;v=(v-2**(a.bits-1))/maximum
    scale=2**(b.bits-8);maximum=(1<<b.bits)-1
    if dst.range=='Limited':y=y*219*scale+16*scale;u=u*224*scale+128*scale;v=v*224*scale+128*scale
    else:y=y*maximum;u=u*maximum+2**(b.bits-1);v=v*maximum+2**(b.bits-1)
    y,u,v=[np.rint(np.clip(x,0,maximum)).astype(np.uint32) for x in (y,u,v)]
    if b.family=='yuvpack':
        ys=iter((y[:,::2],y[:,1::2]));lookup={'U':u,'V':v};arrays=[np.stack([next(ys) if ch=='Y' else lookup[ch] for ch in b.order],axis=2)]
    elif b.family=='yuvsp':arrays=[y,np.stack((u,v) if b.order=='YUV' else (v,u),axis=2)]
    else:arrays=[y]+list((u,v) if b.order=='YUV' else (v,u))
    planes,size=layout(target);out=bytearray(size);pos=0
    for values,(rows,row,stride) in zip(arrays,planes):
        values=(values<<b.shift).astype(b.endian+('u1' if b.storage=='u8' else 'u2'));dest=np.frombuffer(out,np.uint8,count=rows*stride,offset=pos).reshape(rows,stride);dest[:,:row]=np.ascontiguousarray(values).view(np.uint8).reshape(rows,row);pos+=rows*stride
    return bytes(out)

def encode_container(rgb,alpha,fmt,color):
    if fmt not in CONTAINERS:raise ValueError('未知图片容器')
    bits=16 if '16bit' in fmt else 8;limit=(1<<bits)-1;a=np.clip(rgb,0,1)
    if color.range=='Limited':a=(a*(219*2**(bits-8))+16*2**(bits-8))/limit
    bgr=np.rint(a[:,:,[2,1,0]]*limit).astype(np.uint16 if bits==16 else np.uint8)
    if alpha is not None and fmt.startswith(('PNG','TIFF','WebP')):bgr=np.dstack((bgr,np.rint(np.clip(alpha,0,1)*limit).astype(bgr.dtype)))
    ext={'PNG':'.png','TIFF':'.tiff','JPEG':'.jpg','BMP':'.bmp','WebP':'.webp'}[fmt.split()[0]]
    ok,buf=cv2.imencode(ext,bgr,[cv2.IMWRITE_JPEG_QUALITY,98] if ext=='.jpg' else [cv2.IMWRITE_WEBP_QUALITY,101] if ext=='.webp' else [])
    if not ok:raise ValueError('编码失败')
    return buf.tobytes()

def preview(rgb,color,max_width=16384,managed=True):
    h,w=rgb.shape[:2];small=cv2.resize(rgb,(max(1,round(w*min(1,max_width/w))),max(1,round(h*min(1,max_width/w)))),interpolation=cv2.INTER_AREA)
    if managed:small=convert(small,color,Color())
    return np.ascontiguousarray(np.rint(np.clip(small,0,1)*255).astype(np.uint8))

def result(rgb,alpha,src,dst,spec,fmt,cancel=None,raw_input=None,input_spec=None):
    check(cancel);converted=convert(rgb,src,dst,cancel);check(cancel)
    report={'clipped_components':int(np.count_nonzero((converted<0)|(converted>1))), 'total_components':int(converted.size),'minimum':float(converted.min()),'maximum':float(converted.max())}
    direct=transcode_yuv(raw_input,input_spec,spec,src,dst) if raw_input is not None and input_spec else None
    payload=direct if direct is not None else encode_raw(converted,alpha,spec,dst) if fmt in FORMATS else encode_container(converted,alpha,fmt,dst)
    report['direct_yuv']=direct is not None
    if direct is not None:report['clipped_components']=0
    check(cancel)
    if fmt in FORMATS:decoded,decoded_alpha=decode_raw(payload,spec,dst)
    else:
        raw=cv2.imdecode(np.frombuffer(payload,np.uint8),cv2.IMREAD_UNCHANGED);a=raw.astype(np.float32)/np.iinfo(raw.dtype).max;decoded=a[:,:,[2,1,0]];decoded_alpha=a[:,:,3] if a.shape[2]==4 else None
        if dst.range=='Limited':bits=raw.dtype.itemsize*8;decoded=(decoded*((1<<bits)-1)-16*2**(bits-8))/(219*2**(bits-8))
    report['alpha_dropped']=alpha is not None and decoded_alpha is None
    return payload,decoded,report

def write_atomic(path,payload,source=None):
    p=Path(path)
    if source and (p.resolve()==Path(source).resolve() or (p.exists() and os.path.samefile(p,source))):raise ValueError('不能覆盖当前来源文件')
    if not p.parent.is_dir():raise ValueError('输出目录不存在')
    temp=None
    try:
        with tempfile.NamedTemporaryFile(dir=p.parent,prefix='.prism-',delete=False) as handle:temp=handle.name;handle.write(payload);handle.flush();os.fsync(handle.fileno())
        os.replace(temp,p);temp=None
    finally:
        if temp and os.path.exists(temp):os.unlink(temp)

def save_result(path,payload,source,spec,color,fmt,report):
    metadata={'application':'Prism Pixel 0.1.0','format':fmt,'spec':asdict(replace(spec,offset=0,frame_stride=0)),'color':asdict(color),'report':report,'note':'Color interpretation is explicit; no embedded ICC/HDR mastering metadata is written.'}
    side=Path(str(path)+'.json')
    if side.resolve()==Path(source).resolve():raise ValueError('参数文件不能覆盖来源')
    write_atomic(path,payload,source)
    try:write_atomic(side,json.dumps(metadata,ensure_ascii=False,indent=2).encode('utf-8'),source)
    except OSError as exc:return f'图像已保存，但参数 JSON 写入失败：{exc}'
    return '图像和参数 JSON 已保存'
