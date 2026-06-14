from PySide6.QtCore import Qt, QEvent, QObject, Signal, Slot, QThread, QThreadPool, QRunnable, Slot, QSize
from PySide6.QtGui import QFont, QIcon, QPixmap
from PySide6.QtWidgets import (QApplication, QFileDialog, QMainWindow, QButtonGroup, QPushButton, 
                               QMessageBox, QTextEdit,  QHBoxLayout, QVBoxLayout, QDockWidget,
                               QMainWindow, QStatusBar, QWidget, QFrame, QListWidget,
                               QSplitter, QPlainTextEdit, QLabel, QTreeWidgetItem, QAbstractItemView,
                               QTreeWidget, QLineEdit, QGridLayout, QGroupBox, QStyle)

#External packages
import time
from pipython import GCSDevice, GCSError

#Personal packages
from PI import PI
from BiologicAPI.Biologic import Biologic
from QToggle import QToggle


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

class threadInit():
    def __init__(self, workerClass, *arg):
        self.thread= QThread()
        self.worker= workerClass(*arg)

        self.worker.moveToThread(self.thread)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

class Device(QWidget):

    def __init__(self, layout, buttonText:str, type:str, serial:str):
        super().__init__()
        deviceNames= {'BL': 'VMP-300', 'Z': 'Z-stage *Mercury*', 'XY':'XY-stage *Olympus*', 'Pz': 'Piezo *Nanocube*'}
        
        self.serial= serial
        self.type= type
        self.name= deviceNames[type]
        self.positioner= GCSDevice()
        self.potentiostat= {'api':None, 'channel':1, 'board_type': None, 'id_': None}
                       
        self.frame= QFrame(); layout.addWidget(self.frame)
        self.frame.setFrameStyle(QFrame.Shape.Panel| QFrame.Shadow.Raised)
        self.frame.setLineWidth(3); self.frame.setMidLineWidth(3)
        self.frameLayout= QGridLayout(self.frame); self.frameLayout.setSpacing(1)
        self.frameLayout.setSpacing(5)

        self.labelDevice= QLabel(buttonText); self.frameLayout.addWidget(self.labelDevice,0,0)
        self.labelDevice.setFont(QFont("Arial", 10, QFont.Weight.Bold)) 
        self.labelDevice.setAlignment(Qt.AlignmentFlag.AlignCenter) 

        self.toggle= QToggle(); self.frameLayout.addWidget(self.toggle,1,0)

class PIconnect(QObject): 

        message= Signal(str)
        status= Signal(bool)
        progress= Signal(object)
        connection= Signal(object)
        finished= Signal()              

        def __init__(self, PIdevice:Device):
            super().__init__()
            self.deviceNames= {'BL': 'VMP-300', 'Z': 'Z-stage *Mercury*', 'XY':'XY-stage *Olympus*', 'Pz': 'Piezo *Nanocube*'}
            self.PIdevice= PIdevice.positioner
            self.PIname= PIdevice.name
            self.serial= PIdevice.serial
            
        def connectPIdevice(self):

            try:
                # Connect to PI device through USB
                self.PIdevice.ConnectUSB(self.serial) 

                # Depending on the positioner, the initialization is different

                if  self.PIname==self.deviceNames['Z']: #For Z-stage Connect -> Activate Servo -> Reference     
                    
                    self.PIdevice.gcscommands.SVO(1,1)
                    self.PIdevice.gcscommands.VEL(1, 1)
                    self.PIdevice.gcscommands.FPL()
        
                elif  self.PIname==self.deviceNames['XY']: #For XY-stage Connect -> Activate Servo -> Reference     
                    
                    self.PIdevice.gcscommands.SVO({1:1, 2:1})
                    self.PIdevice.gcscommands.VEL({1:1, 2:1})
                    self.PIdevice.gcscommands.FRF()

                elif self.PIname==self.deviceNames['Pz']: #For Piezo Connect -> Activate Servo   
                    
                    self.PIdevice.gcscommands.SVO({1:1, 2:1, 3:1})
                    self.PIdevice.gcscommands.VEL({1:1, 2:1, 3:1})

                #Wait until all stages are ready
                while not all(list(self.PIdevice.qONT().values())): 
                    time.sleep(0.1)

                if self.PIdevice.gcscommands.IsConnected():
                        print(f"[{self.PIname}] Connected and ready to be used!")
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

        def disconnectPIdevice(self):
            try: 
                self.PIdevice.gcscommands.CloseConnection()
                print(f"[{self.PIname}] Disconnected")

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

