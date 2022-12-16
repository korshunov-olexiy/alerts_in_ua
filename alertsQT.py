from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView


class Window(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__(flags=QtCore.Qt.WindowStaysOnTopHint|QtCore.Qt.CustomizeWindowHint|
                                QtCore.Qt.WindowMaximizeButtonHint|QtCore.Qt.WindowCloseButtonHint|
                                QtCore.Qt.WindowMinimizeButtonHint)
        title = "Мапа тревог України"
        self.setWindowTitle(title)
        self.setGeometry(self.geometry_rect())
        self.show()

    def geometry_rect(self) -> QtCore.QRect:
        rect = QtWidgets.QApplication.desktop().availableGeometry()
        toolbar = 30
        win_width, win_height = rect.width()//4, rect.height() - toolbar
        x = rect.width() - win_width - 1
        return QtCore.QRect(x, toolbar, win_width, win_height)


if __name__ == "__main__":
    import sys

    def callback_function(html):
        QMessageBox.question(window, "Title", str(html), QMessageBox.Yes|QMessageBox.No)
        # print(html)

    def on_load_finished():
        browser.page().runJavaScript("document.querySelector('path.map-district:nth-child(18)')", callback_function)

    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    browser = QWebEngineView(window)
    window.setCentralWidget(browser)
    url = QtCore.QUrl("https://alerts.in.ua")
    browser.load(url)
    # QMessageBox.question(window, "Title", browser.page().findText("Сумська"), QMessageBox.Yes|QMessageBox.No)
    browser.loadFinished.connect(on_load_finished)
    sys.exit(app.exec_())
