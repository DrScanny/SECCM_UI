from pipython import GCSDevice, datarectools, pitools
from PySide6.QtCore import Qt, QObject, QThread, Signal, Slot
from PySide6.QtWidgets import QProgressDialog, QMessageBox
import time

"""
Class to control the PI controllers and stage
"""

class PI(QObject): 

        warning= Signal(str)
        progress= Signal(int)
        position= Signal(list)
        connection= Signal(bool)
        finished= Signal()              

        def __init__(self):
            super().__init__()

        def connectPI(self, PIdevice:GCSDevice, type:str, serial:str):
            print('connecting to positionner...')

            PIdevice.ConnectUSB(serial) # Connect through USB

            match type:

                case 'Z': #For Z-stage Connect -> Activate Servo -> Reference     
                    PIdevice.SVO(1,1)
                    PIdevice.FPL()

                    while not all(list(PIdevice.qONT(1).values())): 
                        time.sleep(0.1)

                    if PIdevice.gcscommands.qFRF(): #If reference is succesful 
                        print("Z-stage -Mercury- connected")
                    else:
                        print('Connection to Z-stage -Mercury- Failed')
        
                case 'XY': #For XY-stage Connect -> Activate Servo -> Reference
                    PIdevice.SVO({1:1, 2:1})
                    PIdevice.FRF()

                    while not all(list(PIdevice.qONT([1,2]).values())):
                        time.sleep(0.1)

                    if all(list(PIdevice.gcscommands.qFRF().values())):#If reference is succesful 
                        print("XY-stage -Olympus- connected and ready to be used")  
                    else:
                        print('Connection to XY-stage -Olympus- Failed')

                case 'Pz': #For Piezo -> Connect (Does not require any referencing)
                    PIdevice.SVO({1:1, 2:1, 3:1})
                    
                    if PIdevice.gcscommands.IsConnected(): # IF connected
                        print("Piezo -Nanocube- connected")     
                    else:
                        print('Connection to Piezo -Nanocube- Failed')

            self.connection.emit(True)

        def movePI(self, XYstage:GCSDevice, Zstage:GCSDevice, move:list[float]):

            #Calculating the predicted position for each positioner after moving 
            Xf= abs(move[0] + XYstage.qPOS()['1'])
            Yf= abs(move[1] + XYstage.qPOS()['2'])
        
            #Before moving check travel range is appropriate
            if Xf<=65 and Yf<=65:
                XYstage.VEL({'1':2, '2':2})
                XYstage.MVR({'1':move[0], '2':move[1]})
            else:
                self.warning.emit('Move commands exceeds XY Stage limits') 

            Zf= move[2] + Zstage.qPOS()['1']
            print(f'Zf={Zstage.qPOS()['1']}')
    
            if Zf>=0 and Zf<=25:
                Zstage.VEL('1',1)
                Zstage.MVR('1', move[2])

            else:
                self.warning.emit('Move commands exceeds Z Stage limits') 

            while not all(list(XYstage.qONT().values())):
                time.sleep(1)
            
            while not Zstage.qONT()['1']:
                time.sleep(1)

            self.position.emit([XYstage.qPOS()['1'], XYstage.qPOS()['2'], Zstage.qPOS()['1']])  
            self.finished.emit() 

        def resetPI(self, XYstage:GCSDevice, Zstage:GCSDevice):

            if XYstage.IsConnected():
                XYstage.FRF()

            while not all(list(XYstage.qONT(1).values())):
                time.sleep(1)

            self.finished.emit()
            
            if Zstage.IsConnected():
                Zstage.gcscommands.FNL()

            while not all(list(Zstage.qONT(1).values())):
                time.sleep(1)

            print('Positioners have been reset!')
            self.finished.emit()

        def stopPI(self, XYstage:GCSDevice, Zstage:GCSDevice):
            if XYstage.IsConnected():
                XYstage.gcscommands.HLT(noraise=True)

            if Zstage.IsConnected():
                Zstage.gcscommands.HLT(noraise=True)

            print('Positioners motion Stopped by User!')
            self.finished.emit()

        def moveToPI(self, XYstage:GCSDevice, Zstage:GCSDevice, move:list[float]):

            if XYstage.IsConnected():
                XYstage.gcscommands.MOV({1:move[0], 2:move[1]})

            if Zstage.IsConnected():
                Zstage.gcscommands.MOV('1', move[2])
            
            self.finished.emit()

if __name__ == "__main__":

    print('This File does nothing and only has helper functions for advanced positioners algorithm')