class DeviceManager(QWidget):

    startCommand= Signal(object)
    endCommand= Signal(object)

    def __init__(self):
        super().__init__()
      
        self.layoutMain= QHBoxLayout(); self.setLayout(self.layoutMain)
        self.groupDevice= QGroupBox('Devices'); self.layoutMain.addWidget(self.groupDevice)
        self.groupDevice.setStyleSheet(""" QGroupBox {font-size: 14px; font-weight: bold;}  """)
        self.layoutDevice= QHBoxLayout(self.groupDevice)

        self.potentiostat= {'api':None, 'channel':1, 'board_type': None, 'id_': None}
        self.BL= Device(self.layoutDevice, 'Potentiostat', 'BL', '192.168.2.2')
        self.XY= Device(self.layoutDevice, 'XY-Stage', 'XY', '0125076674')
        self.Z= Device(self.layoutDevice, 'Z-Stage', 'Z', '0026550002')
        self.Pz= Device(self.layoutDevice, 'Piezo', 'Pz', '0125021719')
        self.PIdevices= {'XY':self.XY.positioner, 'Z':self.Z.positioner, 'Pz':self.Pz.positioner}

        self.buttonStopAll= QPushButton(); self.layoutDevice.addWidget(self.buttonStopAll)
        self.layoutStop= QVBoxLayout(self.buttonStopAll)
        self.buttonStopAll.setFixedSize(95, 70)
        self.buttonStopAll.setStyleSheet("""QPushButton {background-color: #f0f0f0;
                                                    border: 4px solid #d0d0d0;
                                                    border-top-color: #ffffff;
                                                    border-left-color: #ffffff;
                                                    border-radius: 4px;
                                                    padding: 6px;font-weight: bold;} """)
        
        self.labelStopButtonIcon= QLabel(); self.layoutStop.addWidget(self.labelStopButtonIcon)
        pixmapStop= QPixmap(r"Icons\Stop-red_37107.png")
        scaled_pixmap = pixmapStop.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.labelStopButtonIcon.setPixmap(scaled_pixmap)
        self.labelStopButtonIcon.setAlignment(Qt.AlignmentFlag.AlignCenter)             
        self.layoutStop.addWidget(self.labelStopButtonIcon )   

        self.buttonStopAll.pressed.connect(self.stopAll)

        self.BL.toggle.checkStateChanged.connect(lambda: self.toggleDevice(self.BL))
        self.XY.toggle.checkStateChanged.connect(lambda: self.toggleDevice(self.XY))
        self.Z.toggle.checkStateChanged.connect(lambda: self.toggleDevice(self.Z))
        self.Pz.toggle.checkStateChanged.connect(lambda: self.toggleDevice(self.Pz))
      
    def toggleDevice(self, device:Device):
        if device.toggle.isChecked():
            if device.type== 'BL':
                self.connectPotentiostat(device)

            else:
                self.connectPositioner(device) 
                print(f'2nd time {device.positioner}')

        else: 
            if device.type== 'BL':
                self.disconnectPotentiostat(device)

            else:
                self.disconnectPositioner(device)


    def deviceStatus(self, device:Device):
   
        if device.type== 'BL':
            print(device.potentiostat['api'])
            if not device.potentiostat['api']:
                
                print(f'unchecking toggle because api:{device.potentiostat['api']}')
                device.toggle.setChecked(False)

        else:
            #device= getattr(self, 'PIdevice')
            if not device.positioner.IsConnected():
                print('unchecking toggle')
                device.toggle.setChecked(False)
    
    def stopAll(self):
        print('Emergency stop')

    def connectPositioner(self, device:Device):
        self.PIdevice= threadInit(PIconnect, device)
        
        self.PIdevice.thread.started.connect(self.PIdevice.worker.connectPIdevice)
        self.PIdevice.worker.finished.connect(lambda: self.deviceStatus(device))
        self.PIdevice.worker.finished.connect(lambda: self.endCommand.emit({'end':0}))
        
        self.PIdevice.thread.start()
        self.startCommand.emit({'start': f"Connecting to {device.name}... "})

    def disconnectPositioner(self, device:Device):
        self.PIdevice= threadInit(PIconnect, device)
        
        self.PIdevice.thread.started.connect(self.PIdevice.worker.disconnectPIdevice)
        self.PIdevice.worker.finished.connect(lambda: self.endCommand.emit({'end':0}))
        
        self.PIdevice.thread.start()
        self.startCommand.emit({'start': f"Disconnecting from {device.name}... "})
       
    def connectPotentiostat(self, device:Device):
        self.BLdevice= threadInit(Biologic, device.potentiostat)

        self.BLdevice.thread.started.connect(self.BLdevice.worker.connectBL)
        self.BLdevice.worker.biologic.connect(lambda settings: setattr(self.BL, 'potentiostat', settings))
        self.BLdevice.worker.finished.connect(lambda: self.deviceStatus(device))
        self.BLdevice.worker.finished.connect(lambda: self.endCommand.emit({'end':0}))
        
        self.BLdevice.thread.start()
        self.startCommand.emit({'start': "Connecting to VMP-300... "})

    def disconnectPotentiostat(self, device:Device):
        self.BLdevice= threadInit(Biologic, device.potentiostat)

        self.BLdevice.thread.started.connect(self.BLdevice.worker.disconnectBL)
        self.BLdevice.worker.finished.connect(lambda: self.deviceStatus(device))
        self.BLdevice.worker.finished.connect(lambda: self.endCommand.emit({'end':0}))
        
        self.BLdevice.thread.start()
        self.startCommand.emit({'start': "Connecting to VMP-300... "})
        
    def connectAll(self):
   
        """
        self.connectPotentiostat(self.VMP300.labelStatus)
        self.connectPositioner(self.Pz.labelStatus, self.PzStage, self.piezoSerial, 'Pz')
        self.connectPositioner(self.Z.labelStatus, self.Zstage, self.Zserial, 'Z')
        self.connectPositioner(self.XY.labelStatus, self.XYstage, self.XYserial, 'XY')
        """

    def _threadClose(self, worker, thread:QThread):
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

if __name__ == '__main__':
    app= QApplication([])
    main= DeviceManager()
    main.show()
    app.exec()

