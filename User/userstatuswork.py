# _*_ coding=utf-8 _*_
from userstatus import Ui_Dialog
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QDialog, QMessageBox

from PyQt5 import QtCore
import sys

class MyStatus(QDialog,Ui_Dialog):
    signal=QtCore.pyqtSignal(list)
    def __init__(self):
        super(MyStatus, self).__init__()
        self.setupUi(self)
        self.label_3.setText(QtCore.QDateTime.currentDateTime().toString())

    def setUsr(self,usr):
        self.label_4.setText(usr)
    def checklogout(self):
        quitclick=QMessageBox.warning(self, "Warning", "Quit?", QMessageBox.Cancel|QMessageBox.Yes)
        if quitclick==QMessageBox.Yes:
            self.signal.emit([self.label_4.text(),QtCore.QTime.currentTime().toString(QtCore.Qt.DefaultLocaleLongDate)])
            self.close()
'''
if __name__=='__main__':
    app = QApplication(sys.argv)
    Mystatus =MyStatus()
    Mystatus.show()
    sys.exit(app.exec_())'''