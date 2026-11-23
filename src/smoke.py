from pathlib import Path
import json,time
from PySide6.QtCore import QTimer

def run(app,window,directory):
    out=Path(directory);out.mkdir(parents=True,exist_ok=True);start=time.monotonic();window.demo();timer=QTimer(window)
    def poll():
        if window.output is not None and not window.jobs:
            timer.stop();window.grab().save(str(out/'packaged_window.png'));(out/'result.json').write_text(json.dumps({'ok':True,'version':'0.1.0','shape':list(window.source[0].shape),'payload_bytes':len(window.output[0])}));window.close();app.quit()
        elif time.monotonic()-start>60:
            timer.stop();(out/'result.json').write_text(json.dumps({'ok':False,'error':window.notice.text()}));window.close();app.exit(1)
    timer.timeout.connect(poll);timer.start(100)
