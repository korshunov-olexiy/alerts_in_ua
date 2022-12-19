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

    def callback_function(bool_res):
        # if bool(bool_res):
        QMessageBox.question(window, "Title", str(bool_res), QMessageBox.Yes)

    def on_load_finished():
        browser.page().runJavaScript('''
        function GetOblast(findObl){
            let mycls = document.getElementsByClassName('map-district hour-0 active  air-raid ');
            for (let i = 0; i < mycls.length; i++){
                if (mycls[i].attributes['data-oblast'].nodeValue.toLowerCase().includes(findObl.toLowerCase())){
                    return true;
                }
            }
            return false;
        };
        GetOblast('Сумська');
        ''', callback_function)

    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    browser = QWebEngineView(window)
    window.setCentralWidget(browser)
    url = QtCore.QUrl("https://alerts.in.ua")
    browser.load(url)
    # QMessageBox.question(window, "Title", browser.page().findText("Сумська"), QMessageBox.Yes|QMessageBox.No)
    browser.loadFinished.connect(on_load_finished)
    sys.exit(app.exec_())
