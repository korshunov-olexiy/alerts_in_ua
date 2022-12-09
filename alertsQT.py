import sys

from PyQt5 import QtCore, QtGui
from PyQt5 import QtWidgets
from PyQt5 import QtWidgets as QtGui
from PyQt5.QtWebEngineWidgets import *
from screeninfo import get_monitors

monitor = get_monitors()[0]
app=QtWidgets.QApplication(sys.argv)

win = QtGui.QMainWindow(flags=QtCore.Qt.WindowStaysOnTopHint|
                                QtCore.Qt.CustomizeWindowHint|
                                QtCore.Qt.WindowMaximizeButtonHint|
                                QtCore.Qt.WindowCloseButtonHint|
                                QtCore.Qt.WindowMinimizeButtonHint)
w=QWebEngineView(win)
win.setCentralWidget(w)
w.load(QtCore.QUrl('https://alerts.in.ua'))

ws = monitor.width
hs = monitor.height
width = ws//4
height = hs - 75
x = ws - width + 5
y = 0

win.height =height
win.width = width
win.setGeometry(x, 30, width, height)

win.show()
app.exec_()
