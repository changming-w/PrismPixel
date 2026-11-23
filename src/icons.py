"""Small, consistent vector command icons; no OS-dependent icon theme."""
from PySide6.QtCore import QByteArray,Qt
from PySide6.QtGui import QIcon,QPixmap,QPainter
from PySide6.QtSvg import QSvgRenderer

SHAPES={
'concentrate':'<path fill="#e8dcba" d="M2 12c5-8 15-8 20 0-5 8-15 8-20 0z"/><circle fill="#6e99bb" cx="12" cy="12" r="4"/><circle fill="#324a61" cx="12" cy="12" r="1.5"/>',
'history':'<circle fill="#d8e5ef" cx="13" cy="12" r="8"/><path d="M13 7v5l4 2M3 4v6h6M3 10a10 10 0 0 1 17-6"/>',
'file':'<path fill="#f5f7fa" d="M6 3h9l4 4v14H6z"/><path d="M15 3v5h4M9 12h7M9 16h5"/>',
'folder':'<path fill="#c9ac7d" d="M3 6h7l2 2h9v12H3z"/><path fill="#e7d2aa" d="M3 10h18l-2 10H3z"/>',
'session':'<rect fill="#d6ba91" x="4" y="7" width="16" height="13" rx="2"/><path d="M9 7V4h6v3M4 12h16"/>',
'save':'<path fill="#92b4d4" d="M4 3h14l3 3v15H4z"/><path fill="#f7f8fa" d="M8 3h8v6H8zM8 14h9v7H8z"/>',
'export':'<path fill="#f4f6f8" d="M4 3h11v18H4z"/><path d="M10 11h11m-4-4 4 4-4 4"/>',
'play':'<path fill="#73ad86" d="m7 4 14 8-14 8z"/>',
'stop':'<rect fill="#d47c79" x="5" y="5" width="14" height="14" rx="1"/>',
'original':'<rect fill="#e6edf3" x="3" y="4" width="18" height="16" rx="1"/><circle fill="#d9bc67" cx="16" cy="9" r="2"/><path fill="#83aa95" d="m4 19 6-8 4 5 3-3 3 6z"/>',
'heat':'<rect fill="#ec5e55" x="5" y="3" width="11" height="11"/><circle fill="#5c9ce3" cx="14" cy="15" r="6"/>',
'difference':'<rect fill="#e6d759" x="5" y="3" width="11" height="11"/><circle fill="#9eac51" cx="14" cy="15" r="6"/>',
'blend':'<rect fill="#63c67a" x="5" y="3" width="11" height="11"/><circle fill="#629ee1" fill-opacity=".85" cx="14" cy="15" r="6"/>',
'wipe':'<rect fill="#e5edf5" x="4" y="4" width="16" height="16"/><path fill="#91b8d3" d="M4 4h8v16H4z"/><path d="M12 2v20"/>',
'swap':'<path d="M3 8h17l-4-4m4 12H3l4 4M20 8l-4 4M3 16l4-4"/>',
'fit':'<rect fill="#f3f5f7" x="4" y="4" width="16" height="16"/><path d="M4 9h5V4m6 0v5h5M4 15h5v5m6 0v-5h5"/>',
'align':'<rect fill="#c3d7e5" x="3" y="5" width="7" height="14"/><rect fill="#e4d5ae" x="14" y="8" width="7" height="8"/><path d="M2 3h20M2 21h20m-4-13V5m-2 2 2-2 2 2m-2 9v3m-2-2 2 2 2-2"/>',
'actual':'<rect fill="#f5f6f8" x="4" y="4" width="16" height="16"/><path d="m8 9 2-2v10m4-8 2-2v10"/>',
'prev':'<path fill="#789dbb" d="m15 4-9 8 9 8z"/>',
'next':'<path fill="#789dbb" d="m9 4 9 8-9 8z"/>',
'prevdiff':'<path fill="#d5a55c" d="m5 13 7-8 7 8z"/><path d="M5 18h14"/>',
'nextdiff':'<path fill="#d5a55c" d="m5 10 7 8 7-8z"/><path d="M5 5h14"/>',
'focus':'<path d="M3 9V3h6m6 0h6v6M3 15v6h6m6 0h6v-6"/><rect fill="#b1c7d8" x="8" y="8" width="8" height="8"/>',
'demo':'<path fill="#d8b779" d="m3 11 9-8 9 8M6 9v12h12V9"/><path fill="#f3e8d3" d="M10 15h4v6h-4z"/>',
'help':'<circle fill="#c4d9e8" cx="12" cy="12" r="9"/><path d="M9 8c0-4 8-3 6 1-1 2-3 1-3 5M12 17v1"/>'}

def command_icon(name,dark=False):
    stroke='#bdc9d5' if dark else '#41484e'
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><g stroke="{stroke}" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round" fill="none">{SHAPES[name]}</g></svg>'
    image=QPixmap(48,48);image.fill(Qt.GlobalColor.transparent);painter=QPainter(image);QSvgRenderer(QByteArray(svg.encode())).render(painter);painter.end();return QIcon(image)
