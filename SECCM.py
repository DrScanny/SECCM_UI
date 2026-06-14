import os
import sys
import numpy as np
import time
import multiprocessing
import functools
import threading
from pathlib import Path


from PySide6.QtCore import Qt, QEvent, QObject, Signal, Slot, QThread, QThreadPool, QRunnable, Slot

from pipython import GCSDevice, GCSError

from BiologicAPI.kbio.kbio_api import KBIO_api
from BiologicAPI.kbio.kbio_tech import get_experiment_data
from BiologicAPI.kbio.kbio_tech import get_info_data
from kbio.utils import exception_brief

from BiologicAPI.CA_biologic import ca_parm
from BiologicAPI.OCP_biologic import ocp_parm

import UI_Settings

#region: exception
def exception():
        def decorator(func):
            @functools.wraps(func)
            def wrapper(self, *args, **kwargs):
                try:
                    # Attempt to execute the decorated function
                    result = func(self, *args, **kwargs)
                    return result
                
                except GCSError as err:
                    print(f'[ERROR] {func.__name__}: {err}.')
                
                except IOError:
                    print('[ERROR] Connection to Positioner: Checked if controller is turned ON.')

                except Exception as err:
                    # Handle the exception gracefully
                    print(f"[ERROR] {func.__name__}: {err}")
                    # Optional: Return a default fallback value or re-raise with 'raise'
                    return None 
                
                finally:
                    # This block always runs, even if an exception or return occurred
                    method= getattr(self, "clean")
                    method()
            
            return wrapper
        return decorator

