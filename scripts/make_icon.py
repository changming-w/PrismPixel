from pathlib import Path
import struct
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage,QPainter,QColor,QLinearGradient,QPen
from PySide6.QtCore import Qt,QBuffer,QIODevice,QRectF
app=QApplication([]);out=Path(__file__).resolve().parents[1]/'assets';out.mkdir(exist_ok=True)
image=QImage(256,256,QImage.Format.Format_ARGB32);image.fill(Qt.GlobalColor.transparent);p=QPainter(image);p.setRenderHint(QPainter.RenderHint.Antialiasing)
p.setPen(Qt.PenStyle.NoPen);g=QLinearGradient(0,0,256,256);g.setColorAt(0,QColor('#172d4b'));g.setColorAt(1,QColor('#102036'));p.setBrush(g);p.drawRoundedRect(QRectF(3,3,250,250),54,54)
for x,y,c in [(48,48,'#ff7279'),(136,48,'#6fd5b2'),(48,136,'#69aaff'),(136,136,'#d1e5ff')]:
    p.setBrush(QColor(c));p.drawRoundedRect(QRectF(x,y,72,72),16,16)
p.end();image.save(str(out/'pixel.png'));buffer=QBuffer();buffer.open(QIODevice.OpenModeFlag.WriteOnly);image.save(buffer,'PNG');data=bytes(buffer.data());(out/'pixel.ico').write_bytes(struct.pack('<HHH',0,1,1)+struct.pack('<BBBBHHII',0,0,0,0,1,32,len(data),22)+data)
for name,up in [('down',False),('up',True)]:
    a=QImage(16,12,QImage.Format.Format_ARGB32);a.fill(Qt.GlobalColor.transparent);p=QPainter(a);p.setRenderHint(QPainter.RenderHint.Antialiasing);p.setPen(QPen(QColor('#61748b'),1.8));p.drawLine(4,8 if up else 4,8,4 if up else 8);p.drawLine(8,4 if up else 8,12,8 if up else 4);p.end();a.save(str(out/(name+'.png')))
