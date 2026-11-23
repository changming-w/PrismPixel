import os,sys,time,json,tempfile
from pathlib import Path
os.environ['QT_QPA_PLATFORM']='offscreen'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from app import Window,STYLE,setup_fonts
from engine import Spec,Color,encode_raw
import numpy as np
app=QApplication([]);setup_fonts(app);app.setStyleSheet(STYLE)
with tempfile.TemporaryDirectory() as t:
    os.environ['PRISM_PIXEL_CONFIG']=str(Path(t)/'config.ini');w=Window();w.show()
    s=Spec('BGR10_TIGHT_LSB',3840,2160);a=np.empty((2160,3840,3),np.float32);a[:,:,0]=np.linspace(0,1,3840);a[:,:,1]=.4;a[:,:,2]=.7
    path=Path(t)/'frame.bin';path.write_bytes(encode_raw(a,None,s,Color()));del a
    w.input.set_spec(s);w.target.format.setCurrentText('P010');w.target.range.setCurrentText('Limited')
    ticks=[];timer=QTimer();timer.setInterval(5);timer.timeout.connect(lambda:ticks.append(time.perf_counter()));timer.start();start=time.perf_counter();w.add_files([str(path)])
    while w.output is None or w.jobs:
        app.processEvents();time.sleep(.001)
        if time.perf_counter()-start>40:raise AssertionError(w.notice.text())
    timer.stop();elapsed=time.perf_counter()-start;gaps=np.diff(ticks)
    assert len(ticks)>30,'UI event loop did not stay live'
    assert w.before.view.item.pixmap().width()==3840
    # Changing target parameters must retain the already-decoded source array.
    source=w.source[0];w.target.range.setCurrentText('Full');assert w.source[0] is source and w.output is None
    r={'ok':True,'load_and_p010_preview_seconds':round(elapsed,3),'ui_timer_ticks':len(ticks),'max_tick_gap_seconds':round(float(gaps.max()),3),'full_resolution_pixmap':True}
    Path('validation/ui_4k.json').write_text(json.dumps(r,indent=2));print(json.dumps(r));w.close();w.pool.waitForDone();app.processEvents()
