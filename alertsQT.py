# -*- coding: utf-8 -*-

import json
from configparser import ConfigParser
from pathlib import Path
from time import sleep
from urllib.request import urlopen

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QMessageBox


class ReadConfig:
    def __init__(self, ini_file) -> None:
        config = ConfigParser(delimiters="=")
        config.read(ini_file, encoding="utf-8")
        flag_save = False
        if not config.has_section("main"):
            # set default value of option 'oblast' in 'main' section
            config.add_section("main")
            flag_save = True
        if not config.has_option("main", "oblast"):
            config["main"] = {"oblast": "Sumy"}
            flag_save = True
        if not config.has_option("main", "url_alarm_api"):
            config.set("main", "url_alarm_api", "https://sirens.in.ua/api/v1/")
            flag_save = True
        if not config.has_option("main", "url_alarm_map"):
            config.set("main", "url_alarm_map", "https://alerts.in.ua")
            flag_save = True
        if flag_save: # save config in ini-file
            with open(ini_file, "w") as configfile:
                config.write(configfile)
        self.oblast = config.get("main", "oblast")
        self.url_alarm_api = config.get("main", "url_alarm_api")
        self.url_alarm_map = config.get("main", "url_alarm_map")


class Worker(QObject):
    finished = pyqtSignal()
    alarm_on = pyqtSignal(int)

    def __init__(self) -> None:
        super().__init__()
        self.status_alarmed = [0, False, False]

    def run(self) -> None:
        while True:
            with urlopen(ini_obj.url_alarm_api, timeout=10) as response:
                sleep(3)
                data_raw = json.loads(response.read())
                data = {k.lower(): v for k, v in data_raw.items()}
                data_oblast = data[ini_obj.oblast.lower()]
                if not data_oblast is None and not self.status_alarmed[1]:
                    self.alarm_on.emit(True)
                    self.status_alarmed = [self.status_alarmed[0]+1, True, False]
                if data_oblast is None and not self.status_alarmed[2] and self.status_alarmed[1] != 0:
                    self.alarm_on.emit(False)
                    self.status_alarmed = [self.status_alarmed[0]+1, False, True]


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
        self.worker.alarm_on.connect(self.ShowMessage)
        self.thread.start()

    def ShowMessage(self):
        msgbox = QMessageBox(parent=self)
        msgbox.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)
        msgbox.setWindowTitle("Повітряна тривога")
        msgbox.setDefaultButton(QMessageBox.Ok)
        if self.worker.status_alarmed: # if alarm on
            msgbox.setIconPixmap(QPixmap(str(Path().cwd().joinpath("msg_alarm_on.png"))))
            msgbox.setText("УВАГА! Повітряна тривога!\nВСІ В УКРИТТЯ!!!")
        else: # if alarm off
            msgbox.setIconPixmap(QPixmap(str(Path().cwd().joinpath("msg_alarm_off.png"))))
            msgbox.setText("ВІДБІЙ ПОВІТРЯНОЇ ТРИВОГИ")
        msgbox.exec_()


if __name__ == "__main__":
    import sys

    ini_obj = ReadConfig(Path().cwd().joinpath("config.ini"))
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    browser = QWebEngineView(window)
    window.setCentralWidget(browser)
    window.check_alarm()
    url = QtCore.QUrl(ini_obj.url_alarm_map)  # /lite
    browser.load(url)
    ret = app.exec_()
    window.thread.terminate()
    # window.thread.quit()
    # window.thread.wait()
    sys.exit(ret)
