from dataclasses import asdict
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget,QVBoxLayout,QFormLayout,QComboBox,QSpinBox,QDoubleSpinBox,QLabel,QPushButton,QGroupBox,QHBoxLayout,QSizePolicy
from formats import FORMATS,CONTAINERS,description
from colour import Color,PRIMARIES,TRANSFERS,WEIGHTS
from engine import Spec

def combo(values):
    w=QComboBox();w.addItems(list(values));w.setMinimumContentsLength(8);w.setMinimumWidth(0);w.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed);w.setMaxVisibleItems(18);w.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon);return w
def number(maximum=2_000_000_000):
    w=QSpinBox();w.setRange(0,maximum);w.setGroupSeparatorShown(True);return w

class Panel(QWidget):
    changed=Signal()
    def __init__(self,output=False):
        super().__init__();self.output=output;v=QVBoxLayout(self);v.setContentsMargins(12,12,12,12);v.setSpacing(10)
        self.format=combo((CONTAINERS if output else ())+tuple(FORMATS));self.format.setToolTip('格式名称明确区分通道顺序、有效位、容器位数和大小端。MSB=高位对齐。')
        v.addWidget(QLabel('输出格式' if output else '裸数据排布'));v.addWidget(self.format)
        self.desc=QLabel();self.desc.setObjectName('hint');self.desc.setWordWrap(True);v.addWidget(self.desc)
        self.raw_group=QGroupBox('尺寸与内存布局');form=QFormLayout(self.raw_group);form.setSpacing(8)
        self.width=number(16384);self.height=number(16384);self.width.setMinimum(1);self.height.setMinimum(1);self.width.setValue(1920);self.height.setValue(1080);self.width.setMinimumWidth(0);self.height.setMinimumWidth(0);self.width.setMaximumWidth(105);self.height.setMaximumWidth(105)
        sizes=QHBoxLayout();sizes.addWidget(self.width);sizes.addWidget(QLabel('×'));sizes.addWidget(self.height);form.addRow('宽 × 高',sizes)
        self.stride=number();self.chroma_stride=number();self.offset=number();self.frame_stride=number();self.chroma=combo(('Centered','Cosited'))
        for label,w in [('行步长 / B',self.stride),('色度行步长 / B',self.chroma_stride),('文件头偏移 / B',self.offset),('帧跨度 / B',self.frame_stride),('色度位置',self.chroma)]:form.addRow(label,w)
        for w in (self.stride,self.chroma_stride,self.frame_stride):w.setSpecialValueText('自动 / 紧密')
        self.stride.setToolTip('RGB/Y 平面每行字节数，RGB 平面格式对每个平面使用相同步长。')
        self.chroma_stride.setToolTip('U/V 或 UV 平面行步长；0 表示紧密排列，不继承 Y 步长。')
        self.frame_stride.setToolTip('相邻帧起点的间隔，可用于忽略每帧尾部硬件填充。')
        self.chroma.setToolTip('Centered：居中色度、双线性上采样/面积下采样；Cosited：左上同位色度。')
        v.addWidget(self.raw_group)
        if output:
            self.width.setEnabled(False);self.height.setEnabled(False)
            for w in (self.offset,self.frame_stride):w.hide();form.labelForField(w).hide()
        group=QGroupBox('色彩解释' if not output else '目标色彩');form=QFormLayout(group);form.setSpacing(8)
        self.primaries=combo(PRIMARIES);self.transfer=combo(TRANSFERS);self.matrix=combo(WEIGHTS);self.range=combo(('Full','Limited'));self.white=QDoubleSpinBox();self.white.setRange(1,10000);self.white.setValue(100);self.white.setSuffix(' nit')
        for title,w in [('RGB 原色',self.primaries),('传递函数',self.transfer),('YUV 矩阵',self.matrix),('码值范围',self.range),('参考白',self.white)]:form.addRow(title,w)
        self.matrix.setToolTip('只影响 Y′CbCr↔RGB 的编码矩阵，不等同于 RGB 原色色域变换。')
        self.white.setToolTip('线性 RGB=1 对应亮度；PQ 使用绝对亮度。SDR 转换通常保持两侧一致。')
        v.addWidget(group)
        preset=QHBoxLayout()
        for label,prim,tr,matrix in [('sRGB','BT.709','sRGB','BT.709'),('709','BT.709','BT.709 OETF','BT.709'),('2020','BT.2020','Gamma 2.2','BT.2020 NCL')]:
            button=QPushButton(label);button.setToolTip('设定色彩组合；范围仍由用户选择');button.clicked.connect(lambda _,p=prim,t=tr,m=matrix:self.set_color(Color(p,t,m,self.range.currentText())));preset.addWidget(button)
        v.addLayout(preset)
        self.note=QLabel('容器图片按手动色彩设置解释；不自动应用 ICC。' if not output else '预览会重新解码实际输出字节，包含位深量化和色度采样的影响。');self.note.setWordWrap(True);self.note.setObjectName('hint');v.addWidget(self.note);v.addStretch()
        for w in self.findChildren(QComboBox):w.currentIndexChanged.connect(self._changed)
        for w in self.findChildren(QSpinBox)+self.findChildren(QDoubleSpinBox):w.valueChanged.connect(self._changed)
        self._changed()
    def _changed(self,*_):
        name=self.format.currentText();raw=name in FORMATS
        self.desc.setText(description(name) if raw else '标准图片容器 · 保留整数位深 · 色彩参数另存 JSON')
        self.raw_group.setVisible(raw)
        self.matrix.setEnabled(raw and FORMATS[name].family.startswith('yuv'))
        self.changed.emit()
    def spec(self):return Spec(self.format.currentText(),self.width.value(),self.height.value(),self.stride.value(),self.chroma_stride.value(),self.offset.value(),self.frame_stride.value(),self.chroma.currentText())
    def color(self):return Color(self.primaries.currentText(),self.transfer.currentText(),self.matrix.currentText(),self.range.currentText(),self.white.value())
    def set_color(self,color):
        for k in ('primaries','transfer','matrix','range'):getattr(self,k).setCurrentText(getattr(color,k))
        self.white.setValue(color.white)
    def set_spec(self,s):
        self.format.setCurrentText(s.format)
        for key in ('width','height','stride','chroma_stride','offset','frame_stride'):getattr(self,key).setValue(getattr(s,key))
        self.chroma.setCurrentText(s.chroma)
    def set_container(self,yes):
        if not self.output:
            self.raw_group.setVisible(not yes);self.format.setEnabled(not yes);self.matrix.setEnabled(not yes and FORMATS[self.format.currentText()].family.startswith('yuv'))
