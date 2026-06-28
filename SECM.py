import os
import sys
import numpy as np
import time
import functools
import threading
from pathlib import Path
import random


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
"""
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
"""

#region: SECM_PI
class SECM_PI(QObject): 

    position= Signal(list)
    connection= Signal(bool)
    finished= Signal()              

    def __init__(self, threadInstance:QThread, PIdevice:dict[str,GCSDevice], SECMsettings:UI_Settings.SECM, event:dict[str,threading.Event]):
        super().__init__()

        self.XYstage:GCSDevice= PIdevice['XY']
        self.Zstage:GCSDevice= PIdevice['Z']
        self.Piezo:GCSDevice= PIdevice['Pz']
        
        self.settings:UI_Settings.SECM= SECMsettings
        self.event_piezoReady:threading.Event= event['ready']
        self.event_piezoLimit:threading.Event= event['limit']
        self.event_stopTip:threading.Event= event['stop']
        self.threadInstance= threadInstance
        
    #region: Approach

    def debug(self):
        print('Positioner...')
        i=0
        while i<10:
            i+=1
            print(i)
            time.sleep(1)
            if self.threadInstance.isInterruptionRequested():
                self.finished.emit()
                return print('Interrupted by user')
        self.finished.emit()

    def map(self):
        pass

    def approach(self):

        try:
            # Counting the number of full piezo approach cycle
            counter=1

            #Initializing positioners speed and position for tip down procedure
            self.Zstage.gcscommands.VEL(1, 0.01)
            self.Piezo.VEL('3', 5) 
            self.Piezo.MOV('3', 60) 

            while any(list(self.Piezo.gcscommands.IsMoving().values())):
                time.sleep(1)

            #Primary loop, the positioners will continually move, until the stopTip event is set
            #   1- Piezo move for tip down 
            #   2- Reset the Piezo and move the Z-Stage

            print('[DEBUG] piezo ready')
            self.event_piezoReady.set()
            time.sleep(3)

            while True:
                #Starting piezo movement from 60 to 0 um for approach, 2 seconds wait to let potentiostat start beforehand
                time.sleep(2)
                print(f"[SECCM] Piezo Approaching #{counter}")
                self.Piezo.VEL('3', self.settings.speed)
                self.Piezo.MOV('3', 0) 

                #While the Piezo is moving, stop if **Stop Criteria** is met
                while any(list(self.Piezo.gcscommands.IsMoving().values())):
                    time.sleep(1)
                
                    if self.event_stopTip.is_set():
                        print('[DEBUG] Landing succesful!?')
                        return
                    
                    if self.threadInstance.isInterruptionRequested():
                        self.Piezo.gcscommands.HLT(noraise=True)
                        print('[SECCM] Approach Interrupted by User!')
                        return 

                #If the Piezo reaches its limit without being stopped, reset the piezo and move the Z-Stage by the corresponding amount
                #*** Set event_piezoLimit to signal potentiostat to stop during piezo reset***
                self.event_piezoLimit.set() 
                self.event_piezoReady.clear()
                counter+=1
                print("[SECCM] Piezo Limit Reached")
            
                self.Zstage.gcscommands.MVR('1', -0.06) 
                self.Piezo.gcscommands.VEL('3', 5) 
                self.Piezo.gcscommands.MOV('3', 60) 

                # Waiting for positioner reset to be done
                while any(list(self.Zstage.gcscommands.IsMoving().values())):
                    time.sleep(1)
                    if self.threadInstance.isInterruptionRequested():
                        self.Zstage.gcscommands.HLT(noraise=True)
                        print('[SECCM] Approach Interrupted by User!')
                        return

                #*** Emit signal to signal piezo have been reset to potentiostat***
                self.currentPosition= [-1*round(self.XYstage.qPOS()['1'],3), round(self.XYstage.qPOS()['2'],3), round(self.Zstage.qPOS()['1']-25,3)]
                self.position.emit(self.currentPosition)  
                self.event_piezoLimit.clear() 
                self.event_piezoReady.set() 
                print("[SECM] Positioners Reset")

        except GCSError as err:
            print(f'[ERROR] **SECM|SECM_PI|approachPI**: {err}.')
                
        except IOError:
            print('[ERROR] **SECCM|SECCM_PI|approachPI**: Checked if Controller is Turned ON.')

        except Exception as err:
            # Handle the exception gracefully
            print(f"[ERROR] **SECCM|SECCM_PI|approachPI**: {err}")
            # Optional: Return a default fallback value or re-raise with 'raise'
            return None 
        
        finally:
            # This block always runs, even if an exception or return occurred
            self.Zstage.gcscommands.VEL(1,1)
            self.clean()

    #region: Utility 
    def clean(self):
        self.finished.emit()


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#region: SECCM BL
class SECM_BL(QObject): 

    finished= Signal() # Signal that process is over
    echemData= Signal(object) # Echem data sent as a dict {'t':time, 'Ewe':potential, 'Iwe':current, 'cycle':cycle} *exception for OCP only has time and potential
    technique= Signal(object)
    done= Signal()

    def __init__(self, threadInstance:QThread, potentiostat, SECMsettings: UI_Settings.SECM, event:dict[str,threading.Event], techniqueList):
        super().__init__()

        self.channel:int= potentiostat['channel']
        self.id_= potentiostat['id_']
        self.api:KBIO_api= potentiostat['api']
        self.board_type= potentiostat['board_type']
        self.verbosity:int = 1
        self.threadInstance= threadInstance

        self.settings:UI_Settings.SECM= SECMsettings
        self.event_piezoReady:threading.Event= event['ready']
        self.event_piezoLimit:threading.Event= event['limit']
        self.event_stopTip:threading.Event= event['stop']
        self.techniqueList= techniqueList

    def debug(self):
        print("[SECM] VMP-300 Tip Down")
        
        for techSettings in self.techniqueList:
                        
            print(f'Running: {techSettings}')
            self.technique.emit(techSettings)
            for i in range(1,25):
                self.echemData.emit({'t': i, 'Ewe': round(random.uniform(1.0, 2.0), 2), 'Iwe':round(random.uniform(5, 10.0), 2), 'cycle': 1})
                time.sleep(0.1)

            self.finished.emit()
        self.finished.emit()

    def map(self):
        pass

    #region: ApproachBL
    def approach(self):
    
        try:
            iData= []
            self.event_piezoReady.wait()
            print("[SECM] VMP-300 Tip Down")
            approachSettings= UI_Settings.echemSettings('CA', duration=10800, potential= self.settings.Eapp, dt=0.1, iRange= self.settings.iRange)
            self.loadTechnique(approachSettings)
            self.api.StartChannel(self.id_, self.channel)
            
            while True: 

                data= self.api.GetData(self.id_, self.channel)
                status, tech_name= get_info_data(self.api, data) 

                for output in get_experiment_data(self.api, data, tech_name, self.board_type):
                    iData.append(output['Iwe'])

                    if len(iData)>30: # Function that determine if the tip should be stopped based on the stop criteria
                        break
                
                iBulk=sum(iData[10:])/len(iData)
                iMin, iMax= self.tipStop(iBulk)
            
                for output in get_experiment_data(self.api, data, tech_name, self.board_type):
                    self.echemData.emit(output)

                    if output['Iwe']<iMin or output['Iwe']>iMax: # Function that determine if the tip should be stopped based on the stop criteria
                        self.event_stopTip.set() # Set the 'stop' event flag. Signal the end of approach curve: Stop all activity!
                        print('[DEBUG] Tip Down Interrupted by Stop Criteria')
                        return

                # Stop the measurement once the piezo limit is reached
                if self.event_piezoLimit.is_set():
                    print("[DEBUG] VMP-300 interrupted, waiting until piezo are reinitialized")
                    break

                if status == "STOP":
                    print(f'Approach duration exceeded the time limit of 10800')
                    return

                if self.threadInstance.isInterruptionRequested():
                    return
        
        except Exception as err:
            # Handle the exception gracefully
            print(f"[ERROR] **SECM|SECM_BL|approachBL**: {exception_brief(err, self.verbosity >= 1)}")
            # Optional: Return a default fallback value or re-raise with 'raise'
            self.finished.emit()
            return None 
        
        finally:
            # This block always runs, even if an exception or return occurred
            self.finished.emit()

    def runEchem(self):
        try:
            for tech in self.techniqueList:
                        
                self.loadTechnique(tech)
                self.api.StartChannel(self.id_, self.channel)
                self.technique.emit(tech)
                print(f'[VMP-300] Running: {tech}')

            #while loop will emit echem data while potentiostat is running
            while True:
                data= self.api.GetData(self.id_, self.channel)
                status, tech_name= get_info_data(self.api, data)
                for output in get_experiment_data(self.api, data, tech_name, self.board_type):
                    self.echemData.emit(output)

                if status == "STOP":
                    print(f'[VMP-300] Succesful {tech.technique} Measurement')
                    break
            
                if self.threadInstance.isInterruptionRequested():
                    print(f'[VMP-300] {tech.technique} Measurement Stopped by User')
                    break

            self.done.emit()

        except Exception as err:
            # Handle the exception gracefully
            print(f"[ERROR] **SECM|SECM_BL|runEchem**: {exception_brief(err, self.verbosity >= 1)}")
            # Optional: Return a default fallback value or re-raise with 'raise'
            return None 
        
        finally:
            self.finished.emit()

    def loadTechnique(self, tech):

        ecc_parms= False
        tech_file= False

        match tech.technique:
            case 'CA':
                tech_file, ecc_parms= ca_parm(self.board_type, self.api, tech)
            case 'OCP':
                tech_file, ecc_parms= ocp_parm(self.board_type, self.api, tech)
            case 'CV':
                tech_file, ecc_parms= cv_parm(self.board_type, self.api, tech)
            case 'CP':
                tech_file, ecc_parms= cp_parm(self.board_type, self.api, tech)
            case _:
                print("> Invalid technique or settings")

        self.api.LoadTechnique(self.id_, self.channel, tech_file, ecc_parms, first=True, last=True, display=(self.verbosity > 1))

    def tipStop(self, ibulk):
            
            match self.settings.stop:
                case 0: #tip stop based relative current change
                    imax= ibulk*self.settings.limPos
                    imin= ibulk*self.settings.limNeg
                  
                case 1: #tip stop based absolute current change
                    imax= ibulk+self.settings.limPos
                    imin= ibulk-self.settings.limNeg
                
                case 2: #tip stop based on current limit
                    imax= self.settings.limPos
                    imin= self.settings.limNeg

            return imin,imax  

class threadInit():
    def __init__(self, workerClass, *arg):
        self.thread= QThread()
        self.worker= workerClass(self.thread, *arg)
        self.worker.moveToThread(self.thread)

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

if __name__ == '__main__':
    print('Package for SECCM approach, Does nothing')
