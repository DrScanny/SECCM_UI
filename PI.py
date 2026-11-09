from pipython import GCSDevice, GCSError, datarectools
from PySide6.QtCore import Qt, QObject, QThread, Signal, Slot
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
                    method= getattr(self, "updatePosition")
                    method(position=True)
            
            return wrapper
        return decorator

class PI(QObject): 

        message= Signal(str)
        progress= Signal(int)
        position= Signal(list)
        connection= Signal(bool)
        finished= Signal()              

        def __init__(self, threadInstance:QThread, PIdevice:dict[str,GCSDevice], move:list[float]=[0.0, 0.0, 0.0, 0.0]):
            super().__init__()

            self.XYstage= PIdevice['XY']
            self.Zstage= PIdevice['Z']
            self.Piezo= PIdevice['Pz']
            self.Xmove= -1*move[0]
            self.Ymove= move[1]
            self.Zmove= move[2]
            self.Pzmove= move[3]
            self.currentPosition= [0.0, 0.0, 0.0, 0.0]
            self.threadInstance= threadInstance

        def debug(self):
            print(f'Moving by [{self.Xmove}, {self.Ymove}, {self.Zmove}]')
            print('Moving...')
            i=0
            while i<60:
                i+=1
                print(i)
                time.sleep(1)
                if self.threadInstance.isInterruptionRequested():
                    self.finished.emit()
                    return
            
            self.finished.emit()

        @_exception()
        def moveXYZ(self):
        
            #Moving Stages
            if self.Xmove !=0 or self.Ymove !=0:
                print('[move XYZ Debug] moving XY stage')
                self.XYstage.gcscommands.MVR({'1':self.Xmove, '2':self.Ymove})
            if self.Zmove !=0:
                print('[move XYZ Debug] moving Z stage')
                self.Zstage.gcscommands.MVR('1', self.Zmove)

            #Wait until Stages have stopped moving
            self.wait(interrupt=True)

        @_exception()
        def movePz(self):
            
            #Moving Piezo
            if self.Pzmove !=0:
                print('[move XYZ Debug] moving piezo')
                self.Piezo.gcscommands.MOV('3', self.Pzmove)
         
            #Wait until Stages have stopped moving
            self.wait(interrupt=True)

        @_exception()
        def resetXYZ(self):

            if self.XYstage.IsConnected():
                self.XYstage.gcscommands.FRF()

            if self.Zstage.IsConnected():
                self.Zstage.gcscommands.FPL()

            if self.Piezo.IsConnected():
                self.Piezo.gcscommands.MOV('3', 0)

            self.wait()
            print('[POSITIONERS] Reset!')
       
        @_exception()
        def moveToXYZ(self):

            if self.XYstage.IsConnected():
                self.XYstage.gcscommands.MOV({1:self.Xmove, 2:self.Ymove})

            if self.Zstage.IsConnected():
                self.Zstage.gcscommands.MOV('1', self.Zmove)

            self.wait(interrupt=True)

        def updatePosition(self, position:bool =False):

            if self.XYstage.IsConnected():
                self.currentPosition[0]= -1*round(self.XYstage.qPOS()['1'],3)
            if self.XYstage.IsConnected():
                self.currentPosition[1]= round(self.XYstage.qPOS()['2'],3)      
            if self.Zstage.IsConnected():
                self.currentPosition[2]= round(self.Zstage.qPOS()['1']-25,3)
            if self.Piezo.IsConnected():
                self.currentPosition[3]= round(self.Piezo.qPOS()['3'],3)
            
            self.position.emit(self.currentPosition)  
            
            if position:
                print(f'[POSITIONERS] Moved to {self.currentPosition}')

            self.finished.emit()

        def wait(self, interrupt:bool= False):
            # IsMoving returns an ordered dict: True if moving for each axis of the positioner. 
            # The dict values are turned into a list and then if any values are true the while loop continues until all axis have stopped

            if interrupt:

                if self.XYstage.IsConnected():
                    while any(list(self.XYstage.gcscommands.IsMoving().values())):
                        if self.threadInstance.isInterruptionRequested():
                            self.XYstage.gcscommands.HLT(noraise=True)
                            print('[DEBUG] *moveXYZ* Interrupted by User')
                            return
                        
                if self.Zstage.IsConnected():
                    while any(list(self.Zstage.gcscommands.IsMoving().values())):
                        if self.threadInstance.isInterruptionRequested():
                            self.Zstage.gcscommands.HLT(noraise=True)
                            print('[DEBUG] *moveXYZ* Interrupted by User')
                            return

                if self.Piezo.IsConnected():
                    while any(list(self.Piezo.gcscommands.IsMoving().values())):
                        if self.threadInstance.isInterruptionRequested():
                            self.Piezo.gcscommands.HLT(noraise=True)
                            print('[DEBUG] *movePz* Interrupted by User')
                            return
            else:
            
                if self.XYstage.IsConnected():
                    while any(list(self.XYstage.gcscommands.IsMoving().values())):
                        time.sleep(0.5)

                if self.Zstage.IsConnected():
                    while any(list(self.Zstage.gcscommands.IsMoving().values())):
                        time.sleep(0.5)

                if self.Piezo.IsConnected():
                    while any(list(self.Piezo.gcscommands.IsMoving().values())):
                        time.sleep(0.5)

if __name__ == "__main__":

    print('This file only has helper functions for advanced positioners algorithm')



