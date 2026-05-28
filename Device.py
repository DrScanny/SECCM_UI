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
                               QTreeWidget, QLineEdit, QGridLayout, QGroupBox)

from Biologic import Biologic
import UI_Settings
from PI import PI


def handle_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Connection to device has failed {func.__name__}: {e}")
            return None  # Or a custom default response
    return wrapper

def _Vline(layout):
    line = QFrame()
    line.setFrameShape(QFrame.Shape.VLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    layout.addWidget(line)

def _LabelStyle(label:QLabel, state:bool):
    if state== False:
        label.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)
        label.setStyleSheet("background-color: #ff0000;")

    if state== True:
        label.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)
        label.setStyleSheet("background-color: #00FF00;")

    
class Device(QWidget):
    def __init__(self):
        super().__init__()

        self.potentiostat= Biologic()
        self.positioner= PI()

        self.potentiostatIP= '192.168.2.2'
        self.piezoSerial= '0125021719'
        self.Zserial= '0026550002'
        self.XYserial='0125076674'

        self.layoutWidget= QHBoxLayout(); self.setLayout(self.layoutWidget)
        self.frame= QFrame(); self.layoutWidget.addWidget(self.frame)
        self.frame.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)
        self.layoutDevice= QHBoxLayout(self.frame)

        self.buttonConnectAll= QPushButton('Connect All'); self.layoutDevice.addWidget(self.buttonConnectAll)
        self.buttonConnectAll.clicked.connect(self.connectAll)

        _Vline(self.layoutDevice)

        self.layoutPotentiostat= QVBoxLayout(); self.layoutDevice.addLayout(self.layoutPotentiostat)
        self.buttonConnectPot= QPushButton('Potentiostat'); self.layoutPotentiostat.addWidget(self.buttonConnectPot)
        self.buttonConnectPot.clicked.connect(lambda: self.connectDevices(self.labelPot, self.potentiostatIP, 'Pot'))
        self.labelPot= QLabel('   '); self.layoutPotentiostat.addWidget(self.labelPot)
        _LabelStyle(self.labelPot, False)

        _Vline(self.layoutDevice)

        self.layoutPiezo= QVBoxLayout(); self.layoutDevice.addLayout(self.layoutPiezo)
        self.buttonConnectPiezo= QPushButton('Piezo'); self.layoutPiezo.addWidget(self.buttonConnectPiezo)
        self.buttonConnectPiezo.clicked.connect(lambda: self.connectDevices(self.labelPiezo, self.piezoSerial, 'Pz'))
        self.labelPiezo= QLabel('   '); self.layoutPiezo.addWidget(self.labelPiezo)
        _LabelStyle(self.labelPiezo, False)

        _Vline(self.layoutDevice)

        self.layoutZstage= QVBoxLayout(); self.layoutDevice.addLayout(self.layoutZstage)
        self.buttonConnectZstage= QPushButton('Z-stage'); self.layoutZstage.addWidget(self.buttonConnectZstage)
        self.buttonConnectZstage.clicked.connect(lambda: self.connectDevices(self.labelZstage, self.Zserial, 'Z'))
        self.labelZstage= QLabel('   '); self.layoutZstage.addWidget(self.labelZstage)
        _LabelStyle(self.labelZstage, False)

        _Vline(self.layoutDevice)

        self.layoutXYstage= QVBoxLayout(); self.layoutDevice.addLayout(self.layoutXYstage)
        self.buttonConnectXYstage= QPushButton('XY-stage'); self.layoutXYstage.addWidget(self.buttonConnectXYstage)
        self.buttonConnectXYstage.clicked.connect(lambda: self.connectDevices(self.labelXYstage, self.XYserial, 'XY'))
        self.labelXYstage= QLabel('   '); self.layoutXYstage.addWidget(self.labelXYstage)
        _LabelStyle(self.labelXYstage, False)
     

    def connectDevices(self, label:QLabel, address:str, type:str):

        connectionStatus= False

        if type== 'Pot':
            connectionStatus= self.potentiostat.connect(ip_address= address)

        else:
            connectionStatus= self.positioner.connectPositioner(address, type)
     

        if connectionStatus:
            _LabelStyle(label,True)

    def connectAll(self):
        self.connectDevices(self.labelPot, self.potentiostatIP, 'Pot')
        self.connectDevices(self.labelPiezo, self.piezoSerial, 'Pz')
        self.connectDevices(self.labelZstage, self.Zserial, 'Z')
        self.connectDevices(self.labelXYstage, self.XYserial, 'XY')


if __name__ == '__main__':
    app= QApplication([])
    main= Device()
    main.show()
    app.exec()

