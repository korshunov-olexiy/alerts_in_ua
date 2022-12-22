# -*- coding: utf-8 -*-

import json
from pathlib import Path
from time import sleep
from urllib.request import urlopen

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QMessageBox


class Worker(QObject):
    finished = pyqtSignal()
    alarm_on = pyqtSignal(int)
    alarmed = False

    def __init__(self, oblast) -> None:
        super().__init__()
        self.oblast = oblast.lower()

    def run(self) -> None:
        while True:
            with urlopen('https://sirens.in.ua/api/v1/', timeout=10) as response:
                sleep(3)
                data_raw = json.loads(response.read())
                data = {k.lower(): v for k, v in data_raw.items()}
                data_oblast = data[self.oblast.lower()]
                if not data_oblast is None and not self.alarmed:
                    self.alarm_on.emit(True)
                    self.alarmed = True
                if data_oblast is None:
                    self.alarm_on.emit(False)
                    self.alarmed = False


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
        self.worker = Worker("Luhans'k")

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
        self.worker.alarm_on.connect(self.ShowMessage)
        self.thread.start()

    def ShowMessage(self):
        msgbox = QMessageBox(parent=self)
        msgbox.setIconPixmap(QPixmap(str(Path().cwd().joinpath("msg_icon.png"))))
        msgbox.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)
        msgbox.setWindowTitle("Повітряна тривога")
        msgbox.setDefaultButton(QMessageBox.Ok)
        if self.worker.alarmed: # if alarm on
            msgbox.setText("УВАГА! Повітряна тривога! ВСІ В УКРИТТЯ!!!")
        else: # if alarm off
            msgbox.setText("ВІДБІЙ ПОВІТРЯНОЇ ТРИВОГИ")
        msgbox.exec_()


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    browser = QWebEngineView(window)
    window.setCentralWidget(browser)
    window.check_alarm()
    url = QtCore.QUrl("https://alerts.in.ua/lite")
    browser.load(url)
    # QMessageBox.question(window, "Title", browser.page().findText("Сумська"), QMessageBox.Yes|QMessageBox.No)
    ret = app.exec_()
    window.thread.terminate()
    # window.thread.quit()
    # window.thread.wait()
    sys.exit(ret)
