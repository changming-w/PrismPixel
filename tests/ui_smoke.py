import os,sys,time,tempfile,json
from pathlib import Path
os.environ['QT_QPA_PLATFORM']='offscreen'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from PySide6.QtWidgets import QApplication
from app import Window,STYLE,setup_fonts
from engine import Spec,Color,encode_raw
import numpy as np

def run():
    app=QApplication([]);setup_fonts(app);app.setStyle('Fusion');app.setStyleSheet(STYLE)
    with tempfile.TemporaryDirectory() as t:
        os.environ['PRISM_PIXEL_CONFIG']=str(Path(t)/'config.ini');w=Window();w.show()
        def wait(pred):
            start=time.monotonic()
            while not pred():
                app.processEvents();time.sleep(.01)
                if time.monotonic()-start>30:raise AssertionError('Timeout: '+w.notice.text())
            for _ in range(10):app.processEvents();time.sleep(.01)
        w.demo();wait(lambda:w.output is not None and not w.jobs)
        assert w.source[2]['bit_depth']==16 and w.export_button.isEnabled()
        original=w.source[0];w.target.format.setCurrentText('P010');w.target.range.setCurrentText('Limited');w.target.primaries.setCurrentText('BT.2020');w.target.transfer.setCurrentText('Gamma 2.2');w.target.matrix.setCurrentText('BT.2020 NCL')
        assert w.output is None and not w.export_button.isEnabled()
        w.convert();wait(lambda:w.output is not None and not w.jobs)
        assert w.source[0] is original and len(w.output[0])==960*540*3
        output=Path(t)/'converted.yuv';w.export(path=str(output));wait(lambda:output.exists() and not w.jobs)
        assert Path(str(output)+'.json').exists()
        w.tabs.setCurrentIndex(1);w.path_label.setText('内置示例 · 16bit RGB → P010 / BT.2020');app.processEvents();out=Path('validation');out.mkdir(exist_ok=True);w.grab().save(str(out/'01_workspace.png'));w.resize(1100,720);app.processEvents();assert w.export_button.isVisible();w.grab().save(str(out/'02_compact.png'));assert w.tabs.widget(1).horizontalScrollBar().maximum()==0;w.resize(1600,1000)
        w.add_files([str(output)]);wait(lambda:w.source is not None and not w.jobs)
        assert w.input.format.currentText()=='P010' and w.input.range.currentText()=='Limited'
        assert w.source[0].shape==(540,960,3)
        # Reusing stale output after an input edit must be impossible.
        w.input.width.setValue(962);assert w.source is None and w.output is None
        w.input.set_spec(Spec('BGR10_TIGHT_LSB',4,2,frame_stride=32));w.input.set_color(Color())
        a=np.full((2,4,3),.3,np.float32);b=np.full_like(a,.8);s=w.input.spec();raw=Path(t)/'multi.bin';raw.write_bytes(encode_raw(a,None,s,Color())+bytes(2)+encode_raw(b,None,s,Color()))
        w.target.format.setCurrentText('PNG 16bit');w.add_files([str(raw)]);wait(lambda:w.source is not None and not w.jobs)
        assert w.frame.maximum()==1
        w.frame.setValue(1);wait(lambda:w.source is not None and not w.jobs);assert abs(w.source[0].mean()-.8)<.001
        w.actual();assert w.before.view.transform().m11()==1
        w.fit();assert w.before.view.fit_mode
        w.close();w.pool.waitForDone();app.processEvents()
        assert not w.jobs
        print(json.dumps({'ok':True,'checks':['16bit container','P010 conversion','actual-byte preview','export with JSON','sidecar reload','stale output invalidation','multi-frame stride','fit and 1:1']}))
if __name__=='__main__':run()
