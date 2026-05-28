from pipython import GCSDevice, datarectools, pitools
from PySide6.QtCore import Qt, QObject, QThread, Signal, Slot
from PySide6.QtWidgets import QProgressDialog, QMessageBox
import UI_Settings
import time

"""
Class to control the PI controllers and stage
"""

class PI(QObject):               

        def __init__(self):

            self.Pz= GCSDevice()
            self.Zstage= GCSDevice()
            self.XYstage= GCSDevice()

            self.Xmove= 0.0
            self.Ymove= 0.0
            self.Zmove= 0.0

        def connectPositioner(self, serialnum:str, type:str):

            match type:

                case 'Z': #For Z-stage Connect -> Activate Servo -> Reference
                    self.Zstage.ConnectUSB(serialnum=serialnum) # Connect through USB
                    self.Zstage.SVO(1,1)
                    self.Zstage.FPL()

                    while not all(list(self.Zstage.qONT(1).values())): 
                        time.sleep(0.1)

                    if self.Zstage.gcscommands.qFRF()[1]: #If reference is succesful 
                        print("Z-stage -Mercury- connected")
                        return True
                    else:
                        print('Connection to Z-stage -Mercury- Failed')
                        return False
        
                case 'XY': #For XY-stage Connect -> Activate Servo -> Reference
                    self.XYstage.ConnectUSB(serialnum=serialnum) # Connect through USB
                    self.XYstage.SVO({1:1, 2:1})
                    self.XYstage.FRF()

                    while not all(list(self.XYstage.qONT([1,2]).values())):
                        time.sleep(0.1)

                    if all(list(self.XYstage.gcscommands.qFRF().values())):#If reference is succesful 
                        print("XY-stage -Olympus- connected and ready to be used")
                        return True
                    else:
                        print('Connection to XY-stage -Olympus- Failed')
                        return False

                case 'Pz': #For Piezo -> Connect (Does not require any referencing)
                    self.Pz.ConnectUSB(serialnum=serialnum) # Connect through USB
                    self.Pz.SVO({1:1, 2:1, 3:1})
                    
                    if self.Pz.gcscommands.IsConnected(): # IF connected
                        print("Piezo -Nanocube- connected")
                        return True
                    else:
                        print('Connection to Piezo -Nanocube- Failed')
                        return False

        def move(self)->list[float]|str:

            #Calculating the predicted position for each positioner after moving 
            X0= self.XYstage.qPOS()['1']
            Y0= self.XYstage.qPOS()['2']
            Z0= self.Zstage.qPOS()['1']

            Xtravel= abs(self.Xmove + self.XYstage.qPOS()['1'])
            Ytravel= abs(self.Ymove + self.XYstage.qPOS()['2'])
            Ztravel= self.Zmove + self.Zstage.qPOS()['1']
          
            if Xtravel<=65 and Ytravel<=65:
                self.XYstage.VEL({'1':2, '2':2})
                self.XYstage.MVR({'1':self.Xmove, '2':self.Ymove})
            else:
                return 'Move commands exceeds XY Stage limits'

            if Ztravel>=0 and Ztravel<=25:
                self.Zstage.VEL('1',1)
                self.Zstage.MVR('1',self.Zmove)

            else:
                return 'Move commands exceeds Z Stage limits'

            while not all(list(self.XYstage.qONT().values())):
                time.sleep(0.5)
                
            while not self.Zstage.qONT()['1']:
                time.sleep(0.5)

            print(f'Succesful move to ({self.XYstage.qPOS()['1']}, {self.XYstage.qPOS()['2']}, {self.Zstage.qPOS()['1']-Z0})')

            return [self.XYstage.qPOS()['1'], self.XYstage.qPOS()['2'], self.Zstage.qPOS()['1']-Z0]  

        def reset(self):
           
            if self.XYstage.IsConnected():
                self.XYstage.FRF()

            if self.Zstage.IsConnected():
                self.Zstage.FPL()

            while not all(list(self.XYstage.qONT(1).values())):
                time.sleep(0.5)

            while not self.Zstage.qONT()['1']:
                time.sleep(0.5)

            if self.Zstage.gcscommands.qFRF()[1] and all(list(self.XYstage.gcscommands.qFRF().values())):
                print('Succesful reset!')
                return True
            else:
                print('Error in reset!')
                return False

        def stop(self):
            if self.XYstage.IsConnected():
                self.XYstage.gcscommands.HLT(noraise=True)

            if self.Zstage.IsConnected():
                self.Zstage.gcscommands.HLT(noraise=True)

            print('Positioners motion Stopped!')

        def moveTo(self, coordinates):
            if self.XYstage.IsConnected():
                self.XYstage.gcscommands.MOV({1:coordinates[0], 2:coordinates[1]})

            if self.Zstage.IsConnected():
                self.Zstage.gcscommands.MOV({1:coordinates[3]})

if __name__ == "__main__":

    print('This File does nothing and only has helper functions for advanced positioners algorithm')



