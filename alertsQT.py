# -*- coding: utf-8 -*-

import json
from base64 import standard_b64decode as b64decode
from configparser import ConfigParser
from pathlib import Path
from time import sleep
from urllib.request import urlopen

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QPushButton, QRadioButton, QGroupBox, QGridLayout, QButtonGroup

from png_files import png_files


class ReadConfig:
    def __init__(self, ini_file) -> None:
        self.ini_file = ini_file
        if not self.ini_file.exists():
            self.choose_oblast()
        self.file_msg_alarm_on = "msg_alarm_on.png"
        self.file_msg_alarm_off = "msg_alarm_off.png"
        self.root_dir = Path().cwd()
        self.base64_alarm_on = png_files["msg_alarm_on"]
        self.base64_alarm_off = png_files["msg_alarm_off"]
        self.check_config()

    def choose_oblast() -> str:
        pass

    def check_config(self) -> None:
        self.main_section = "main"
        self.config = ConfigParser(delimiters="|")
        self.config.read(self.ini_file, encoding="utf8")
        self.config_state1 = self.config
        if not self.config.has_section(self.main_section):
            self.config.add_section(self.main_section)
        if not self.config.has_option(self.main_section, "msg_alarm_on"):
            self.config.set(self.main_section, "msg_alarm_on", self.base64_alarm_on)
        if not self.config.has_option(self.main_section, "msg_alarm_off"):
            self.config.set(self.main_section, "msg_alarm_off", self.base64_alarm_off)
        self.check_alarm_file()
        if not self.config.has_option(self.main_section, "oblast"):
            self.config.set(self.main_section, "oblast", "Sumy")
        if not self.config.has_option(self.main_section, "url_alarm_api"):
            self.config.set(self.main_section, "url_alarm_api", "https://sirens.in.ua/api/v1/")
        if not self.config.has_option(self.main_section, "url_alarm_map"):
            self.config.set(self.main_section, "url_alarm_map", "https://alerts.in.ua")
        if self.config is self.config_state1: # save config in ini-file
            with open(self.ini_file, "w") as configfile:
                self.config.write(configfile)
        self.oblast = self.config.get(self.main_section, "oblast")
        self.url_alarm_api = self.config.get(self.main_section, "url_alarm_api")
        self.url_alarm_map = self.config.get(self.main_section, "url_alarm_map")

    def check_alarm_file(self) -> None:
        file_on = self.root_dir.joinpath(self.file_msg_alarm_on)
        if not file_on.exists():
            with open(file_on, "wb") as f:
                f.write(b64decode(self.base64_alarm_on))
        file_off = self.root_dir.joinpath(self.file_msg_alarm_off)
        if not file_off.exists():
            with open(file_off, "wb") as f:
                f.write(b64decode(self.base64_alarm_off))


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

    def stop(self):
        self._isRunning = False


class ChooseDialog(QDialog):

    def __init__(self, parent=None) -> None:
        super(ChooseDialog, self).__init__(parent=parent, flags=QtCore.Qt.WindowStaysOnTopHint)
        self.btn_text = "Слідкувати за"
        self.setWindowTitle("Вибір області для моніторингу")
        self.group = QButtonGroup()
        self.group.setExclusive(True)
        self.radiobuttons = [QRadioButton(d) for d in self.get_oblasts()]
        self.layout = QVBoxLayout()
        self.button = QPushButton()
        self.button.setText(self.btn_text)
        for radiobutton in self.radiobuttons:
            self.group.addButton(radiobutton)
            self.layout.addWidget(radiobutton)
            radiobutton.toggled.connect(self.set_command_button_text)
            if radiobutton.text().lower() == "sumy":
                radiobutton.setChecked(True)
        self.setLayout(self.layout)
        self.layout.addWidget(self.button)
        self.resize(300, 64)

    def set_command_button_text(self):
        self.button.setText(f"{self.btn_text} '{self.group.checkedButton().text()}'")

    ''' get text of checked radiobutton or empty '''
    def get_checked_radiobutton(self):
        for elem in self.groupbox.children():
            if isinstance(elem, QtWidgets.QRadioButton) and elem.isChecked():
                return elem.text()
        return ""

    ''' возвращает список областей '''
    def get_oblasts(self):
        with urlopen(ini_obj.url_alarm_api, timeout=10) as response:
            return list(json.loads(response.read()).keys())


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None) -> None:
        super(MainWindow, self).__init__(flags=QtCore.Qt.WindowStaysOnTopHint|QtCore.Qt.CustomizeWindowHint|
                                QtCore.Qt.WindowMaximizeButtonHint|QtCore.Qt.WindowCloseButtonHint|
                                QtCore.Qt.WindowMinimizeButtonHint)
        title = "Мапа тривог України"
        self.setWindowTitle(title)
        self.setGeometry(self.geometry_rect())
        self.thread = QThread()
        self.worker = Worker()
        self.show()
        choice_dialog = ChooseDialog()
        # choice_dialog.show()
        choice_dialog.exec_()

    def geometry_rect(self) -> QtCore.QRect:
        rect = QtWidgets.QApplication.desktop().availableGeometry()
        toolbar = 30
        win_width, win_height = rect.width()//4, rect.height() - toolbar
        x = rect.width() - win_width - 1
        return QtCore.QRect(x, toolbar, win_width, win_height)

    def check_alarm(self):
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.stop_thread)
        self.worker.alarm_on.connect(self.ShowMessage)
        self.thread.start()

    def ShowMessage(self):
        msgbox = QMessageBox(parent=self)
        msgbox.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)
        msgbox.setWindowTitle("Повітряна тривога")
        msgbox.setDefaultButton(QMessageBox.Ok)
        if self.worker.status_alarmed: # if alarm on
            msgbox.setIconPixmap(QPixmap(Path().cwd().joinpath("msg_alarm_on.png").__str__()))
            msgbox.setText("УВАГА! Повітряна тривога!\nВСІ В УКРИТТЯ!!!")
        else: # if alarm off
            msgbox.setIconPixmap(QPixmap(Path().cwd().joinpath("msg_alarm_off.png").__str__()))
            msgbox.setText("ВІДБІЙ ПОВІТРЯНОЇ ТРИВОГИ")
        msgbox.exec_()

    def stop_thread(self):
        self.worker.stop()
        self.thread.quit()
        self.thread.wait()


if __name__ == "__main__":
    import sys

    ini_obj = ReadConfig(Path().cwd().joinpath("config.ini"))
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    browser = QWebEngineView(window)
    window.setCentralWidget(browser)
    window.check_alarm()
    url = QtCore.QUrl(ini_obj.url_alarm_map)
    browser.load(url)
    ret = app.exec_()
    sys.exit(ret)
