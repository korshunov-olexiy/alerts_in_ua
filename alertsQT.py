from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWebEngineWidgets import QWebEngineView
from screeninfo import get_monitors


class Window(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__(flags=QtCore.Qt.WindowStaysOnTopHint|QtCore.Qt.CustomizeWindowHint|
                                    QtCore.Qt.WindowMaximizeButtonHint|QtCore.Qt.WindowCloseButtonHint|
                                    QtCore.Qt.WindowMinimizeButtonHint)
        title = "Мапа тревог України"
        self.setWindowTitle = title
        self.setGeometry(self.geometry_rect())
        self.show()

    def geometry_rect(self):
        monitor = get_monitors()[0]
        scree_width, screen_height = monitor.width, monitor.height
        win_width, win_height = scree_width//4, screen_height - 75
        x = scree_width - win_width + 5
        return QtCore.QRect(x, 30, win_width, win_height)


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = Window()

    browser = QWebEngineView(window)
    window.setCentralWidget(browser)
    browser.load(QtCore.QUrl('https://alerts.in.ua'))
    sys.exit(app.exec_())
