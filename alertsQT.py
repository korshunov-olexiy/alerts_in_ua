from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5.QtWebEngineWidgets import *
from screeninfo import get_monitors

monitor = get_monitors()[0]

ws = monitor.width
hs = monitor.height
width = ws//4
height = hs - 75
x = ws - width + 5


if __name__ == "__main__":
    import sys

    app=QtWidgets.QApplication(sys.argv)
    win = QtWidgets.QMainWindow(flags=QtCore.Qt.WindowStaysOnTopHint|
                                    QtCore.Qt.CustomizeWindowHint|
                                    QtCore.Qt.WindowMaximizeButtonHint|
                                    QtCore.Qt.WindowCloseButtonHint|
                                    QtCore.Qt.WindowMinimizeButtonHint)
    win.height = height
    win.width = width
    win.setGeometry(x, 30, width, height)

    win_main = QWebEngineView(win)
    win.setCentralWidget(win_main)
    win_main.load(QtCore.QUrl('https://alerts.in.ua'))
    win.show()
    sys.exit(app.exec_())
