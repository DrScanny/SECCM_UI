from PySide6.QtCore import Qt, QEvent, QObject, Signal, Slot, QThread, QThreadPool, QRunnable, Slot, QSize
from PySide6.QtGui import QFont, QIcon, QPixmap
from PySide6.QtWidgets import (QApplication, QFileDialog, QMainWindow, QButtonGroup, QPushButton, 
                               QMessageBox, QTextEdit,  QHBoxLayout, QVBoxLayout, QDockWidget,
                               QMainWindow, QStatusBar, QWidget, QFrame, QListWidget,
                               QSplitter, QPlainTextEdit, QLabel, QTreeWidgetItem, QAbstractItemView,
                               QTreeWidget, QLineEdit, QGridLayout, QGroupBox, QStyle)

#External packages
import time
import os
import sys
from pipython import GCSDevice, GCSError

import kbio.kbio_types as KBIO
from kbio.c_utils import c_is_64b
from kbio.kbio_api import KBIO_api

from BiologicAPI.kbio.kbio_tech import get_experiment_data
from BiologicAPI.kbio.kbio_tech import get_info_data
from kbio.utils import exception_brief

#Personal packages
from PI import PI
from kbio.utils import exception_brief
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
        self.potentiostat= {'api':None, 'channel':1, 'board_type': None, 'id_': None, 'verbosity': 1}
                       
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

class BLconnect(QObject):
    finished= Signal() # Signal that process is over
    echemData= Signal(object) # Echem data sent as a dict {'t':time, 'Ewe':potential, 'Iwe':current, 'cycle':cycle} *exception for OCP only has time and potential
    biologic= Signal(object) # Potentiostat api information to connect to instrument
    connectionStatus= Signal(bool)
    technique= Signal(str)

    def __init__(self, instrument:Device):
        super().__init__()

        self.channel= instrument.potentiostat['channel']
        self.id_= instrument.potentiostat['id_']
        self.api= instrument.potentiostat['api']
        self.board_type= instrument.potentiostat['board_type']
        self.verbosity= 1

    def connectBL(self, ip_address= "192.168.2.2", channel_nb= 1):

        try:

            address= ip_address
            self.channel= channel_nb

            binary_path= os.getcwd()
            force_load_firmware = True

            # determine library file according to Python version (32b/64b)
            if c_is_64b:
                DLL_file = "EClib64.dll"
            else:
                DLL_file = "EClib.dll"

            DLL_path = f"{binary_path}{os.sep}BiologicAPI{os.sep}lib{os.sep}{DLL_file}"

            # ==============================================================================#

            # API initialize
            self.api = KBIO_api(DLL_path)

            # BL_GetLibVersion
            version = self.api.GetLibVersion()
            print()
            # BL_Connect

            self.id_, device_info = self.api.Connect(address)
            print(device_info)
            print()

            # based on board_type, determine firmware filenames
            self.board_type = self.api.GetChannelBoardType(self.id_, self.channel)
            match self.board_type:
                case KBIO.BOARD_TYPE.ESSENTIAL.value:
                    firmware_path = "kernel.bin"
                    fpga_path = "Vmp_ii_0437_a6.xlx"
                case KBIO.BOARD_TYPE.PREMIUM.value:
                    firmware_path = "kernel4.bin"
                    fpga_path = "vmp_iv_0395_aa.xlx"
                case KBIO.BOARD_TYPE.DIGICORE.value:
                    firmware_path = "kernel.bin"
                    fpga_path = ""
                case _:
                    print("> Board type detection failed")
                    sys.exit(-1)

            # Load firmware
            print(f"> Loading {firmware_path} ...")
            # create a map from channel set
            channel_map = self.api.channel_map({self.channel})
            # BL_LoadFirmware
            self.api.LoadFirmware(self.id_, channel_map, firmware=firmware_path, fpga=fpga_path, force=force_load_firmware)
            print("> ... firmware loaded")
            print()

            # BL_GetChannelInfos
            channel_info = self.api.GetChannelInfo(self.id_, self.channel)
            print(f"> Channel {self.channel} info :")
            print(channel_info)
            print()

            if not channel_info.is_kernel_loaded:
                print("> kernel must be loaded in order to run the experiment")
                sys.exit(-1)

            self.biologic.emit({'api':self.api, 'channel':1, 'board_type': self.board_type, 'id_': self.id_})
            self.connectionStatus.emit(True)
            
            print('[EVENT] Connected to VMP-300!')

        except Exception as err:
                # Handle the exception gracefully
                print(f"[ERROR] Connecting to VMP-300: {exception_brief(err, self.verbosity >= 1)}")
                # Optional: Return a default fallback value or re-raise with 'raise'
                return False
        
        finally:
            self.finished.emit()
          
          
    def disconnectBL(self):
        self.api.Disconnect(self.id_)
        print('[VMP-300] Disconnected')
  

