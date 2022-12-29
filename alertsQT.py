# -*- coding: utf-8 -*-

import json
from base64 import standard_b64decode as b64decode
from configparser import ConfigParser
from pathlib import Path
from time import sleep
from typing import Any, List, Optional
from urllib.error import URLError
from urllib.request import urlopen

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QObject, Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineView
from PyQt5.QtWidgets import (QButtonGroup, QDialog, QLabel, QMessageBox,
                             QPushButton, QRadioButton, QSizePolicy, QToolBar,
                             QVBoxLayout, QWidget)

from png_files import png_files


class StatusAlarmed:

    def __init__(self, status_alarmed: Optional[List[Any]] = [0, False]) -> None:
        self.status_alarmed = status_alarmed

    def get(self) -> List[Any]:
        return self.status_alarmed

    def set(self, status_value: List[Any]) -> None:
        self.status_alarmed = status_value

    def clear(self):
        self.set([0, False])


status_alarmed = StatusAlarmed()

class ReadConfig:

    def __init__(self, ini_file) -> None:
        self.ini_file = ini_file
        self.file_msg_alarm_on = "msg_alarm_on.png"
        self.file_msg_alarm_off = "msg_alarm_off.png"
        self.root_dir = Path().cwd()
        self.base64_alarm_on = png_files["msg_alarm_on"]
        self.base64_alarm_off = png_files["msg_alarm_off"]
        self.check_config()

    def check_config(self) -> None:
        self.main_section = "main"
        self.config = ConfigParser(delimiters="|")
        self.config.read(self.ini_file, encoding="utf8")
        if not self.config.has_section(self.main_section):
            self.config.add_section(self.main_section)
        if not self.config.has_option(self.main_section, "msg_alarm_on"):
            self.set_value(self.main_section, "msg_alarm_on", self.base64_alarm_on)
        if not self.config.has_option(self.main_section, "msg_alarm_off"):
            self.set_value(self.main_section, "msg_alarm_off", self.base64_alarm_off)
        self.check_alarm_file()
        if not self.config.has_option(self.main_section, "oblast"):
            self.set_value(self.main_section, "oblast", "Sumy")
        if not self.config.has_option(self.main_section, "url_alarm_api"):
            self.set_value(self.main_section, "url_alarm_api", "https://sirens.in.ua/api/v1/")
        if not self.config.has_option(self.main_section, "url_alarm_map"):
            self.set_value(self.main_section, "url_alarm_map", "https://alerts.in.ua")
        self.save_config()
        self.oblast = self.config.get(self.main_section, "oblast")
        self.url_alarm_api = self.config.get(self.main_section, "url_alarm_api")
        self.url_alarm_map = self.config.get(self.main_section, "url_alarm_map")

    ''' get value from key in section ini file '''
    def get_value(self, section, key) -> str:
        return self.config.get(section, key)

    ''' save value to key for section '''
    def set_value(self, section, key, value) -> bool:
        self.config.set(section, key, value)
        return True

    ''' save to ini file '''
    def save_config(self) -> bool:
        with open(self.ini_file, "w") as configfile:
            self.config.write(configfile)
        return True

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

    def run(self) -> None:
        while True:
            try:
                ini_obj = ReadConfig(Path().cwd().joinpath("config.ini"))
                ini_obj_state1 = ini_obj
                with urlopen(ini_obj.url_alarm_api, timeout=10) as response:
                    window.label.setText(f"Робота в звичайному режимі...<br>Область для спостереження: <b>{ini_obj.oblast}<\b>")
                    window.label.setStyleSheet("color: green;")
                    data_raw = json.loads(response.read())
                    data = {k.lower(): v for k, v in data_raw.items()}
                    data_oblast = data.get(ini_obj.oblast.lower())
                    if not data_oblast is None and status_alarmed.get()[1] == False:
                        self.alarm_on.emit(True)
                        status_alarmed.set([status_alarmed.get()[0]+1, True])
                    if status_alarmed.get()[0] > 0 and status_alarmed.get()[1] == False:
                        self.alarm_on.emit(False)
                        status_alarmed.set([status_alarmed.get()[0]+1, False])
            except TimeoutError:
                window.label.setText("Затримка отримання даних.\nМожливо не працює сервер...")
                window.label.setStyleSheet("color: yellow;")
                sleep(10)
            except (URLError, ConnectionResetError):
                window.label.setText("Помилка отримання даних.\nПеревірте з'єднання...")
                window.label.setStyleSheet("color: red;")
                sleep(10)
            sleep(3)

    def stop(self):
        self._isRunning = False


