"""Prism Pixel: explicit, read-only inputs and asynchronous conversion jobs."""
import sys,os,json,threading,traceback,tempfile
from dataclasses import asdict,replace
from pathlib import Path
import numpy as np
import cv2
from PySide6.QtCore import Qt,QSize,Signal,QObject,QRunnable,QThreadPool,QSettings,QTimer
from PySide6.QtGui import QAction,QKeySequence,QImage,QPixmap,QIcon,QFontDatabase,QFont
from PySide6.QtWidgets import QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QFileDialog,QListWidget,QListWidgetItem,QSplitter,QTabWidget,QScrollArea,QToolBar,QCheckBox,QSpinBox,QProgressBar,QMessageBox,QSizePolicy
from panels import Panel
from viewer import Pane,STYLE,ASSETS
from icons import command_icon
from formats import FORMATS,CONTAINERS,IMAGE_EXTS
from colour import Color
from engine import Spec,read,preview,result,save_result,layout,frame_info,write_atomic,encode_raw

VERSION='0.1.0'
def setup_fonts(app):
    for name in ('msyh.ttc','msyhbd.ttc','segoeui.ttf','consola.ttf'):
        p=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'/name
        if p.exists():QFontDatabase.addApplicationFont(str(p))
    app.setFont(QFont('Microsoft YaHei UI',9))

class Signals(QObject):
    done=Signal(int,object,str)
class Job(QRunnable):
    def __init__(self,token,fn):super().__init__();self.token=token;self.fn=fn;self.cancel=threading.Event();self.signals=Signals()
    def run(self):
        try:self.signals.done.emit(self.token,self.fn(self.cancel),'')
        except InterruptedError:self.signals.done.emit(self.token,None,'已取消')
        except Exception as exc:self.signals.done.emit(self.token,None,str(exc))

