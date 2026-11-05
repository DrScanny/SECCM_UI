import os
import sys
import numpy as np
import time
import functools
import threading
from pathlib import Path
import random


from PySide6.QtCore import QObject, Signal, QThread

from pipython import GCSDevice, GCSError

from BiologicAPI.kbio.kbio_api import KBIO_api
from BiologicAPI.kbio.kbio_tech import get_experiment_data
from BiologicAPI.kbio.kbio_tech import get_info_data
from kbio.utils import exception_brief

from BiologicAPI.CA_biologic import ca_parm
from BiologicAPI.OCP_biologic import ocp_parm
from BiologicAPI.CV_biologic import cv_parm
from BiologicAPI.CP_biologic import cp_parm

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

    def __init__(self, threadInstance:QThread, PIdevice:dict[str,GCSDevice], SECMsettings:UI_Settings.SECM, mapCoordinates, event:dict[str,threading.Event]):
        super().__init__()

        self.XYstage:GCSDevice= PIdevice['XY']
        self.Zstage:GCSDevice= PIdevice['Z']
        self.Piezo:GCSDevice= PIdevice['Pz']
        
        self.settings:UI_Settings.SECM= SECMsettings
        self.event_ready:threading.Event= event['ready']
        self.event_stop:threading.Event= event['stop']
        self.threadInstance= threadInstance
        self.mapCoordinates= mapCoordinates
        
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

    def const_dist(self):
        
        for coordinates in self.mapCoordinates:
            self.XYstage.gcscommands.MOV(['1','2'], coordinates)
            while any(list(self.XYstage.gcscommands.IsMoving().values())):
                time.sleep(0.25)
                self.position.emit([-1*round(self.XYstage.qPOS()['1'],3), 
                                    round(self.XYstage.qPOS()['2'],3), 
                                    round(self.Zstage.qPOS()['1']-25,3), 
                                    round(self.Piezo.qPOS()['3'],3)])

            self.event_ready.set()
            time.sleep(2)


    def approach(self): #Method for approach curve

        try:
            positioner= self.Zstage #Default positioner use for approach curve
            match self.settings.positioner: #Match the chosen positioner to the appropriate method for approaching

                case 0: #Coarse positioning with Z-stage
                    print("Preparing Z-stage for SECM approach (~ 5s), please wait...")
                    self.Piezo.gcscommands.MOV('3', 0) #Making sure piezo is neutral
                    self.Zstage.gcscommands.VEL('1', self.settings.speed/1000) #Assign user chosen speed to Zstage
 
                    self.event_ready.wait() #Wait until bulk current measurement is terminated and coordinate positioner movement with echem measurement
                    self.Zstage.gcscommands.MOV('1', 0) #Move Z-stage toward sample
                
                case 1: #Coarse positioning with Z-stage
                    print("Preparing Piezo for SECM approach (~ 20s), please wait...")
                    positioner=self.Piezo

                    #Move Piezo up 100 um
                    self.Piezo.gcscommands.VEL('3', 10)
                    self.Piezo.gcscommands.MOV('3', 100)
                    time.sleep(1)

                    #Move Z-stage down 100 um to offset the Piezo going up
                    self.Zstage.gcscommands.VEL('1', 10e-3)
                    self.Zstage.gcscommands.MVR('1', -0.1)
                    self.wait(self.Piezo)

                    self.Piezo.gcscommands.VEL('3', self.settings.speed)
                    self.event_ready.wait() 
                    self.Piezo.gcscommands.MOV('3', 0)

                case _:
                    print('[ERROR] Positioner not recognized')
                    return

            # Waiting for further commands while positioner are moving except for special case interrupt: 1- Tip approach stoppage, 2- User stoppage
            self.wait(positioner)
                 
        except GCSError as err:
            print(f'[ERROR] **SECM|SECM_PI|approachPI**: {err}.')
                
        except IOError:
            print('[ERROR] **SECCM|SECCM_PI|approachPI**: Controller unresponsive, check if its Turned ON.')

        except Exception as err:
            # Handle the exception gracefully
            print(f"[ERROR] **SECCM|SECCM_PI|approachPI**: {err}")
            # Optional: Return a default fallback value or re-raise with 'raise'
            return None 
        
        finally:
            # This block always runs, even if an exception or return occurred
            self.clean()

    #region: Utility 
    def clean(self): #This utility method always run at the end of any measurements. 1- Resets settings 2-Update positions 3-Emit finished signal
        self.Zstage.gcscommands.VEL(1,1)
        self.position.emit([-1*round(self.XYstage.qPOS()['1'],3), 
                            round(self.XYstage.qPOS()['2'],3), 
                            round(self.Zstage.qPOS()['1']-25,3), 
                            round(self.Piezo.qPOS()['3'],3)])
        self.finished.emit()

    # This utility method is to prevent any stage movement command inputs while stages are running. The method can be interrupted: 1- Tip approach stoppage, 2- User interrupt
    def wait(self, positioner): 
         
        #Loop that run until the positioner stops emiting the IsMoving signal
        while any(list(positioner.gcscommands.IsMoving().values())):

            #While the Piezo is moving, stop if **Stop Criteria** is met
            if self.event_stop.is_set():
                positioner.gcscommands.HLT(noraise=True)
                print('[DEBUG] Landing succesful!?')
                return
                            
            #While the Piezo is moving, stop if user pressed stop
            if self.threadInstance.isInterruptionRequested():
                positioner.gcscommands.HLT(noraise=True)
                print('[MSG] Approach Interrupted by User!')
                return 
        
            #While stage is moving it updates the position
            self.position.emit([-1*round(self.XYstage.qPOS()['1'],3), 
                                round(self.XYstage.qPOS()['2'],3), 
                                round(self.Zstage.qPOS()['1']-25,3), 
                                round(self.Piezo.qPOS()['3'],3)])

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#region: SECM BL
class SECM_BL(QObject): 

    finished= Signal() # Signal that process is over
    echemData= Signal(object) # Echem data sent as a dict {'t':time, 'Ewe':potential, 'Iwe':current, 'cycle':cycle} *exception for OCP only has time and potential
    technique= Signal(object)
    done= Signal()

    def __init__(self, threadInstance:QThread, potentiostat, SECMsettings: UI_Settings.SECM, techniqueList, event:dict[str,threading.Event]):
        super().__init__()

        self.channel:int= potentiostat['channel']
        self.id_= potentiostat['id_']
        self.api:KBIO_api= potentiostat['api']
        self.board_type= potentiostat['board_type']
        self.verbosity:int = 1
        self.threadInstance= threadInstance
      
        self.settings:UI_Settings.SECM= SECMsettings
        self.event_ready:threading.Event= event['ready']
        self.event_stop:threading.Event= event['stop']
        self.techniqueList= None

    #region: ApproachBL
    def approach(self):
    
        try:
            #By default coarse approach
            time=10800
            timestep= 0.1
            nBulk= 50

            #Storage for measuring bulk current
            match self.settings.positioner:
                case 0:
                    pass
                
                case 1:
                    time=3600
                    timestep= 0.005
                    nBulk= 3000
            
            #For SECM approach curve for now only chronoamp approach
            approachSettings= UI_Settings.echemSettings('CA', duration=time, potential= self.settings.Eapp, dt=timestep, iRange= self.settings.iRange)
            self.technique.emit(approachSettings)
            self.loadTechnique(approachSettings)
            self.api.StartChannel(self.id_, self.channel)

            #Measuring bulk current first
            i=0
            iBulkData= np.zeros(nBulk)
            print('Measuring bulk current')
            while i<nBulk: 

                data= self.api.GetData(self.id_, self.channel)
                status, tech_name= get_info_data(self.api, data) 
   
                for output in get_experiment_data(self.api, data, tech_name, self.board_type):
                    iBulkData[i]=output['Iwe']
                    i+=1
                
                if self.threadInstance.isInterruptionRequested():
                    return
            
            iBulk=np.average(iBulkData[int(nBulk*0.8):])
            iMin, iMax= self.tipStop(iBulk)
            print(f'bulk current measurement finished ibulk={iBulk} iMin={iMin} and iMax={iMax}')   

            #Wait until positioners are reset to start potentiostat
            print('Starting measurement')
            self.event_ready.set() 
            
            #Once bulk current is established, start true measurement
            while True: 

                data= self.api.GetData(self.id_, self.channel)
                status, tech_name= get_info_data(self.api, data) 
                    
                for output in get_experiment_data(self.api, data, tech_name, self.board_type):
                    #Measurement is stopped if stop condition is fulfilled
                    if np.abs(output['Iwe'])<iMin or np.abs(output['Iwe'])>iMax: # Function that determine if the tip should be stopped based on the stop criteria
                        self.event_stop.set() # Set the 'stop' event flag. Signal the end of approach curve: Stop all activity!
                        
                        print(output['Iwe'], np.abs(output['Iwe'])<iMin, np.abs(output['Iwe'])>iMax)
                        print('[MSG] Tip Down Interrupted by Stop Criteria')
                        return
                    self.echemData.emit(output)
            
                # Measurement is stopped if reached time limit or user stop
                if status == "STOP":
                    print(f'Approach duration exceeded the time limit')
                    return

                if self.threadInstance.isInterruptionRequested():
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

    def const_dist(self):

        time=43200
        timestep= 1
        
        approachSettings= UI_Settings.echemSettings('CA', duration=time, potential= self.settings.Eapp, dt=timestep, iRange= self.settings.iRange)
        self.technique.emit(approachSettings)
        self.loadTechnique(approachSettings)
        self.api.StartChannel(self.id_, self.channel)

        while True: 
    
            data= self.api.GetData(self.id_, self.channel)
            status, tech_name= get_info_data(self.api, data) 
                
            for output in get_experiment_data(self.api, data, tech_name, self.board_type):
                #Measurement is stopped if stop condition is fulfilled
                if self.event_ready.is_set():
                    self.echemData.emit(output)
        
            # Measurement stop signals: 1- Duration exceeded, 2- Mapping completed, 3- User interruption
            if status == "STOP":
                print(f'Approach duration exceeded the time limit')
                return

            if self.event_stop.is_set():
                return

            if self.threadInstance.isInterruptionRequested():
                return

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
                    imax= np.abs(ibulk*self.settings.limPos/100)
                    imin= np.abs(ibulk*self.settings.limNeg/100)
                  
                case 1: #tip stop based absolute current change
                    imax= np.abs(ibulk+self.settings.limPos)
                    imin= np.abs(ibulk-self.settings.limNeg)
                
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
