import sys,unittest,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from colour import *
from formats import *
from engine import *

class RawTests(unittest.TestCase):
    def test_all_registered_formats(self):
        rgb=np.full((8,12,3),(.22,.48,.73),np.float32);alpha=np.full((8,12),.7,np.float32)
        for name,f in FORMATS.items():
            for range_ in (('Full',) if f.family=='565' else ('Full','Limited')):
                with self.subTest(format=name,range=range_):
                    s=Spec(name,12,8);c=Color(range=range_);encoded=encode_raw(rgb,alpha,s,c)
                    self.assertEqual(len(encoded),layout(s)[1]);decoded,a=decode_raw(encoded,s,c)
                    tolerance=.018 if f.family=='565' else .012 if f.bits==8 else .003 if f.bits==10 else .0008 if f.bits==12 else .00006
                    np.testing.assert_allclose(decoded,rgb,atol=tolerance)
                    if 'A' in f.order:self.assertIsNotNone(a)
    def test_nv12_reference_black_white_and_neutral(self):
        s=Spec('NV12',2,2);data=bytes([16,235,16,235,128,128]);rgb,_=decode_raw(data,s,Color(range='Limited'))
        np.testing.assert_allclose(rgb[:,0],0,atol=1e-7);np.testing.assert_allclose(rgb[:,1],1,atol=1e-7)
        self.assertEqual(encode_raw(rgb,None,s,Color(range='Limited')),data)
    def test_p010_msb_and_planar_lsb(self):
        p010=np.array([64,940,64,940,512,512],'<u2')<<6
        rgb,_=decode_raw(p010.tobytes(),Spec('P010',2,2),Color(range='Limited'))
        np.testing.assert_allclose(rgb[:,1],1,atol=1e-7)
        planar=encode_raw(rgb,None,Spec('YUV420P10LE',2,2),Color(range='Limited'))
        np.testing.assert_array_equal(np.frombuffer(planar,'<u2'),[64,940,64,940,512,512])
    def test_tight_known_samples_and_row_padding(self):
        values=np.array([[0,1,1023,512,17,19]],np.uint16)
        integer=sum(int(v)<<(i*10) for i,v in enumerate(values[0]));packed=integer.to_bytes(8,'little')
        self.assertEqual(pack_tight(values).tobytes(),packed)
        np.testing.assert_array_equal(unpack_tight(np.frombuffer(packed,np.uint8)[None,:],6),values)
        rgb,_=decode_raw(packed+b'xx',Spec('BGR10_TIGHT_LSB',2,1,stride=10),Color())
        np.testing.assert_allclose(rgb[0,0],[1,1/1023,0],atol=1e-7)
    def test_rgb565_and_channel_order(self):
        rgb,_=decode_raw(bytes([0,248,224,7,31,0]),Spec('RGB565LE',3,1),Color())
        np.testing.assert_array_equal(rgb[0],np.eye(3))
        self.assertEqual(encode_raw(rgb,None,Spec('BGR8',3,1),Color()),bytes([0,0,255,0,255,0,255,0,0]))
    def test_yuyv_uyvy_order(self):
        c=Color(range='Limited');a,_=decode_raw(bytes([16,128,235,128]),Spec('YUYV',2,1),c)
        b,_=decode_raw(bytes([128,16,128,235]),Spec('UYVY',2,1),c);np.testing.assert_array_equal(a,b)
    def test_layout_only_keeps_all_chroma_samples(self):
        # Includes saturated/illegal RGB combinations: a RGB roundtrip would clip them.
        source=Spec('NV12',8,4);data=np.random.default_rng(19).integers(0,256,48,dtype=np.uint8).tobytes();color=Color(range='Limited')
        for name in ('I420','YV12','NV21','P010','YUV420P10LE','YUV420P10BE','P016'):
            with self.subTest(format=name):
                dst=Spec(name,8,4);encoded=transcode_yuv(data,source,dst,color,color)
                restored=transcode_yuv(encoded,dst,source,color,color);self.assertEqual(restored,data)
        self.assertIsNone(transcode_yuv(data,source,Spec('I444',8,4),color,color))
    def test_stride_frames_and_truncation(self):
        s=Spec('RGB8',2,2,stride=8,offset=3,frame_stride=20)
        a=np.ones((2,2,3),np.float32);b=np.zeros_like(a)
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'frames.bin';p.write_bytes(b'HDR'+encode_raw(a,None,s,Color())+b'xxxx'+encode_raw(b,None,s,Color())+b'TAIL')
            self.assertEqual(frame_info(p,s)['frames'],2);self.assertEqual(frame_info(p,s)['tail_bytes'],4)
            np.testing.assert_array_equal(read(p,s,Color(),1)[0],b)
            with self.assertRaises(ValueError):read(p,s,Color(),2)
        with self.assertRaises(ValueError):layout(Spec('I420',3,2))
        with self.assertRaises(ValueError):layout(Spec('RGB8',4,4,stride=3))
        with self.assertRaises(ValueError):decode_raw(b'1',Spec('RGB8',2,2),Color())
    def test_quantization_and_alpha_containers(self):
        with tempfile.TemporaryDirectory() as t:
            for fmt in CONTAINERS:
                a=np.full((12,12,3),.42,np.float32);alpha=np.full((12,12),.6,np.float32)
                payload,out,report=result(a,alpha,Color(),Color(),Spec(width=12,height=12),fmt)
                np.testing.assert_allclose(out,a,atol=.01)
                if fmt=='PNG 16bit':
                    p=Path(t)/'a.png';p.write_bytes(payload);decoded,al,info=read(p,Spec(),Color());self.assertEqual(info['bit_depth'],16);np.testing.assert_allclose(al,alpha,atol=1/65535)
    def test_source_protection_and_atomic_output(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'source.bin';p.write_bytes(b'original')
            with self.assertRaises(ValueError):write_atomic(p,b'bad',p)
            self.assertEqual(p.read_bytes(),b'original')
            out=Path(t)/'out.bin';save_result(out,b'abc',p,Spec(),Color(),'RGB8',{})
            self.assertEqual(out.read_bytes(),b'abc');self.assertTrue(Path(str(out)+'.json').exists())

class ColorTests(unittest.TestCase):
    def test_709_2020_reference_matrix(self):
        transform=np.linalg.inv(rgb_xyz('BT.2020'))@rgb_xyz('BT.709')
        expected=np.array([[.627404,.329283,.043313],[.069097,.919540,.011362],[.016391,.088013,.895595]])
        np.testing.assert_allclose(transform,expected,atol=1e-6)
        np.testing.assert_allclose(transform@np.ones(3),1,atol=1e-12)
    def test_transfers_reference_and_roundtrip(self):
        a=np.linspace(.001,1,200,dtype=np.float64)
        for name in TRANSFERS:np.testing.assert_allclose(transfer(transfer(a,name),name,True),a,atol=1e-5)
        self.assertAlmostEqual(float(transfer(np.array(.04045),'sRGB',True)),.0031308,places=7)
        self.assertAlmostEqual(float(transfer(np.array(.5080784215),'PQ ST2084',True,100)),1,places=7)
    def test_primary_roundtrip_and_601_distinction(self):
        a=np.random.default_rng(42).uniform(.1,.9,(6,7,3)).astype(np.float32);src=Color();dst=Color('BT.2020','Gamma 2.2','BT.2020 NCL')
        b=convert(a,src,dst);np.testing.assert_allclose(convert(b,dst,src),a,atol=2e-6)
        self.assertFalse(np.allclose(rgb_xyz('BT.601 525'),rgb_xyz('BT.601 625')))
    def test_matrix_known_red(self):
        rgb=np.array([[[1.,0,0]]],np.float32)
        y,u,v=to_yuv(rgb,'BT.709');self.assertAlmostEqual(float(y[0,0]),.2126,places=6);self.assertAlmostEqual(float(v[0,0]),.5,places=6)
        np.testing.assert_allclose(from_yuv(y,u,v,'BT.709'),rgb,atol=1e-7)

if __name__=='__main__':unittest.main()