class DeviceManager(QWidget):

    startCommand= Signal(object)
    endCommand= Signal(object)

    def __init__(self):
        super().__init__()
      
        self.layoutMain= QHBoxLayout(); self.setLayout(self.layoutMain)
        self.groupDevice= QGroupBox('Devices'); self.layoutMain.addWidget(self.groupDevice)
        self.groupDevice.setStyleSheet(""" QGroupBox {font-size: 14px; font-weight: bold;}  """)
        self.layoutDevice= QHBoxLayout(self.groupDevice)

        self.potentiostat= {'api':None, 'channel':1, 'board_type': None, 'id_': None, 'verbosity': 1}
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

        self.BL.toggle.checkStateChanged.connect(lambda: self.connectDevice(self.BL))
        self.XY.toggle.checkStateChanged.connect(lambda: self.connectDevice(self.XY))
        self.Z.toggle.checkStateChanged.connect(lambda: self.connectDevice(self.Z))
        self.Pz.toggle.checkStateChanged.connect(lambda: self.connectDevice(self.Pz))
      
    def connectDevice(self, device:Device):
        if device.toggle.isChecked():

            match device.type:
                case'BL':
                    self.connectPotentiostat()

                case 'XY':
                    self.connectXY() 

                case 'Z':
                    self.connectZ() 

                case 'Pz':
                    self.connectPz() 

        else: 
            if device.type== 'BL':
                self.disconnectPotentiostat(device)

            else:
                self.disconnectPositioner(device)


    def deviceStatus(self, device:Device):

        try:
            if device.type== 'BL':
                if not device.potentiostat['api']:
                    
                    print(f'unchecking toggle because api:{device.potentiostat['api']}')
                    device.toggle.setChecked(False)

            else:
                if not device.positioner.IsConnected():
                    print('unchecking toggle')
                    device.toggle.setChecked(False)

        except GCSError as err:
            print(f"[ERROR] Connection to {device.name}: {GCSError(err)}")

        except Exception as err:
            print(f"[ERROR] : {exception_brief(err, extended= True)}")

    def connectXY(self):
        self.XYconnect= threadInit(PIconnect, self.XY)
        
        self.XYconnect.thread.started.connect(self.XYconnect.worker.connectPIdevice)
        self.XYconnect.worker.finished.connect(lambda: self.deviceStatus(self.XY))
        self.XYconnect.worker.finished.connect(lambda: self.endCommand.emit({'end':0}))
        
        self.XYconnect.thread.start()
        self.startCommand.emit({'start': f"Connecting to {self.XY.name}... "})

    def connectZ(self):
        self.Zconnect= threadInit(PIconnect, self.Z)
        
        self.Zconnect.thread.started.connect(self.Zconnect.worker.connectPIdevice)
        self.Zconnect.worker.finished.connect(lambda: self.deviceStatus(self.Z))
        self.Zconnect.worker.finished.connect(lambda: self.endCommand.emit({'end':0}))
        
        self.Zconnect.thread.start()
        self.startCommand.emit({'start': f"Connecting to {self.Z.name}... "})

    def connectPz(self):
        self.PzConnect= threadInit(PIconnect, self.Pz)
        
        self.PzConnect.thread.started.connect(self.PzConnect.worker.connectPIdevice)
        self.PzConnect.worker.finished.connect(lambda: self.deviceStatus(self.Pz))
        self.PzConnect.worker.finished.connect(lambda: self.endCommand.emit({'end':0}))
        
        self.PzConnect.thread.start()
        self.startCommand.emit({'start': f"Connecting to {self.Pz.name}... "})

    def disconnectPositioner(self, device:Device):
        self.PIdevice= threadInit(PIconnect, device)
        
        self.PIdevice.thread.started.connect(self.PIdevice.worker.disconnectPIdevice)
        self.PIdevice.worker.finished.connect(lambda: self.endCommand.emit({'end':0}))
        
        self.PIdevice.thread.start()
        self.startCommand.emit({'start': f"Disconnecting from {device.name}... "})
       
    def connectPotentiostat(self):
        self.BLdevice= threadInit(BLconnect, self.BL)

        self.BLdevice.thread.started.connect(self.BLdevice.worker.connectBL)
        self.BLdevice.worker.biologic.connect(lambda settings: setattr(self.BL, 'potentiostat', settings))
        self.BLdevice.worker.finished.connect(lambda: self.deviceStatus(self.BL))
        self.BLdevice.worker.finished.connect(lambda: self.endCommand.emit({'end':0}))
        
        self.BLdevice.thread.start()
        self.startCommand.emit({'start': "Connecting to VMP-300... "})

    def disconnectPotentiostat(self, device:Device):
        self.BLdevice= threadInit(BLconnect, device)

        self.BLdevice.thread.started.connect(self.BLdevice.worker.disconnectBL)
        self.BLdevice.worker.finished.connect(lambda: self.deviceStatus(device))
        
        self.BLdevice.thread.start()
        
    def connectAll(self):

        self.connectPotentiostat()
        time.sleep(3)
        self.connectXY() 
        time.sleep(3)
        self.connectZ() 
        time.sleep(3)
        self.connectPz() 


if __name__ == '__main__':
    app= QApplication([])
    main= DeviceManager()
    main.show()
    app.exec()

