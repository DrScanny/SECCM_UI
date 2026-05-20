import sys
import pyqtgraph as pg
from pipython import GCSDevice, datarectools, pitools
import threading
import time
import functools

from PySide6.QtCore import Qt, QEvent
from PySide6.QtWidgets import (QApplication, QFileDialog, QMainWindow, QButtonGroup, QPushButton, 
                               QMessageBox, QTextEdit,  QHBoxLayout, QVBoxLayout, QDockWidget,
                               QMainWindow, QStatusBar, QWidget, QFrame, QListWidget,
                               QSplitter, QPlainTextEdit, QLabel, QTreeWidgetItem, QAbstractItemView,
                               QTreeWidget, QLineEdit, QGridLayout)

from Biologic import Biologic
from pipython import GCSDevice, datarectools, pitools
import UI_Settings


def handle_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Connection to device has failed {func.__name__}: {e}")
            return None  # Or a custom default response
    return wrapper

def PIconnect(PIdevice, serialnum):
    PIdevice.ConnectUSB(serialnum=serialnum) # Connect through USB
    print(PIdevice.qIDN().strip() )
    
def PIinit(PIdevice, type):

    match type:

        case 'Z':
            PIdevice.SVO(1, 1)
            PIdevice.FRF()
            while not all(list(PIdevice.qONT(1).values())):
                time.sleep(0.1)
            print(PIdevice.qFRF())

        case 'XY':
            PIdevice.SVO({1:1, 2:1})
            PIdevice.FRF()
            while not all(list(PIdevice.qONT([1,2]).values())):
                time.sleep(0.1)
            print(PIdevice.qFRF())

        case 'piezo':
            PIdevice.SVO('1',1)

    print("Device initialized")

class Device(QWidget):
    def __init__(self):
        super().__init__()

        self.layoutWidget= QVBoxLayout(); self.setLayout(self.layoutWidget)
        self.treeDevices= QTreeWidget(); self.layoutWidget.addWidget(self.treeDevices)
        self.treeDevices.setHeaderLabels(["Device", "Status"])
        self.treeDevices.setIndentation(10)

        self.potentiostat= Biologic()
        self.piezo= GCSDevice()
        self.Zstage= GCSDevice()
        self.XYstage= GCSDevice()

        self.treeItem_potentiostat= QTreeWidgetItem(["VMP-300", "    \U0001F534"]); self.treeDevices.addTopLevelItem(self.treeItem_potentiostat) 
        self.treeItem_piezo= QTreeWidgetItem(["Nanocube","    \U0001F534"]); self.treeDevices.addTopLevelItem(self.treeItem_piezo) 
        self.treeItem_Zstage= QTreeWidgetItem(["Mercury", "    \U0001F534"]); self.treeDevices.addTopLevelItem(self.treeItem_Zstage) 
        self.treeItem_XYstage= QTreeWidgetItem(["Olympus", "    \U0001F534"]); self.treeDevices.addTopLevelItem(self.treeItem_XYstage) 

        self.potentiostatIP= QTreeWidgetItem(self.treeItem_potentiostat); self.potentiostatIP.setFlags(self.potentiostatIP.flags() | Qt.ItemFlag.ItemIsEditable)
        self.piezoSerial= QTreeWidgetItem(self.treeItem_piezo); self.piezoSerial.setFlags(self.piezoSerial.flags() | Qt.ItemFlag.ItemIsEditable)
        self.Zserial= QTreeWidgetItem(self.treeItem_Zstage); self.Zserial.setFlags(self.Zserial.flags() | Qt.ItemFlag.ItemIsEditable)
        self.XYserial= QTreeWidgetItem(self.treeItem_XYstage); self.XYserial.setFlags(self.XYserial.flags() | Qt.ItemFlag.ItemIsEditable)

        self.potentiostatIP.setText(0, '192.168.2.2')
        self.piezoSerial.setText(0, '0125021719')
        self.Zserial.setText(0, '0026550002')
        self.XYserial.setText(0, '0125076674')

        self.buttonConnectPot= QPushButton('Connect'); self.treeDevices.setItemWidget(self.potentiostatIP, 1, self.buttonConnectPot)
        self.buttonConnectPot.clicked.connect(lambda: self.connectDevices(0))
        self.buttonConnectPiezo= QPushButton('Connect'); self.treeDevices.setItemWidget(self.piezoSerial, 1, self.buttonConnectPiezo)
        self.buttonConnectPiezo.clicked.connect(lambda: self.connectDevices(1))
        self.buttonConnectZ= QPushButton('Connect'); self.treeDevices.setItemWidget(self.Zserial, 1, self.buttonConnectZ)
        self.buttonConnectZ.clicked.connect(lambda: self.connectDevices(2))
        self.buttonConnectXY= QPushButton('Connect'); self.treeDevices.setItemWidget(self.XYserial, 1, self.buttonConnectXY)
        self.buttonConnectXY.clicked.connect(lambda: self.connectDevices(3))

        self.buttonConnectAll= QPushButton('Connect'); self.layoutWidget.addWidget(self.buttonConnectAll)
        self.buttonConnectAll.clicked.connect(self.connectAll)

    def connectDevices(self, device:int):
        address= self.treeDevices.topLevelItem(device).child(0).text(0)
        connected= False
     
        match device:
            case 0:
                self.potentiostat.connect(ip_address= address)
                connected= True

            case 1:
                PIconnect(self.piezo, address)
                if self.piezo.IsConnected():
                    connected= True
                    PIinit(self.piezo, 'piezo')
                 
            case 2:
                PIconnect(self.Zstage, address)
                if self.Zstage.IsConnected():
                    connected= True
                    PIinit(self.Zstage, 'Z')

            case 3:
                PIconnect(self.XYstage, address)
                if self.XYstage.IsConnected():
                    connected= True
                    PIinit(self.XYstage, 'XY')
                    
        if connected:
            self.treeDevices.topLevelItem(device).setText(1, '    \U0001F7E2')

    def connectAll(self):
        self.connectDevices(0)
        self.connectDevices(1)
        self.connectDevices(2)
        self.connectDevices(3)


if __name__ == '__main__':
    app= QApplication([])
    main= Device()
    main.show()
    app.exec()

