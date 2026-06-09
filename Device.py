from PySide6.QtCore import Qt, QEvent, QObject, Signal, Slot, QThread, QThreadPool, QRunnable, Slot
from PySide6.QtWidgets import (QApplication, QFileDialog, QMainWindow, QButtonGroup, QPushButton, 
                               QMessageBox, QTextEdit,  QHBoxLayout, QVBoxLayout, QDockWidget,
                               QMainWindow, QStatusBar, QWidget, QFrame, QListWidget,
                               QSplitter, QPlainTextEdit, QLabel, QTreeWidgetItem, QAbstractItemView,
                               QTreeWidget, QLineEdit, QGridLayout, QGroupBox)
#from qtwidgets import Toggle, AnimatedToggle


from pipython import GCSDevice, GCSError, gcserror
import time
from PI import PI
from BiologicAPI.Biologic import Biologic


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

class PIconnect(QObject): 
        deviceNames= {'Z': 'Z-stage -Mercury-', 'XY':'XY-stage -Olympus-', 'Pz': 'Piezo -Nanocube- '}

        message= Signal(str)
        status= Signal(bool)
        progress= Signal(object)
        finished= Signal()              

        def __init__(self, PIdevice:GCSDevice, type:str, serial:str):
            super().__init__()

            
            self.PIdevice= PIdevice
            self.PIname= PIconnect.deviceNames[type]
            self.type= type
            self.serial= serial
            
        def connectPIdevice(self):

            try:
                # Connect to PI device through USB
                self.PIdevice.ConnectUSB(self.serial) 

                # Depending on the positioner, the initialization is different

                if  self.type=='Z': #For Z-stage Connect -> Activate Servo -> Reference     
                    
                    self.PIdevice.gcscommands.SVO(1,1)
                    self.PIdevice.gcscommands.VEL(1, 1)
                    self.PIdevice.FPL()
        
                elif  self.type=='XY': #For XY-stage Connect -> Activate Servo -> Reference     
                    
                    self.PIdevice.gcscommands.SVO({1:1, 2:1})
                    self.PIdevice.gcscommands.VEL({1:1, 2:1})
                    self.PIdevice.FRF()

                elif self.type=='Pz': #For Piezo Connect -> Activate Servo   
                    
                    self.PIdevice.gcscommands.SVO({1:1, 2:1, 3:1})
                    self.PIdevice.gcscommands.VEL({1:1, 2:1, 3:1})

                #Wait until all stages are ready
                while not all(list(self.PIdevice.qONT().values())): 
                    time.sleep(0.1)

                if self.PIdevice.gcscommands.IsConnected():
                        print(f"[EVENT] Connection to {self.PIname}, ready to be used!")
                        self.status.emit(True)

            except IOError:
                print(f'[ERROR] Connection to {self.PIname}: Checked if controller is turned ON.')
                self.status.emit(False)

            except GCSError as err:
                print(f"[ERROR] Connection to {self.PIname}: {GCSError(err)}")

            except Exception as err:
                self.status.emit(False)
                print(f"[ERROR] Connection to {self.PIname}: {err}")
                
            finally:
                self.finished.emit()
            
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

    startCommand= Signal(object)
    endCommand= Signal(object)

    def __init__(self):
        super().__init__()

        self.potentiostat= {'api':None, 'channel':1, 'board_type': None, 'id_': None}
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

        self.VMP300.button.clicked.connect(lambda: self.connectPotentiostat(self.VMP300.labelStatus))
        self.XY.button.clicked.connect(lambda: self.connectPositioner(self.XY.labelStatus, self.XYstage, self.XYserial, 'XY'))
        self.Z.button.clicked.connect(lambda: self.connectPositioner(self.Z.labelStatus, self.Zstage, self.Zserial, 'Z'))
        self.Pz.button.clicked.connect(lambda: self.connectPositioner(self.Pz.labelStatus, self.PzStage, self.piezoSerial, 'Pz'))

    def connectPositioner(self, label:QLabel, positioner:GCSDevice, serialnum:str, type:str):
        self.newThread= QThread()
        self.newWorker= PIconnect(positioner, type, serialnum)
        self.newWorker.moveToThread(self.newThread)
        self.newThread.started.connect(self.newWorker.connectPIdevice)
    
        self.newWorker.message.connect(lambda m: print(m))
        self.newWorker.progress.connect(lambda m: print(m))
        self.newWorker.status.connect(lambda status:  _LabelStatus(label, status))
        self.newThread.finished.connect(lambda: self.endCommand.emit({'end':0}))

        self._threadClose(self.newWorker, self.newThread)
 
        self.startCommand.emit({'start': f"Connecting to {PIconnect.deviceNames[type]}... "})
        self.newThread.start()
       
    def connectPotentiostat(self, label:QLabel):

        self.newThread= QThread()
        self.newWorker= Biologic(self.potentiostat)
        self.newWorker.moveToThread(self.newThread)
        self.newThread.started.connect(self.newWorker.connectBiologic)
    
        self.newWorker.biologic.connect(lambda settings: setattr(self, 'potentiostat', settings))
        self.newWorker.biologic.connect(lambda: _LabelStatus(label, True))
        self.newThread.finished.connect(lambda: self.endCommand.emit({'end':0}))

        self._threadClose(self.newWorker, self.newThread)

        self.startCommand.emit({'start': "Connecting to VMP-300... "})
        self.newThread.start()
        
    def connectAll(self):
        self.connectPotentiostat(self.VMP300.labelStatus)
        self.connectPositioner(self.Pz.labelStatus, self.PzStage, self.piezoSerial, 'Pz')
        self.connectPositioner(self.Z.labelStatus, self.Zstage, self.Zserial, 'Z')
        self.connectPositioner(self.XY.labelStatus, self.XYstage, self.XYserial, 'XY')

    def _threadClose(self, worker, thread:QThread):
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

if __name__ == '__main__':
    app= QApplication([])
    main= Device()
    main.show()
    app.exec()

