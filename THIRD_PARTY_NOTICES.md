# Third-party components

Prism Pixel uses PySide6 / Qt for Python and shiboken6 (LGPLv3 / GPLv3 / commercial options), NumPy (BSD-3-Clause), and OpenCV / opencv-python-headless (Apache-2.0 and bundled third-party licenses). PyInstaller is a build dependency (GPL with bootloader distribution exception).

The MSI includes the available distribution license/notice files under `licenses/`. Qt is dynamically linked; keep the DLLs and notices when distributing the portable build. Component rights remain with their respective authors.

- Qt: https://doc.qt.io/qtforpython-6/licenses.html
- NumPy: https://numpy.org/
- OpenCV: https://opencv.org/
- PyInstaller: https://pyinstaller.org/

Windows system fonts are used at runtime and are not redistributed. FFmpeg is used only as an optional independent validation tool, not bundled or required at runtime.
