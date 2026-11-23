"""Explicit raw pixel formats. All byte orders are part of the format name."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Format:
    name: str
    family: str
    order: str
    bits: int = 8
    storage: str = 'u8'
    endian: str = '<'
    shift: int = 0
    sx: int = 1
    sy: int = 1

FORMATS = {}
def add(name, family, order, **kw):
    FORMATS[name] = Format(name, family, order, **kw)

for order in ('RGB','BGR','RGBA','BGRA','ARGB','ABGR'):
    add(order+'8','rgb',order)
    for bits in (10,12,16):
        for endian, label in (('<','LE'),('>','BE')):
            add(f'{order}{bits}_U16{label}', 'rgb', order, bits=bits, storage='u16', endian=endian)
            if bits != 16:
                add(f'{order}{bits}_MSB16{label}', 'rgb', order, bits=bits, storage='u16', endian=endian, shift=16-bits)
for order in ('RGB','BGR'):
    add(order+'10_TIGHT_LSB','rgb',order,bits=10,storage='tight')
    for bits in (8,10,12,16):
        add(f'{order}{bits}_PLANAR','rgbp',order,bits=bits,storage='u8' if bits==8 else 'u16')
    for endian,label in (('<','LE'),('>','BE')):
        add(order+'565'+label,'565',order,bits=6,storage='u16',endian=endian)
for order in ('RGB','BGR'):
    add(order+'10A2_LE','1010102',order+'A',bits=10,storage='u32')
add('GBR8_PLANAR','rgbp','GBR')
add('GBR16_PLANAR','rgbp','GBR',bits=16,storage='u16')
for name,order,sx,sy in [('I420','YUV',2,2),('YV12','YVU',2,2),('I422','YUV',2,1),('I444','YUV',1,1)]:
    add(name,'yuvp',order,sx=sx,sy=sy)
for sub,sx,sy in [('420',2,2),('422',2,1),('444',1,1)]:
    for bits in (10,12,16):
        for endian,label in (('<','LE'),('>','BE')):
            add(f'YUV{sub}P{bits}{label}','yuvp','YUV',bits=bits,storage='u16',endian=endian,sx=sx,sy=sy)
for name,order,sx,sy in [('NV12','YUV',2,2),('NV21','YVU',2,2),('NV16','YUV',2,1),('NV61','YVU',2,1),('NV24','YUV',1,1),('NV42','YVU',1,1)]:
    add(name,'yuvsp',order,sx=sx,sy=sy)
for prefix,sx,sy in [('P0',2,2),('P2',2,1),('P4',1,1)]:
    for bits in (10,12,16):
        add(prefix+str(bits),'yuvsp','YUV',bits=bits,storage='u16',shift=16-bits,sx=sx,sy=sy)
for order in ('YUYV','UYVY','YVYU','VYUY'):
    add(order,'yuvpack',order,sx=2)
for bits in (10,16):
    add('Y2'+str(bits),'yuvpack','YUYV',bits=bits,storage='u16',shift=16-bits,sx=2)

CONTAINERS = ('PNG 8bit','PNG 16bit','TIFF 8bit','TIFF 16bit','JPEG','BMP','WebP')
IMAGE_EXTS = {'.png','.jpg','.jpeg','.bmp','.tif','.tiff','.webp'}

def description(f):
    if isinstance(f,str): f=FORMATS[f]
    if f.family.startswith('yuv'):
        sample = {(2,2):'4:2:0',(2,1):'4:2:2',(1,1):'4:4:4'}[(f.sx,f.sy)]
        layout={'yuvp':'平面','yuvsp':'半平面','yuvpack':'交错'}[f.family]
        return f'{sample} · {layout} · {f.bits}bit · '+('高位对齐' if f.shift else '低位对齐')
    if f.storage=='tight': return '每 4 分量 5 字节 · LSB 位流 · 每行独立打包'
    if f.family=='1010102': return '32bit 字：低→高 '+f.order+' = 10/10/10/2bit'
    if f.family=='565': return '16bit 字：高→低 '+f.order+' = 5/6/5bit'
    return f'{f.order} · '+('平面' if f.family=='rgbp' else '交错')+f' · {f.bits}bit · '+('高位对齐' if f.shift else '低位对齐')