#region: SECCM_PI
class SECCM_PI(QObject): 

    message= Signal(str)
    progress= Signal(int)
    position= Signal(list)
    connection= Signal(bool)
    finished= Signal()              

    def __init__(self, PIdevice:dict[str,GCSDevice], SECCMsettings:UI_Settings.SECCM, event:dict[str,threading.Event]):
        super().__init__()

        self.XYstage:GCSDevice= PIdevice['XY']
        self.Zstage:GCSDevice= PIdevice['Z']
        self.Piezo:GCSDevice= PIdevice['Pz']
        
        self.settings:UI_Settings.SECCM= SECCMsettings
        self.event_piezoReady:threading.Event= event['ready']
        self.event_piezoLimit:threading.Event= event['limit']
        self.event_stopTip:threading.Event= event['stop']

    #region: Approach

    def approachPI(self):

        try:
            # Counting the number of full piezo approach cycle
            counter=1
            self.event_piezoLimit.clear()

            #Initializing positioners speed and position for tip down procedure
            self.Zstage.gcscommands.VEL(1, 0.01)
            self.Piezo.VEL('3', 5) 
            self.Piezo.MOV('3', 60) 
            self.wait(self.Piezo)

            #Primary loop, the positioners will continually move, until the stopTip event is set
            #   1- Piezo move for tip down 
            #   2- Reset the Piezo and move the Z-Stage
            while True:
                
                #Starting piezo movement from 60 to 0 um for approach, 3 seconds wait to let potentiostat start beforehand
                time.sleep(3)
                print(f"[APPROACH] Piezo descent #{counter}")
                self.Piezo.VEL('3', self.settings.speed)
                self.Piezo.MOV('3', 0) 

                #While the Piezo is moving, stop if **Stop Criteria** is met
                while any(list(self.Piezo.gcscommands.IsMoving().values())):
                    if self.event_stopTip.is_set():
                        break
                
                if self.event_stopTip.is_set():
                        break 

                #If the Piezo reaches its limit without being stopped, reset the piezo and move the Z-Stage by the corresponding amount
                #*** Set event_piezoLimit to signal potentiostat to stop during piezo reset***
                self.event_piezoLimit.set()
                counter+=1
                print("[APPROACH] Piezo limit reached")
            
                self.Zstage.MOV(-0.06) 
                self.Piezo.VEL('3', 5) 
                self.Piezo.MOV('3', 60) 

                # Waiting for positioner reset to be done
                self.wait(self.Zstage)
                #*** Emit signal to signal piezo have been reset to potentiostat***
                self.event_piezoReady.set()
                print("[APPROACH] Positioners have been reset")

        except GCSError as err:
            print(f'[ERROR] **SECCM|SECCM_PI|approachPI**: {err}.')
                
        except IOError:
            print('[ERROR] **SECCM|SECCM_PI|approachPI**: Checked if controller is turned ON.')

        except Exception as err:
            # Handle the exception gracefully
            print(f"[ERROR] **SECCM|SECCM_PI|approachPI**: {err}")
            # Optional: Return a default fallback value or re-raise with 'raise'
            return None 
        
        finally:
            # This block always runs, even if an exception or return occurred
            self.clean()
            self.Zstage.gcscommands.VEL(1,1)

    #region: Utility 
    @exception()
    def wait(self, PIdevice:GCSDevice):
        # IsMoving returns an ordered dict: True if moving for each axis of the positioner. 
        # The dict values are turned into a list and then if any values are true the while loop continues until all axis have stopped
        
        while any(list(PIdevice.gcscommands.IsMoving().values())):
            time.sleep(0.5)
        
    def clean(self):
        self.finished.emit()


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#region: SECCM BL
class SECCM_BL(QObject): 

    finished= Signal() # Signal that process is over
    echemData= Signal(object) # Echem data sent as a dict {'t':time, 'Ewe':potential, 'Iwe':current, 'cycle':cycle} *exception for OCP only has time and potential

    def __init__(self, potentiostat, SECCMsettings: UI_Settings.SECCM, event:dict[str,threading.Event]):
        super().__init__()

        self.channel:int= potentiostat['channel']
        self.id_= potentiostat['id_']
        self.api:KBIO_api= potentiostat['api']
        self.board_type= potentiostat['board_type']
        self.verbosity:int = 1
        self.runBiologic:bool= True

        self.settings:UI_Settings.SECCM= SECCMsettings
        self.event_piezoReady:threading.Event= event['ready']
        self.event_piezoLimit:threading.Event= event['limit']
        self.event_stopTip:threading.Event= event['stop']

    #region: ApproachBL
    def approachBL(self):

        try:

            while True: #Primary While loop -> Repeat tip down measurement until trigger or max range hit

                # Measurements are reset each time the piezo hits the limit
                self.event_piezoReady.wait()
                print("[APPROACH] VMP-300 running")
                self.loadTechnique() 
                self.api.StartChannel(self.id_, self.channel)
                self.event_piezoReady.clear() 

                """
                    Secondary loop -> Start acquisition and stops while positioners are resetting.
                        1- Each time the piezo reaches the limit (60 um).
                        2- Once the tip stop has been triggered, the whole approach is stopped. 
                """
                while True: 

                    data= self.api.GetData(self.id_, self.channel)
                    status, tech_name= get_info_data(self.api, data) 
                
                    for output in get_experiment_data(self.api, data, tech_name, self.board_type):
                        self.echemData.emit(output)
                    
                        if self.tipStop(output): # Function that determine if the tip should be stopped based on the stop criteria
                            self.event_stopTip.set() # Set the 'stop' event flag. Signal the end of approach curve: Stop all activity!
                            status= "STOP"
                            break

                    # Stop the measurement once the piezo limit is reached
                    if self.event_piezoLimit.is_set():
                        print("[APPROACH] VMP-300 interrupted, waiting until piezo are reinitialized")
                        break
                    
                    if status== "STOP":
                        break

        except Exception as err:
            # Handle the exception gracefully
            print(f"[ERROR] **SECCM|SECCM_BL|approachBL**: {exception_brief(err, self.verbosity >= 1)}")
            # Optional: Return a default fallback value or re-raise with 'raise'
            return None 
        
        finally:
            # This block always runs, even if an exception or return occurred
            self.clean()

    @exception()
    def loadTechnique(self):
            
            #Implementing the stop technique (OCP, CA, AC) based on user selection stored in self.settings.stop
            tech= UI_Settings.OCP('OCP', 600, 2e-4, 1, 0)
            
            match self.settings.stop:
                case 0: #Open Circuit Potential
                    tech_file, ecc_parms= ocp_parm(self.board_type, self.api, tech)

                case 1: #Potentiostatic
                    tech= UI_Settings.CA('CA', potential= self.settings.Eapp, dt= 2e-4, duration= 600)
                    tech_file, ecc_parms= ca_parm(self.board_type, self.api, tech)

                case 2: # AC not implemented yet
                    ecc_parms, tech_file= (False, False)
    
                case _:
                    print("> Invalid technique or settings")
                    ecc_parms, tech_file= (False, False)
    
            if tech_file and ecc_parms:
                self.api.LoadTechnique(self.id_, self.channel, tech_file, ecc_parms, first=True, last=True, display=(self.verbosity > 1))

    @exception()
    def tipStop(self, potentiostatOutput:dict[str,float]):
            
            match self.settings.stop:
                case 0: #tip stop based on DC change from fixed potential
                    if abs(potentiostatOutput['Ewe'])<=1.5:
                        print('Tip stop OCP')
                        return True
                    else:
                        return False
                        
                case 1: #tip stop based on OCP change
                    if abs(potentiostatOutput['Iwe'])>self.settings.Istop:
                        print('Tip stop Potentiostatic')
                        return True
                    else:
                        return False
                
                case 2: #tip stop based on AC change 
                    print('Not implemented yet')
                    return False
                
                case _:
                    return False
                
    def clean(self):
        self.finished.emit()

class threadInit():
    def __init__(self, workerClass, *arg):
        self.thread= QThread()
        self.worker= workerClass(*arg)
        self.worker.moveToThread(self.thread)

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

def SECCM_approach(PIdevice:dict[str,GCSDevice], potentiostat, SECCMsettings:UI_Settings.SECCM):
        
        event= {}
        event['ready']= threading.Event()
        event['limit']= threading.Event()
        event['stop']= threading.Event()

        #Thread assigned to the positioners control during approach
        positioner= threadInit(SECCM_PI, PIdevice, SECCMsettings, event)
        positioner.thread.started.connect(positioner.worker.approachPI)

        #Thread assigned to the potentiostat control during approach
        biologic= threadInit(SECCM_BL, potentiostat, SECCMsettings, event)
        biologic.thread.started.connect(positioner.worker.approachBL)

        positioner.thread.start()
        biologic.thread.start()

        positioner.worker.finished.connect(lambda: print('[APPROACH] Succesful Landing!'))

if __name__ == '__main__':
    print('Package for SECCM approach, Does nothing')
