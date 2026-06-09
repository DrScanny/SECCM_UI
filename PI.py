from pipython import GCSDevice, GCSError, gcserror
from PySide6.QtCore import Qt, QObject, QThread, Signal, Slot
from PySide6.QtWidgets import QProgressDialog, QMessageBox
import time
import functools

"""
Class to control the PI controllers and stage
"""

def _exception():
        def decorator(func):
            @functools.wraps(func)
            def wrapper(self, *args, **kwargs):
                try:
                    # Attempt to execute the decorated function
                    result = func(self, *args, **kwargs)
                    return result
                
                except GCSError as err:
                    print(f'[ERROR] Positioner with {func.__name__}: {err}.')
                
                except IOError:
                    print('[ERROR] Connection to Positioner: Checked if controller is turned ON.')

                except Exception as err:
                    # Handle the exception gracefully
                    print(f"[ERROR] Positioner with {func.__name__}: {err}")
                    # Optional: Return a default fallback value or re-raise with 'raise'
                    return None 
                
                finally:
                    # This block always runs, even if an exception or return occurred
                    method= getattr(self, "_clean")
                    method()
            
            return wrapper
        return decorator

class PI(QObject): 

        message= Signal(str)
        progress= Signal(int)
        position= Signal(list)
        connection= Signal(bool)
        finished= Signal()              

        def __init__(self, PIdevice:dict[str,GCSDevice], move:list[float]=[0.0, 0.0, 0.0]):
            super().__init__()

            self.XYstage= PIdevice['XY']
            self.Zstage= PIdevice['Z']
            self.Piezo= PIdevice['Pz']
            self.Xmove= -1*move[0]
            self.Ymove= move[1]
            self.Zmove= move[2]
            self.currentPosition= [0.0, 0.0, 0.0]

        @_exception()
        def moveXYZ(self):

            #Calculating the predicted position for each positioner after moving 
            Xf= round(abs(self.Xmove + self.XYstage.gcscommands.qPOS()['1']),3)
            Yf= round(abs(self.Ymove + self.XYstage.qPOS()['2']),3)
            Zf= round(self.Zmove + self.Zstage.qPOS()['1'], 3)
        
            #Moving Stages
            self.XYstage.MVR({'1':self.Xmove, '2':self.Ymove})
            self.Zstage.MVR('1', self.Zmove)

            #Wait until Stages have stopped moving
            self._wait(self.XYstage)
            self._wait(self.Zstage)

            self._updatePosition(position= True)

        @_exception()
        def resetXYZ(self):

            if self.XYstage.IsConnected():
                self.XYstage.FRF()

            if self.Zstage.IsConnected():
                self.Zstage.gcscommands.FNL()

            self._wait(self.XYstage)
            self._wait(self.Zstage)

            print('[POSITIONERS] Reset!')
            self._updatePosition()

        @_exception()
        def stopXYZ(self):
            if self.XYstage.IsConnected():
                self.XYstage.gcscommands.HLT(noraise=True)

            if self.Zstage.IsConnected():
                self.Zstage.gcscommands.HLT(noraise=True)

            print('[POSITIONERS] Motion Stopped by User!')
            self._updatePosition()
       
        @_exception()
        def moveToXYZ(self):

            if self.XYstage.IsConnected():
                self.XYstage.gcscommands.MOV({1:self.Xmove, 2:self.Ymove})

            if self.Zstage.IsConnected():
                self.Zstage.gcscommands.MOV('1', self.Zmove)

            self._wait(self.XYstage)
            self._wait(self.Zstage)
         
            self._updatePosition(position= True)

        def _updatePosition(self, position:bool =False):
            self.currentPosition= [round(-1*self.XYstage.qPOS()['1'],3), round(self.XYstage.qPOS()['2'],3), round(self.Zstage.qPOS()['1'],3)-25]
            self.position.emit(self.currentPosition)  
            
            if position:
                print(f'[POSITIONERS] Moved to {self.currentPosition}')

            self.finished.emit()

        def _wait(self, PIdevice:GCSDevice):
            # IsMoving returns an ordered dict: True if moving for each axis of the positioner. 
            # The dict values are turned into a list and then if any values are true the while loop continues until all axis have stopped
            
            while any(list(PIdevice.gcscommands.IsMoving().values())):
                time.sleep(0.5)
            
        def _clean(self):
            self.finished.emit()

if __name__ == "__main__":

    print('This file only has helper functions for advanced positioners algorithm')



