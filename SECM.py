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

    def reset(self):
        print("Resetting positioners, will take 10 seconds")
        self.Piezo.gcscommands.VEL('3', 6) 
        self.Piezo.gcscommands.MOV('3', 60) 
        time.sleep(1)
        self.Zstage.gcscommands.VEL(1, 0.006)
        self.Zstage.gcscommands.MVR('1', -0.06) 

        while any(list(self.Zstage.gcscommands.IsMoving().values())):
            if self.threadInstance.isInterruptionRequested():
                self.Zstage.gcscommands.HLT(noraise=True)
                print('[SECCM] Approach Interrupted by User!')
                return
            
        #Signaling piezo ready to potentiostat
        print(f"[SECM] Positioners Reset Z:{round(self.Zstage.qPOS()['1']-25,3)}, Pz:{round(self.Piezo.qPOS()['1'],3)}")
        self.event_piezoReady.set()
        self.event_piezoLimit.clear()

    def map(self):
        pass


    def approach(self):

        try:

            #First step is to prepare the Z-stage or piezo stage for SECM approach depending on user choice
            positioner= self.Zstage

            if self.settings.positioner== 0:
                print("Preparing Z-stage for SECM approach (~ 5s), please wait...")
                self.Zstage.gcscommands.VEL('1', self.settings.speed/1000)
                self.Zstage.gcscommands.MOV('1', 0)
                
                
            elif self.settings.positioner== 1:
                print("Preparing Piezo for SECM approach (~ 20s), please wait...")
                positioner=self.Piezo

                #Move Piezo up 100 um
                self.Piezo.gcscommands.VEL('3', 5)
                self.Piezo.gcscommands.MOV('3', 100)

                #Move Z-stage down 100 um to offset the Piezo going up
                self.Zstage.gcscommands.VEL('1', 5e-3)
                self.Zstage.gcscommands.MVR('1', -0.1)

                while any(list(self.Piezo.gcscommands.IsMoving().values())):

                    self.position.emit([-1*round(self.XYstage.qPOS()['1'],3), 
                                        round(self.XYstage.qPOS()['2'],3), 
                                        round(self.Zstage.qPOS()['1']-25,3), 
                                        round(self.Piezo.qPOS()['3'],3)])
                    
                #Once all positioners are set, we are ready for the approach
                self.Piezo.gcscommands.VEL('3', self.settings.speed)
                self.Piezo.gcscommands.MOV('3', 0)

            else:
                print('[ERROR] Positioner not recognized')
                return
            
            self.event_piezoReady.set()

            while any(list(positioner.gcscommands.IsMoving().values())):

                self.position.emit([-1*round(self.XYstage.qPOS()['1'],3), 
                                    round(self.XYstage.qPOS()['2'],3), 
                                    round(self.Zstage.qPOS()['1']-25,3), 
                                    round(self.Piezo.qPOS()['3'],3)])

                #While the Piezo is moving, stop if **Stop Criteria** is met
                if self.event_stopTip.is_set():
                    print('[DEBUG] Landing succesful!?')
                    return
                
                #While the Piezo is moving, stop if user pressed stop
                if self.threadInstance.isInterruptionRequested():
                    positioner.gcscommands.HLT(noraise=True)
                    print('[SECCM] Approach Interrupted by User!')
                    return 
        
                 
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

    def __init__(self, threadInstance:QThread, potentiostat, SECMsettings: UI_Settings.SECM, event:dict[str,threading.Event]):
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

    def map(self):
        pass

    #region: ApproachBL
    def approach(self):
    
        try:
            nData=500
            nBulk= 25000
            iData=np.zeros(nData)
            iBulkData= np.zeros(nBulk)
            #Wait until positioners are reset to start potentiostat
            self.event_piezoReady.wait()
            
            #For SECM approach curve for now only chronoamp approach
            approachSettings= UI_Settings.echemSettings('CA', duration=10800, potential= self.settings.Eapp, dt=200e-6, iRange= self.settings.iRange)
            self.technique.emit(approachSettings)
            self.loadTechnique(approachSettings)
            self.api.StartChannel(self.id_, self.channel)
            
            for i in range(nBulk): 

                data= self.api.GetData(self.id_, self.channel)
                status, tech_name= get_info_data(self.api, data) 
   
                for output in get_experiment_data(self.api, data, tech_name, self.board_type):
                    iBulkData[i]=output['Iwe']

                if self.threadInstance.isInterruptionRequested():
                    return
            
            iBulk=np.average(iBulkData)
            iMin, iMax= self.tipStop(iBulk)
            print(f'bulk current measurement finished ibulk={iBulk} iMin={iMin} and iMax={iMax}')    

            while True: 

                for i in range(nData):
                    data= self.api.GetData(self.id_, self.channel)
                    status, tech_name= get_info_data(self.api, data) 
                    
                    for output in get_experiment_data(self.api, data, tech_name, self.board_type):
                        #Measurement is stopped if stop condition is fulfilled
                        iData[i]=output['Iwe']
              
                    # Measurement is stopped if reached time limit or user stop
                    if status == "STOP":
                        print(f'Approach duration exceeded the time limit of 10800')
                        return

                    if self.threadInstance.isInterruptionRequested():
                        return
                    
                    echemData= np.average(iData[i])
                    self.echemData.emit(echemData)

                    if echemData<iMin or echemData>iMax: # Function that determine if the tip should be stopped based on the stop criteria
                        self.event_stopTip.set() # Set the 'stop' event flag. Signal the end of approach curve: Stop all activity!
                        print('[DEBUG] Tip Down Interrupted by Stop Criteria')
                        return
                    
        except Exception as err:
            # Handle the exception gracefully
            print(f"[ERROR] **SECM|SECM_BL|approach**: {exception_brief(err, self.verbosity >= 1)}")
            # Optional: Return a default fallback value or re-raise with 'raise'
            self.finished.emit()
            return None 
        
        finally:
            # This block always runs, even if an exception or return occurred
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
                    imax= ibulk*self.settings.limPos/100
                    imin= ibulk*self.settings.limNeg/100
                  
                case 1: #tip stop based absolute current change
                    imax= ibulk+self.settings.limPos
                    imin= ibulk-self.settings.limNeg
                
                case 2: #tip stop based on current limit
                    imax= self.settings.limPos
                    imin= self.settings.limNeg

                case _: #Error case
                    print('tipStop criteria could not be set')
                    imin=0
                    imax=0

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
