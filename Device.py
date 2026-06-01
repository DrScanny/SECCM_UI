from PySide6.QtCore import Qt, QEvent, QObject, Signal, Slot, QThread, QThreadPool, QRunnable, Slot
from PySide6.QtWidgets import (QApplication, QFileDialog, QMainWindow, QButtonGroup, QPushButton, 
                               QMessageBox, QTextEdit,  QHBoxLayout, QVBoxLayout, QDockWidget,
                               QMainWindow, QStatusBar, QWidget, QFrame, QListWidget,
                               QSplitter, QPlainTextEdit, QLabel, QTreeWidgetItem, QAbstractItemView,
                               QTreeWidget, QLineEdit, QGridLayout, QGroupBox)
#from qtwidgets import Toggle, AnimatedToggle

import sys
import pyqtgraph as pg
from pipython import GCSDevice
import time
import functools
from PI import PI
from BiologicAPI.Biologic import Biologic


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
    line.setFrameShadow(QFrame.Shadow.Raised)
    layout.addWidget(line)
  
def _LabelStatus(label:QLabel, state:bool):
    if state== False:
        label.setText(' \U0001F534 ')
        #label.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)
        #label.setStyleSheet("background-color: #ff0000;")

    if state== True:
        label.setText(' \U0001F7E2 ')
        #label.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)
        #label.setStyleSheet("background-color: #00FF00;")
        
class FrameDevice(QWidget):
    def __init__(self, layout, buttonText:str):
        super().__init__()

        self.frame= QFrame(); layout.addWidget(self.frame)
        self.frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        self.frame.setContentsMargins(1,1,1,1)
        self.frameLayout= QGridLayout(self.frame); self.frameLayout.setSpacing(1)
        self.labelDevice= QLabel(buttonText); self.frameLayout.addWidget(self.labelDevice,0,0)
        self.labelDevice.setContentsMargins(0,0,0,0)
        self.labelStatus= QLabel(''); self.frameLayout.addWidget(self.labelStatus,0,1)
        _LabelStatus(self.labelStatus, False)
        self.button= QPushButton('connect'); self.frameLayout.addWidget(self.button,1,0,1,2)
    
class Device(QWidget):
    def __init__(self):
        super().__init__()

        self.potentiostat= {'channel':1, 'id_':None, 'api':None, 'board_type': None}
        self.PzStage= GCSDevice()
        self.Zstage= GCSDevice()
        self.XYstage= GCSDevice()

        self.potentiostatIP= '192.168.2.2'
        self.piezoSerial= '0125021719'
        self.Zserial= '0026550002'
        self.XYserial='0125076674'

        self.layoutMain= QHBoxLayout(); self.setLayout(self.layoutMain)
        self.frame= QFrame(); self.layoutMain.addWidget(self.frame)
        self.frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Plain)
        self.layoutDevice= QHBoxLayout(self.frame)

        self.buttonConnectAll= QPushButton('Connect'); self.layoutDevice.addWidget(self.buttonConnectAll)
        self.buttonConnectAll.clicked.connect(self.connectAll)
        self.buttonConnectAll.setFixedSize(100,40)

        self.VMP300= FrameDevice(self.layoutDevice, 'VMP300')
        self.XY= FrameDevice(self.layoutDevice, 'XY-Stage')
        self.Z= FrameDevice(self.layoutDevice, 'Z-Stage')
        self.Pz= FrameDevice(self.layoutDevice, 'Piezo')

        self.VMP300.button.clicked.connect(lambda: self.connectPotentiostat())
        self.XY.button.clicked.connect(lambda: self.connectPositioner(self.XY.labelStatus, self.XYstage, self.XYserial, 'XY'))
        self.Z.button.clicked.connect(lambda: self.connectPositioner(self.Z.labelStatus, self.Zstage, self.Zserial, 'Z'))
        self.Pz.button.clicked.connect(lambda: self.connectPositioner(self.Pz.labelStatus, self.PzStage, self.piezoSerial, 'Pz'))

    def connectPositioner(self, label:QLabel, positioner:GCSDevice, serialnum:str, type:str):
     
        self.PIthread= QThread()
        self.worker= PI()
        self.worker.moveToThread(self.PIthread)
        self.PIthread.started.connect(lambda: self.worker.connectPI(positioner, type, serial= serialnum))
        self.worker.connection.connect(lambda connected: _LabelStatus(label, connected))
        self.worker.finished.connect(self.PIthread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.PIthread.finished.connect(self.PIthread.deleteLater)

        self.PIthread.start()

    def connectPotentiostat(self):
        self.BiologicThread= QThread()
        self.worker= Biologic(self.potentiostat)
        self.worker.moveToThread(self.BiologicThread)
        self.BiologicThread.started.connect(lambda: self.worker.connectBiologic(self.potentiostatIP))
        self.worker.connection.connect(self.potentiostatUpdate)
        self.worker.finished.connect(self.BiologicThread.quit)
       
        self.worker.finished.connect(lambda: _LabelStatus(self.VMP300.labelStatus, True))
        self.worker.finished.connect(self.worker.deleteLater)
        self.BiologicThread.finished.connect(self.BiologicThread.deleteLater)

        self.BiologicThread.start()

    def connectAll(self):
        self.connectPotentiostat()
        self.connectPositioner(self.Pz.labelStatus, self.PzStage, self.piezoSerial, 'Pz')
        self.connectPositioner(self.Z.labelStatus, self.Zstage, self.Zserial, 'Z')
        self.connectPositioner(self.XY.labelStatus, self.XYstage, self.XYserial, 'XY')

    def potentiostatUpdate(self, connection):
        print('potentiostat connected!')
        self.potentiostat= connection
    

if __name__ == '__main__':
    app= QApplication([])
    main= Device()
    main.show()
    app.exec()

