import json
from time import sleep
from urllib.request import urlopen

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QMessageBox


class Worker(QObject):
    finished = pyqtSignal()
    alarm_on = pyqtSignal(int)

    def __init__(self, oblast) -> None:
        super().__init__()
        self.oblast = oblast.lower()

    def run(self):
        with urlopen('https://sirens.in.ua/api/v1/', timeout=10) as response:
            sleep(3)
            data = json.loads(response.read()).lower()
            if data[self.oblast]:
                self.alarm_on.emit(1)
            return json.loads(data)
        # self.finished.emit()


class Window(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__(flags=QtCore.Qt.WindowStaysOnTopHint|QtCore.Qt.CustomizeWindowHint|
                                QtCore.Qt.WindowMaximizeButtonHint|QtCore.Qt.WindowCloseButtonHint|
                                QtCore.Qt.WindowMinimizeButtonHint)
        title = "Мапа тревог України"
        self.setWindowTitle(title)
        self.setGeometry(self.geometry_rect())
        self.show()
        self.thread = QThread(self)
        self.worker = Worker()

    def geometry_rect(self) -> QtCore.QRect:
        rect = QtWidgets.QApplication.desktop().availableGeometry()
        toolbar = 30
        win_width, win_height = rect.width()//4, rect.height() - toolbar
        x = rect.width() - win_width - 1
        return QtCore.QRect(x, toolbar, win_width, win_height)

    def check_alarm(self):
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.worker.deleteLater)
        # self.worker.alarm_on.connect(self.ShowMessage)
        self.thread.start()

    def ShowMessage(self):
        QMessageBox.question(window, "Title", f"msg", QMessageBox.Yes)


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    browser = QWebEngineView(window)
    window.setCentralWidget(browser)
    window.check_alarm()
    url = QtCore.QUrl("https://alerts.in.ua")
    browser.load(url)
    # QMessageBox.question(window, "Title", browser.page().findText("Сумська"), QMessageBox.Yes|QMessageBox.No)
    ret = app.exec_()
    window.thread.quit()
    window.thread.wait()
    sys.exit(ret)