class Window(QMainWindow):
    def __init__(self):
        super().__init__();self.setWindowTitle('Prism Pixel · 棱镜图像');self.setWindowIcon(QIcon(str(ASSETS/'pixel.png')));self.resize(1600,1000);self.setMinimumSize(1100,720);self.setAcceptDrops(True)
        self.pool=QThreadPool(self);self.pool.setMaxThreadCount(1);self.jobs={};self.serial=0;self.source=None;self.output=None;self.path=None;self.loading_controls=False;self.closing=False
        self.settings=QSettings('PrismTools','PrismPixel') if not os.environ.get('PRISM_PIXEL_CONFIG') else QSettings(os.environ['PRISM_PIXEL_CONFIG'],QSettings.Format.IniFormat)
        self.files=QListWidget();self.files.setIconSize(QSize(64,42));self.files.currentRowChanged.connect(self.select_file)
        left=QWidget();lv=QVBoxLayout(left);lv.setContentsMargins(0,0,0,0);head=QLabel('  文件 / 图像');head.setObjectName('section');lv.addWidget(head);lv.addWidget(self.files,1)
        self.file_count=QLabel('  拖入图片或裸数据');self.file_count.setObjectName('hint');lv.addWidget(self.file_count)
        self.before=Pane('源图像','按输入参数解码');self.after=Pane('转换预览','实际编码后重新解码');self.views=QSplitter();self.views.addWidget(self.before);self.views.addWidget(self.after);self.views.setSizes([500,500])
        middle=QWidget();mv=QVBoxLayout(middle);mv.setContentsMargins(0,0,0,0);mv.setSpacing(0)
        self.path_label=QLabel('打开一张图片，或使用示例开始');self.path_label.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Fixed);self.path_label.setMinimumWidth(0);self.path_label.setMaximumHeight(28);self.path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse);self.path_label.setObjectName('paneCaption');mv.addWidget(self.path_label)
        mv.addWidget(self.views,1)
        nav=QHBoxLayout();nav.setContentsMargins(10,6,10,6);self.frame=QSpinBox();self.frame.setRange(0,0);self.frame.setPrefix('帧 ');self.frame.valueChanged.connect(lambda _:self.load())
        self.prevframe=QPushButton('前帧');self.nextframe=QPushButton('后帧');self.prevframe.clicked.connect(lambda:self.frame.setValue(self.frame.value()-1));self.nextframe.clicked.connect(lambda:self.frame.setValue(self.frame.value()+1));nav.addWidget(self.prevframe);nav.addWidget(self.frame);nav.addWidget(self.nextframe)
        self.frame_label=QLabel('0 帧');nav.addWidget(self.frame_label);nav.addStretch();self.link=QCheckBox('联动');self.link.setChecked(True);nav.addWidget(self.link);self.syncing=False;self.managed=QCheckBox('sRGB 色彩预览');self.managed.setChecked(True);self.managed.setToolTip('将选定原色/传递函数转换至 sRGB 预览；关闭则直接显示归一化码值。PQ 高亮裁切，不做色调映射。');self.managed.toggled.connect(self.repreview);nav.addWidget(self.managed);mv.addLayout(nav)
        self.pixel=QLabel('像素探针 · 将鼠标移入图片查看 RGB 数值');self.pixel.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Fixed);self.pixel.setObjectName('paneCaption');mv.addWidget(self.pixel)
        self.report=QLabel('等待打开文件');self.report.setWordWrap(True);self.report.setObjectName('paneCaption');mv.addWidget(self.report)
        self.input=Panel();self.target=Panel(True);self.target.format.setCurrentText('PNG 16bit');self.tabs=QTabWidget()
        for title,panel in [('输入',self.input),('转换',self.target)]:
            scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(panel);self.tabs.addTab(scroll,title)
        right=QWidget();rv=QVBoxLayout(right);rv.setContentsMargins(0,0,0,0);rv.setSpacing(8);rv.addWidget(self.tabs,1)
        self.notice=QLabel('参数变更后点击“解码”或“预览”应用。');self.notice.setWordWrap(True);self.notice.setObjectName('hint');rv.addWidget(self.notice)
        row=QHBoxLayout();self.decode_button=QPushButton('应用输入 / 解码');self.preview_button=QPushButton('转换预览');self.preview_button.setObjectName('primary');row.addWidget(self.decode_button);row.addWidget(self.preview_button);rv.addLayout(row)
        self.export_button=QPushButton('导出当前帧…');rv.addWidget(self.export_button);self.decode_button.clicked.connect(self.load);self.preview_button.clicked.connect(self.convert);self.export_button.clicked.connect(self.export)
        self.main_split=QSplitter();self.main_split.addWidget(left);self.main_split.addWidget(middle);self.main_split.addWidget(right);self.main_split.setSizes([200,1030,370]);left.setMinimumWidth(140);right.setMinimumWidth(360);right.setMaximumWidth(450)
        body=QWidget();v=QVBoxLayout(body);v.setContentsMargins(6,6,6,0);v.setSpacing(0);v.addWidget(self.main_split,1);self.progress=QProgressBar();self.progress.setRange(0,0);self.progress.setTextVisible(False);self.progress.hide();v.addWidget(self.progress);self.setCentralWidget(body)
        self.actions={};bar=QToolBar('常用操作');bar.setMovable(False);bar.setIconSize(QSize(22,22));bar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon);self.addToolBar(bar)
        def action(label,icon,tip,fn,key=None):
            a=QAction(command_icon(icon),label,self);a.setToolTip(tip);a.triggered.connect(fn)
            if key:a.setShortcut(QKeySequence(key))
            bar.addAction(a);self.actions[label]=a;return a
        action('打开','file','打开图片或裸数据 · Ctrl+O',self.open_files,'Ctrl+O');action('目录','folder','加入文件夹中的图片和裸数据',self.open_folder);bar.addSeparator()
        action('上张','prev','上一张 · Alt+Left',lambda:self.navigate(-1),'Alt+Left');action('下张','next','下一张 · Alt+Right',lambda:self.navigate(1),'Alt+Right');bar.addSeparator()
        action('适应','fit','适应窗口 · F',self.fit,'F');action('原大','actual','100% 原始像素 · 1',self.actual,'1')
        split=action('双图','wipe','显示或隐藏转换预览',lambda checked:self.after.setVisible(checked));split.setCheckable(True);split.setChecked(True)
        action('全屏','focus','全屏 / 退出 · F11',self.fullscreen,'F11');bar.addSeparator()
        action('解码','play','应用输入参数并解码',self.load);action('预览','blend','按输出排布编码并重新解码预览',self.convert);action('导出','export','导出当前结果 · Ctrl+S',self.export,'Ctrl+S');action('停止','stop','取消计算 · Esc',self.cancel,'Esc');bar.addSeparator()
        action('示例','demo','打开内置彩条渐变样本',self.demo);action('说明','help','格式说明与操作帮助',self.help)
        for label in ('解码','预览','导出'):bar.removeAction(self.actions[label])
        menu=self.menuBar().addMenu('文件(&F)')
        for key in ('打开','目录','导出'):menu.addAction(self.actions[key])
        menu.addSeparator();menu.addAction('载入参数 JSON…',self.import_config);menu.addAction('保存输入参数…',self.export_config);menu.addSeparator();menu.addAction('退出',self.close)
        menu=self.menuBar().addMenu('预设(&P)');menu.addAction('VSC · BGR10 紧凑 · 3840×2160',self.vsc_preset)
        menu.addAction('输入色彩复制到输出',lambda:self.target.set_color(self.input.color()))
        self.menuBar().addMenu('帮助(&H)').addAction(self.actions['说明'])
        self.input.changed.connect(self.input_changed);self.target.changed.connect(self.target_changed)
        self.before.view.moved.connect(lambda:self.sync_view(self.before.view,self.after.view));self.after.view.moved.connect(lambda:self.sync_view(self.after.view,self.before.view))
        self.before.view.pixel.connect(lambda x,y:self.probe(x,y,False));self.after.view.pixel.connect(lambda x,y:self.probe(x,y,True))
        self.before.view.zoomed.connect(lambda p:self.statusBar().showMessage(f'缩放 {p:.1f}% · 滚轮缩放，拖动平移'))
        self.restore();self.buttons(False)
    def restore(self):
        self.loading_controls=True
        try:
            for name,panel in [('input',self.input),('target',self.target)]:
                value=self.settings.value(name,'')
                if value:
                    d=json.loads(value);panel.set_spec(Spec(**d['spec']));panel.set_color(Color(**d['color']))
        except (ValueError,TypeError,KeyError):pass
        self.loading_controls=False
    def buttons(self,busy):
        ready=self.source is not None;current=self.output is not None
        self.decode_button.setEnabled(bool(self.path));self.preview_button.setEnabled(ready and not busy);self.export_button.setEnabled(current and not busy)
        self.actions['解码'].setEnabled(bool(self.path));self.actions['预览'].setEnabled(ready and not busy);self.actions['导出'].setEnabled(current and not busy);self.actions['停止'].setEnabled(busy)
        self.prevframe.setEnabled(self.frame.value()>0);self.nextframe.setEnabled(self.frame.value()<self.frame.maximum())
    def submit(self,fn,kind):
        self.cancel(silent=True);self.serial+=1;token=self.serial;job=Job(token,fn);self.jobs[token]=(job,kind);job.signals.done.connect(self.finished);self.progress.show();self.buttons(True);self.pool.start(job)
    def cancel(self,*_,silent=False):
        for job,_ in self.jobs.values():job.cancel.set()
        self.serial+=1;self.progress.hide()
        if hasattr(self,'actions'):self.buttons(False)
        if not silent:self.statusBar().showMessage('已取消后台任务；来源文件未改变')
    def finished(self,token,value,error):
        pair=self.jobs.pop(token,None)
        if not pair or self.closing or token!=self.serial:return
        self.progress.hide();kind=pair[1]
        if error:self.notice.setText(error);self.statusBar().showMessage(error);self.buttons(False);return
        if kind=='scan':self.add_files(value);self.buttons(bool(self.jobs))
        elif kind=='load':
            self.source=value;rgb,alpha,info,thumb,color,spec,frame=value;h,w=rgb.shape[:2]
            self.loading_controls=True;self.target.width.setValue(w);self.target.height.setValue(h);self.frame.blockSignals(True);self.frame.setMaximum(info['frames']-1);self.frame.setValue(frame);self.frame.blockSignals(False);self.loading_controls=False
            self.before.view.set_image(thumb,(w,h));self.before.caption.setText(f'{w} × {h} · {info["bit_depth"]}bit · {color.primaries} / {color.transfer}')
            self.frame_label.setText(f'共 {info["frames"]} 帧');self.notice.setText(f'已解码；尾部未使用 {info["tail_bytes"]:,} 字节。' if info['tail_bytes'] else '输入已解码，可以修改转换参数。')
            item=self.files.currentItem()
            if item:
                icon=cv2.resize(thumb,(96,max(1,round(96*h/w))),interpolation=cv2.INTER_AREA);h0,w0=icon.shape[:2];item.setIcon(QIcon(QPixmap.fromImage(QImage(icon.data,w0,h0,icon.strides[0],QImage.Format.Format_RGB888).copy())))
            self.buttons(False);self.convert()
        elif kind=='convert':
            self.output=value;payload,decoded,report,thumb,spec,color,fmt=value;h,w=decoded.shape[:2];self.after.view.set_image(thumb,(w,h));self.after.caption.setText(f'{fmt} · {color.primaries} / {color.transfer} · {len(payload):,} B')
            self.report.setText(f'输出 {fmt}   |   超范围裁切分量 {report["clipped_components"]:,} / {report["total_components"]:,}   |   裁切前范围 [{report["minimum"]:.5f}, {report["maximum"]:.5f}]'+('   |   YUV 分量直接重排' if report.get('direct_yuv') else '')+('   |   目标格式不保存 Alpha' if report['alpha_dropped'] else ''))
            self.notice.setText('预览已更新；导出保存同一份编码结果，并附带色彩/排布 JSON。');self.buttons(False)
        elif kind=='save':self.notice.setText(value);self.statusBar().showMessage(value);self.buttons(False)
        elif kind=='display':
            a,b=value
            if self.source:self.before.view.set_image(a,(self.source[0].shape[1],self.source[0].shape[0]))
            if self.output and b is not None:self.after.view.set_image(b,(self.output[1].shape[1],self.output[1].shape[0]))
            self.buttons(False)
    def input_changed(self):
        if self.loading_controls:return
        self.cancel(silent=True);self.frame.blockSignals(True);self.frame.setValue(0);self.frame.blockSignals(False);self.source=None;self.output=None;self.after.view.clear_image();self.before.view.clear_image();self.notice.setText('输入参数已改变，请点击“解码”。');self.buttons(False)
        if self.path:self.input.set_container(Path(self.path).suffix.lower() in IMAGE_EXTS)
    def target_changed(self):
        if self.loading_controls:return
        self.cancel(silent=True);self.output=None;self.after.view.clear_image();self.notice.setText('输出参数已改变，请点击“预览”。');self.buttons(False)
    def load(self,*_):
        if not self.path:return
        path=self.path;s=self.input.spec();c=self.input.color();frame=self.frame.value();managed=self.managed.isChecked();self.source=None;self.output=None;self.before.view.clear_image();self.after.view.clear_image()
        def work(cancel):
            rgb,alpha,info=read(path,s,c,frame,cancel);return rgb,alpha,info,preview(rgb,c,managed=managed),c,s,frame
        self.notice.setText('正在解码…');self.submit(work,'load')
    def convert(self,*_):
        if self.source is None:return
        rgb,alpha,info,_,src,input_spec,_=self.source;s=self.target.spec();dst=self.target.color();fmt=self.target.format.currentText();managed=self.managed.isChecked();self.output=None
        def work(cancel):
            payload,decoded,report=result(rgb,alpha,src,dst,s,fmt,cancel,raw_input=info.get('raw_payload'),input_spec=input_spec);return payload,decoded,report,preview(decoded,dst,managed=managed),s,dst,fmt
        self.notice.setText('正在转换并生成实际输出预览…');self.submit(work,'convert')
    def repreview(self,*_):
        if not self.source:return
        source=self.source;output=self.output;managed=self.managed.isChecked()
        self.submit(lambda cancel:(preview(source[0],source[4],managed=managed),preview(output[1],output[5],managed=managed) if output else None),'display')
    def export(self,*_,path=None):
        if not self.output:return
        payload,decoded,report,_,spec,color,fmt=self.output
        ext='.raw' if fmt in FORMATS else {'PNG':'.png','TIFF':'.tiff','JPEG':'.jpg','BMP':'.bmp','WebP':'.webp'}[fmt.split()[0]]
        if not path:
            default=str(Path(self.path).with_name(Path(self.path).stem+'_converted'+ext));path,_=QFileDialog.getSaveFileName(self,'导出当前帧',default,'输出文件 (*'+ext+')')
        if not path:return
        source=self.path;self.submit(lambda cancel:save_result(path,payload,source,spec,color,fmt,report),'save')
    def open_files(self):
        paths,_=QFileDialog.getOpenFileNames(self,'打开图片或裸数据','','图像与裸数据 (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp *.yuv *.rgb *.bgr *.raw *.bin);;所有文件 (*)');self.add_files(paths)
    def open_folder(self):
        folder=QFileDialog.getExistingDirectory(self,'打开文件夹')
        if folder:self.submit(lambda cancel:[str(p) for p in sorted(Path(folder).iterdir()) if not cancel.is_set() and p.is_file() and p.suffix.lower() in IMAGE_EXTS|{'.yuv','.rgb','.bgr','.raw','.bin'}],'scan')
    def add_files(self,paths):
        known={self.files.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.files.count())};start=self.files.count()
        for path in paths:
            path=os.path.abspath(path)
            if path in known:continue
            item=QListWidgetItem(Path(path).name);item.setToolTip(path);item.setData(Qt.ItemDataRole.UserRole,path);self.files.addItem(item);known.add(path)
        self.file_count.setText(f'  {self.files.count()} 个文件')
        if self.files.count()>start:self.files.setCurrentRow(start)
    def select_file(self,row):
        item=self.files.item(row)
        if not item:return
        self.path=item.data(Qt.ItemDataRole.UserRole);self.path_label.setText(self.path);self.path_label.setToolTip(self.path);self.frame.blockSignals(True);self.frame.setValue(0);self.frame.blockSignals(False)
        side=Path(self.path+'.json')
        if side.exists():
            try:self.apply_config(json.loads(side.read_text(encoding='utf-8')))
            except (ValueError,TypeError,KeyError):self.notice.setText('参数 JSON 无效，沿用手动输入设置')
        self.input.set_container(Path(self.path).suffix.lower() in IMAGE_EXTS);self.load()
    def apply_config(self,d):
        # Parse and validate completely before changing controls.
        s=Spec(**d['spec']);c=Color(**d['color'])
        if s.format not in FORMATS and s.format not in CONTAINERS:raise ValueError('未知格式')
        from colour import PRIMARIES,TRANSFERS,WEIGHTS
        if c.primaries not in PRIMARIES or c.transfer not in TRANSFERS or c.matrix not in WEIGHTS or c.range not in ('Full','Limited') or not 1<=c.white<=10000:raise ValueError('色彩参数无效')
        if s.format in FORMATS:layout(s)
        self.loading_controls=True
        try:
            if s.format in FORMATS:self.input.set_spec(s)
            self.input.set_color(c)
        finally:self.loading_controls=False
    def import_config(self):
        p,_=QFileDialog.getOpenFileName(self,'载入输入参数','','JSON (*.json)')
        if p:
            try:self.apply_config(json.loads(Path(p).read_text(encoding='utf-8')));self.load()
            except Exception as exc:self.notice.setText(str(exc))
    def export_config(self):
        p,_=QFileDialog.getSaveFileName(self,'保存输入参数','input.json','JSON (*.json)')
        if p:
            try:write_atomic(p,json.dumps({'spec':asdict(self.input.spec()),'color':asdict(self.input.color())},indent=2).encode(),self.path)
            except Exception as exc:self.notice.setText(str(exc))
    def navigate(self,step):self.files.setCurrentRow(max(0,min(self.files.count()-1,self.files.currentRow()+step)))
    def sync_view(self,source,target):
        if self.syncing or not self.link.isChecked() or self.output is None or not target.full_size[0]:return
        self.syncing=True
        try:
            target.fit_mode=source.fit_mode;target.setTransform(source.transform());target.centerOn(source.mapToScene(source.viewport().rect().center()))
        finally:self.syncing=False
    def fit(self):self.before.view.fit();self.after.view.fit()
    def actual(self):self.before.view.actual();self.after.view.actual()
    def fullscreen(self):self.showNormal() if self.isFullScreen() else self.showFullScreen()
    def probe(self,x,y,output):
        a=self.output[1] if output and self.output else self.source[0] if not output and self.source else None
        if a is None or x<0 or y<0 or x>=a.shape[1] or y>=a.shape[0]:self.pixel.setText('像素探针 · 将鼠标移入图片查看 RGB 数值');return
        rgb=a[y,x];self.pixel.setText(('输出' if output else '输入')+f' · X {x}  Y {y}   |   RGB 浮点 '+', '.join(f'{v:.6f}' for v in rgb)+'   |   10bit Full 等效 '+', '.join(str(round(float(v)*1023)) for v in rgb))
    def vsc_preset(self):
        self.input.set_spec(Spec('BGR10_TIGHT_LSB',3840,2160,frame_stride=49_766_400));self.input.set_color(Color('BT.2020','Gamma 2.2','BT.2020 NCL'));self.tabs.setCurrentIndex(0)
    def demo(self):
        if not hasattr(self,'demo_dir'):self.demo_dir=tempfile.TemporaryDirectory(prefix='PrismPixel-demo-')
        x=np.linspace(0,1,960,dtype=np.float32);y=np.linspace(0,1,540,dtype=np.float32);rgb=np.empty((540,960,3),np.float32);rgb[:,:,0]=x;rgb[:,:,1]=y[:,None];rgb[:,:,2]=(1-x)[None,:]
        rgb[60:220,100:340]=(1,.2,.08);rgb[290:460,620:850]=(.05,.65,1)
        p=Path(self.demo_dir.name)/'色彩与渐变.png';cv2.imencode('.png',np.rint(rgb[:,:,[2,1,0]]*65535).astype(np.uint16))[1].tofile(p);self.input.set_color(Color());self.target.set_color(Color());self.add_files([str(p)])
    def help(self):
        QMessageBox.information(self,'Prism Pixel · 使用说明',f'Prism Pixel {VERSION}\n\n1. 打开图片或 RAW/YUV/BIN。裸数据需要指定尺寸与排布，再点“解码”。\n2. 在“转换”页设置目标排布、原色、传递函数、矩阵和范围，点“预览”。\n3. 预览来自实际输出字节；导出当前帧并生成参数 JSON。\n\n滚轮缩放、拖动平移；F 适应，1 原大，Alt+左右切图。\n\nBT.601 分 525/625 原色。YUV 为 Y′CbCr；BT.2020 为 NCL。\n16bit 容器低位、高位和紧凑 10bit 位流是不同格式。\n裸数据头/行/帧填充可单独设置。多帧可逐帧查看和导出。\n\n预览转换到 sRGB；不自动读取 ICC，不输出显示器原生 HDR。PQ 使用参考白和绝对亮度换算，不自动 tone mapping。超范围值裁切并计数。')
    def dragEnterEvent(self,event):
        if event.mimeData().hasUrls():event.acceptProposedAction()
    def dropEvent(self,event):self.add_files([u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()])
    def closeEvent(self,event):
        self.closing=True;self.cancel(silent=True)
        for key,p in [('input',self.input),('target',self.target)]:self.settings.setValue(key,json.dumps({'spec':asdict(p.spec()),'color':asdict(p.color())}))
        self.settings.sync();super().closeEvent(event)

def main():
    app=QApplication(sys.argv);setup_fonts(app);app.setStyle('Fusion');app.setStyleSheet(STYLE);w=Window();w.show()
    if '--smoke-test' in sys.argv:
        from smoke import run
        QTimer.singleShot(0,lambda:run(app,w,sys.argv[sys.argv.index('--smoke-test')+1]))
    elif '--demo' in sys.argv:QTimer.singleShot(0,w.demo)
    else:
        paths=[x for x in sys.argv[1:] if not x.startswith('--')]
        if paths:QTimer.singleShot(0,lambda:w.add_files(paths))
    return app.exec()
if __name__=='__main__':raise SystemExit(main())
