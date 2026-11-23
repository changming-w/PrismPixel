from pathlib import Path
import sys
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QImage,QPixmap,QPainter,QColor,QPen,QFont
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel,QGraphicsView,QGraphicsScene,QGraphicsPixmapItem,QSizePolicy

class View(QGraphicsView):
    pixel=Signal(int,int)
    zoomed=Signal(float)
    moved=Signal()
    def __init__(self):
        super().__init__();self.setScene(QGraphicsScene(self));self.item=QGraphicsPixmapItem();self.scene().addItem(self.item)
        self.setBackgroundBrush(QColor('#20252d'));self.setFrameShape(QGraphicsView.Shape.NoFrame);self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform,False);self.setMouseTracking(True);self.fit_mode=True;self.full_size=(0,0)
    def set_image(self,a,size):
        h,w=a.shape[:2];image=QImage(a.data,w,h,a.strides[0],QImage.Format.Format_RGB888).copy();self.item.setPixmap(QPixmap.fromImage(image));self.item.setScale(size[0]/w)
        self.full_size=size;self.setSceneRect(QRectF(0,0,*size))
        if self.fit_mode:self.fit()
    def clear_image(self):self.item.setPixmap(QPixmap());self.full_size=(0,0)
    def fit(self):
        self.fit_mode=True
        if self.full_size[0]:self.fitInView(self.sceneRect(),Qt.AspectRatioMode.KeepAspectRatio);self.zoomed.emit(self.transform().m11()*100)
    def actual(self):self.fit_mode=False;self.resetTransform();self.zoomed.emit(100)
    def resizeEvent(self,event):
        super().resizeEvent(event)
        if self.fit_mode:self.fit()
    def wheelEvent(self,event):
        self.fit_mode=False;factor=1.2 if event.angleDelta().y()>0 else 1/1.2
        if .005<self.transform().m11()*factor<64:self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse);self.scale(factor,factor);self.zoomed.emit(self.transform().m11()*100)
        event.accept()
        self.moved.emit()
    def scrollContentsBy(self,dx,dy):
        super().scrollContentsBy(dx,dy);self.moved.emit()
    def mouseMoveEvent(self,event):
        pos=self.mapToScene(event.position().toPoint());x,y=int(pos.x()),int(pos.y())
        self.pixel.emit(x,y) if 0<=pos.x()<self.full_size[0] and 0<=pos.y()<self.full_size[1] else self.pixel.emit(-1,-1)
        super().mouseMoveEvent(event)
    def leaveEvent(self,event):self.pixel.emit(-1,-1);super().leaveEvent(event)

class Pane(QWidget):
    def __init__(self,title,badge):
        super().__init__();layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);layout.setSpacing(0)
        self.title=QLabel(title);self.title.setObjectName('paneTitle');layout.addWidget(self.title)
        self.view=View();layout.addWidget(self.view,1)
        self.caption=QLabel(badge);self.caption.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Fixed);self.caption.setObjectName('paneCaption');layout.addWidget(self.caption)

STYLE='''
QMainWindow,QWidget {font-family: "Segoe UI", "Microsoft YaHei UI"; font-size: 10pt; color:#263343; background:#f4f6f9;}
QMenuBar {background:#fff; border-bottom:1px solid #dee4eb;}
QToolBar {background:#fff; border-bottom:1px solid #dce2eb; spacing:4px; padding:5px;}
QToolButton {background:transparent;border:1px solid transparent;border-radius:5px;padding:5px 9px;}
QToolButton:hover {background:#e8f1ff;border-color:#cbdffa;}
QToolButton:checked {background:#d9e9ff;color:#005fb8;}
QPushButton {background:#fff;border:1px solid #cbd3de;border-radius:5px;padding:6px 12px;min-height:18px;}
QPushButton:hover {background:#eaf2fc;border-color:#77a5d7;}
QPushButton#primary {background:#0866c6;border-color:#0866c6;color:white;font-weight:600;}
QPushButton:disabled,QToolButton:disabled {color:#9aa5b2;background:#eef1f5;}
QLineEdit,QSpinBox,QDoubleSpinBox,QComboBox {background:white;border:1px solid #cbd3de;border-radius:4px;padding:5px;min-height:18px;}
QComboBox::drop-down {width:20px;border:0;}
QListWidget {background:#fff;border:0;outline:0;}
QListWidget::item {padding:9px 8px;border-bottom:1px solid #edf0f4;}
QListWidget::item:selected {background:#e6f1ff;color:#005fb8;border-left:3px solid #1671d1;}
QLabel#section {font-weight:600;font-size:11pt;padding:6px 0;color:#273b53;}
QLabel#hint {color:#65758a;font-size:9pt;}
QLabel#paneTitle {background:#f9fbfe;padding:9px 12px;font-weight:600;border-bottom:2px solid #79a8ed;}
QLabel#paneCaption {background:#e9eef4;color:#53667d;padding:7px 10px;font-size:9pt;}
QTabWidget::pane {border:0;}
QTabBar::tab {padding:10px 22px;background:#eaf0f6;border-bottom:2px solid transparent;}
QTabBar::tab:selected {background:#fff;border-bottom:2px solid #0866c6;color:#0866c6;}
QScrollArea {border:0;}
QSplitter::handle {background:#dde4ed;width:4px;height:4px;}
QGroupBox {border:1px solid #dbe2eb;border-radius:6px;margin-top:14px;padding:8px;}
QGroupBox::title {subcontrol-origin:margin;left:10px;padding:0 4px;color:#415a77;}
QStatusBar {background:#fff;border-top:1px solid #dce2eb;color:#52667c;}
QProgressBar {border:0;max-height:3px;background:#e0eaf6;}
QProgressBar::chunk {background:#1671d1;}
'''
ASSETS=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parents[1]))/'assets'
STYLE+=f'''QComboBox::down-arrow {{image:url("{(ASSETS/'down.png').as_posix()}");width:12px;height:9px;}}
QSpinBox::up-arrow,QDoubleSpinBox::up-arrow {{image:url("{(ASSETS/'up.png').as_posix()}");width:10px;height:8px;}}
QSpinBox::down-arrow,QDoubleSpinBox::down-arrow {{image:url("{(ASSETS/'down.png').as_posix()}");width:10px;height:8px;}}
'''
