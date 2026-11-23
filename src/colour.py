"""D65 linear-light primary conversion; YCbCr matrices are independent."""
from dataclasses import dataclass
import numpy as np

PRIMARIES = {
    'BT.709': ((.64,.33),(.30,.60),(.15,.06)),
    'BT.2020': ((.708,.292),(.170,.797),(.131,.046)),
    'BT.601 525': ((.630,.340),(.310,.595),(.155,.070)),
    'BT.601 625': ((.640,.330),(.290,.600),(.150,.060)),
}
WEIGHTS = {'BT.709':(.2126,.7152,.0722),'BT.2020 NCL':(.2627,.678,.0593),'BT.601':(.299,.587,.114)}
TRANSFERS = ('sRGB','BT.709 OETF','BT.2020 OETF','Gamma 2.2','Gamma 2.4','Linear','PQ ST2084')

@dataclass(frozen=True)
class Color:
    primaries: str = 'BT.709'
    transfer: str = 'sRGB'
    matrix: str = 'BT.709'
    range: str = 'Full'
    white: float = 100.0

def rgb_xyz(name):
    p=np.asarray(PRIMARIES[name],np.float64)
    m=np.stack((p[:,0]/p[:,1],np.ones(3),(1-p.sum(axis=1))/p[:,1]))
    white=np.array([.3127/.3290,1,(1-.3127-.3290)/.3290])
    return m*np.linalg.solve(m,white)

def transfer(a,name,inverse=False,white=100):
    if white <= 0: raise ValueError('参考白亮度必须大于 0')
    x=np.abs(a);sign=np.sign(a)
    if name=='Linear': return a
    if name.startswith('Gamma '):return sign*x**(float(name.split()[1]) if inverse else 1/float(name.split()[1]))
    if name=='PQ ST2084':
        m1=2610/16384;m2=2523/32;c1=3424/4096;c2=2413/128;c3=2392/128
        if inverse:
            q=np.clip(a,0,1)**(1/m2)
            return (np.maximum(q-c1,0)/np.maximum(c2-c3*q,1e-12))**(1/m1)*10000/white
        q=(np.maximum(a,0)*white/10000)**m1
        return ((c1+c2*q)/(1+c3*q))**m2
    if name=='sRGB':
        out=np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4) if inverse else np.where(x<=.0031308,12.92*x,1.055*x**(1/2.4)-.055)
    elif name in ('BT.709 OETF','BT.2020 OETF'):
        alpha,beta=(1.099,.018) if name=='BT.709 OETF' else (1.09929682680944,.018053968510807)
        out=np.where(x<4.5*beta,x/4.5,((x+alpha-1)/alpha)**(1/.45)) if inverse else np.where(x<beta,4.5*x,alpha*x**.45-(alpha-1))
    else:raise ValueError('未知传递函数 '+name)
    return sign*out

def convert(rgb,src,dst,cancel=None):
    if src.primaries==dst.primaries and src.transfer==dst.transfer and src.white==dst.white:return rgb.copy()
    matrix=(np.linalg.inv(rgb_xyz(dst.primaries))@rgb_xyz(src.primaries)).astype(np.float32)
    out=np.empty_like(rgb,dtype=np.float32)
    for y in range(0,len(rgb),64):
        if cancel and cancel.is_set():raise InterruptedError('已取消')
        linear=transfer(rgb[y:y+64],src.transfer,True,src.white)
        # All linear-light values are normalized to each encoding's reference white.
        linear=(linear@matrix.T)*(src.white/dst.white)
        out[y:y+64]=transfer(linear,dst.transfer,False,dst.white)
    return out

def to_yuv(rgb,matrix):
    kr,kg,kb=WEIGHTS[matrix];y=rgb@np.asarray((kr,kg,kb),np.float32)
    return y,(rgb[:,:,2]-y)/(2*(1-kb)),(rgb[:,:,0]-y)/(2*(1-kr))

def from_yuv(y,u,v,matrix):
    kr,kg,kb=WEIGHTS[matrix];r=y+2*(1-kr)*v;b=y+2*(1-kb)*u;g=(y-kr*r-kb*b)/kg
    return np.stack((r,g,b),axis=2).astype(np.float32)