class ChooseDialog(QDialog):

    def __init__(self, parent=None) -> None:
        super(ChooseDialog, self).__init__(parent=parent, flags=QtCore.Qt.WindowStaysOnTopHint)
        self.btn_text = "Слідкувати за"
        self.setWindowTitle("Вибір області для моніторингу")
        self.btngroup = QButtonGroup()
        self.btngroup.setExclusive(True)
        self.radiobuttons = [QRadioButton(oblast) for oblast in self.get_oblasts()]
        self.layout = QVBoxLayout()
        self.button = QPushButton()
        self.button.setText(self.btn_text)
        self.button.clicked.connect(self.save_config_oblast)
        for radiobutton in self.radiobuttons:
            self.btngroup.addButton(radiobutton)
            self.layout.addWidget(radiobutton)
            radiobutton.toggled.connect(self.set_button_text)
            if radiobutton.text().lower() == ini_obj.get_value("main", "oblast").lower():
                radiobutton.setChecked(True)
        self.setLayout(self.layout)
        self.layout.addWidget(self.button)
        self.resize(300, 64)

    ''' set the text on the button '''
    def set_button_text(self):
        self.button.setText(f"{self.btn_text} '{self.btngroup.checkedButton().text()}'")

    ''' save checked oblast to ini file '''
    def save_config_oblast(self):
        ini_obj.set_value("main", "oblast", self.btngroup.checkedButton().text())
        status_alarmed.clear()
        ini_obj.save_config()
        self.close()

    ''' return list of regions '''
    def get_oblasts(self):
        with urlopen(ini_obj.url_alarm_api, timeout=10) as response:
            return list(json.loads(response.read()).keys())


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None) -> None:
        super(MainWindow, self).__init__(flags=QtCore.Qt.WindowStaysOnTopHint|QtCore.Qt.CustomizeWindowHint|
            QtCore.Qt.WindowMaximizeButtonHint|QtCore.Qt.WindowCloseButtonHint|QtCore.Qt.WindowMinimizeButtonHint)
        title = "Мапа тривог України"
        self.setWindowTitle(title)
        self.setGeometry(self.geometry_rect())
        self.thread = QThread()
        self.worker = Worker()
        self.show()
        
        self.page = QWebEnginePage()
        # add browser object
        self.browser = QWebEngineView(self)
        self.browser.setPage(self.page)
        self.setCentralWidget(self.browser)
        url = QtCore.QUrl(ini_obj.url_alarm_map)
        self.page.setUrl(url)
        self.toolbar = QToolBar()
        self.toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.addToolBar(self.toolbar)
        self.choice_button = QPushButton(self)
        self.choice_button.setText("Змінити область\nспостереження")
        self.choice_button.setStyleSheet("color: #873e23;")
        self.choice_button.clicked.connect(self.show_choose_dialog)
        self.toolbar.addWidget(self.choice_button)
        self.spacer = QWidget()
        self.spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolbar.addWidget(self.spacer)
        self.label = QLabel(self)
        self.label.setTextFormat(Qt.RichText)
        self.label.setMargin(5)
        self.label.setStyleSheet("color: green;")  #border: 1px solid black;
        self.label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.label.setText(f"Робота в звичайному режимі...<br>Область для спостереження: <b>{ini_obj.oblast}<\b>")
        self.toolbar.addWidget(self.label)

    ''' show dialog for choice region '''
    def show_choose_dialog(self):
        choice_dialog = ChooseDialog(self)
        choice_dialog.exec_()

    def geometry_rect(self) -> QtCore.QRect:
        rect = QtWidgets.QApplication.desktop().availableGeometry()
        toolbar = 30
        win_width, win_height = rect.width()//4, rect.height() - toolbar
        x = rect.width() - win_width - 1
        return QtCore.QRect(x, toolbar, win_width, win_height)

    def check_alarm(self) -> None:
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.stop_thread)
        self.worker.alarm_on.connect(self.ShowMessage)
        self.thread.start()

    def ShowMessage(self) -> None:
        msgbox = QMessageBox(parent=self)
        self.i_color = 0
        timer = QTimer(msgbox, interval=1000, timeout=self.updatecolor)
        self.updatecolor()
        msgbox.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)
        msgbox.setWindowTitle("Повітряна тривога")
        msgbox.setDefaultButton(QMessageBox.Ok)
        if status_alarmed.get()[1]: # if alarm on
            msgbox.setIconPixmap(QPixmap(Path().cwd().joinpath("msg_alarm_on.png").__str__()))
            msgbox.setText("УВАГА! Повітряна тривога!\nВСІ В УКРИТТЯ!!!")
        else: # if alarm off
            msgbox.setIconPixmap(QPixmap(Path().cwd().joinpath("msg_alarm_off.png").__str__()))
            msgbox.setText("ВІДБІЙ ПОВІТРЯНОЇ ТРИВОГИ")
        timer.start()
        msgbox.exec_()

    ''' Apply style to QMessageBox and QPushButton '''
    def updatecolor(self):
        rnd_color = ['#6B717E', '#897C8D', '#818290', '#A66465', '#F15D50', '#F35041', '#E23525']
        if self.i_color > len(rnd_color)-1:
            self.i_color = 0
        self.setStyleSheet(f"QMessageBox{{background: {rnd_color[self.i_color]};}} QPushButton{{background-color: white;}}")
        self.i_color += 1

    def stop_thread(self) -> None:
        self.worker.stop()
        self.thread.quit()
        self.thread.wait()


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    ini_obj = ReadConfig(Path().cwd().joinpath("config.ini"))
    window = MainWindow()
    window.check_alarm()
    ret = app.exec_()
    sys.exit(ret)
