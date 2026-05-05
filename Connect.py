import sys
import pyqtgraph as pg
from pipython import GCSDevice, datarectools, pitools
import threading
import time

from PySide6.QtCore import Qt, QEvent
from PySide6.QtWidgets import (QApplication, QFileDialog, QMainWindow, QButtonGroup, QPushButton, 
                               QMessageBox, QTextEdit,  QHBoxLayout, QVBoxLayout, QDockWidget,
                               QMainWindow, QStatusBar, QWidget, QFrame, QListWidget,
                               QSplitter, QPlainTextEdit, QLabel, QTreeWidgetItem, QAbstractItemView,
                               QTreeWidget, QLineEdit, QGridLayout)

from Biologic import Biologic

def _dots(stop_event, deviceName:str= ""):
    while not stop_event.is_set():
        for i in range(4):
            if stop_event.is_set(): break
            print(f"test to {deviceName} {"." * i}".ljust(0),  end="", flush=True) 
            time.sleep(0.5)

def _connectDevice(deviceName:str, connectFunc, TreeItem: QTreeWidgetItem, address:str):
    try:
        #stop_flag= threading.Event()
        #thread= threading.Thread(target=_dots, args=(stop_flag, deviceName))
        #thread.start()

        connectFunc(address)
        TreeItem.setText(1, '\U0001F7E2')

        #stop_flag.set()
        #thread.join()

    except:
        #stop_flag.set()
        #thread.join()
        print(f"\nConnection to {deviceName} failed")


class Device(QWidget):
    def __init__(self):
        super().__init__()

        self.potentiostatIP= QTreeWidgetItem(['IP', '192.168.2.2']); self.potentiostatIP.setFlags(self.potentiostatIP.flags() | Qt.ItemFlag.ItemIsEditable)
        self.piezoSerial= QTreeWidgetItem(['Serial', '0125021719']); self.piezoSerial.setFlags(self.piezoSerial.flags() | Qt.ItemFlag.ItemIsEditable)
        self.Zserial= QTreeWidgetItem(['Serial', '0026550002']); self.Zserial.setFlags(self.Zserial.flags() | Qt.ItemFlag.ItemIsEditable)
      
        self.layoutWidget= QVBoxLayout(); self.setLayout(self.layoutWidget)
        self.treeDevices= QTreeWidget(); self.layoutWidget.addWidget(self.treeDevices)
        self.treeDevices.setHeaderLabels(["Device", "Status"])
        self.treeDevices.addTopLevelItem(QTreeWidgetItem(["VMP-300", "\U0001F534"])); self.treeDevices.topLevelItem(0).addChild(self.potentiostatIP)
        self.treeDevices.addTopLevelItem(QTreeWidgetItem(["Nanocube", "\U0001F534"])); self.treeDevices.topLevelItem(1).addChild(self.piezoSerial)
        self.treeDevices.addTopLevelItem(QTreeWidgetItem(["Mercury", "\U0001F534"])); self.treeDevices.topLevelItem(2).addChild(self.Zserial)
        self.treeDevices.addTopLevelItem(QTreeWidgetItem(["Olympus", "\U0001F534"]))
   
        #region: Biologic
        self.potentiostat= Biologic()
        self.piezo= GCSDevice()
        self.Zstage= GCSDevice()

        self.buttonConnectPot= QPushButton('Connect');self.layoutWidget.addWidget(self.buttonConnectPot)

        #self.buttonConnectPot.clicked.connect(lambda:_connectDevice("VMP-300", self.potentiostat.connect, self.labelPotStatus, self.potentiostatIP))
        self.buttonConnectPot.clicked.connect(self.test)
        #endregion

    def test(self):
        self.treeDevices.topLevelItem(0).setText(1, '\U0001F7E2')

    def connectDevices(self):

        _connectDevice('VMP-300', self.potentiostat.connect(), self.treeDevices.topLevelItem(0), self.treeDevices.topLevelItem(0).child(0).text(1))

    def initDevices(self):
        stages= ['M-111.1DG']
        pitools.startup(self.Zstage,)

        
if __name__ == '__main__':
    app= QApplication([])
    main= Device()
    main.show()
    app.exec()

