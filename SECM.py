import os
import sys
import numpy as np
import time
import functools
import threading
from pathlib import Path
import random
from matplotlib import pyplot


from PySide6.QtCore import QObject, Signal, QThread

from pipython import GCSDevice, GCSError, datarectools, pitools

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

    def __init__(self, threadInstance:QThread, PIdevice:dict[str,GCSDevice], SECMsettings:UI_Settings.SECM, mapSettings:UI_Settings.Mapping, event:dict[str,threading.Event]):
        super().__init__()

        self.XYstage:GCSDevice= PIdevice['XY']
        self.Zstage:GCSDevice= PIdevice['Z']
        self.Piezo:GCSDevice= PIdevice['Pz']
        
        self.settings:UI_Settings.SECM= SECMsettings
        self.eventPI:threading.Event= event['PI']
        self.eventBL:threading.Event= event['BL']
        self.event_stop:threading.Event= event['stop']
        self.threadInstance= threadInstance
        self.mapSettings= mapSettings

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

    #region: constDist
    def const_dist(self):
        
        for coordinates in self.mapSettings.map:
            self.XYstage.gcscommands.MOV(['1','2'], coordinates)
            while any(list(self.XYstage.gcscommands.IsMoving().values())):
                time.sleep(0.25)
                self.updatePos()

            time.sleep(self.mapSettings.wait)
            self.event_ready.set()
            self.event_stop.wait()
            self.event_ready.clear()
            self.event_stop.clear()
            print('[DEBUG] Measurement done, moving to new coordinate')

    #region: approach
    def approach(self, record=True): #Method for approach curve

        try:
            self.positioner:GCSDevice= self.Zstage #Default positioner use for approach curve
            self.axis='1'
            match self.settings.positioner: #Match the chosen positioner to the appropriate method for approaching

                case 0: #Coarse positioning with Z-stage
                    print("Preparing Z-stage for SECM approach (~ 5s), please wait...")
                    self.Piezo.gcscommands.MOV('3', 0) #Making sure piezo is neutral
                    self.Zstage.gcscommands.VEL('1', self.settings.speed/1000) #Assign user chosen speed to Zstage
                    time.sleep(1)

                case 1: #Coarse positioning with Z-stage
                    print("Preparing Piezo for SECM approach (~ 20s), please wait...")
                    self.positioner=self.Piezo
                    self.axis='3'

                    #Move Piezo up 100 um
                    self.Piezo.gcscommands.VEL('3', 5)
                    self.Piezo.gcscommands.MOV('3', 100)

                    #Move Z-stage down 100 um to offset the Piezo going up
                    self.Zstage.gcscommands.VEL('1', 5e-3)
                    self.Zstage.gcscommands.MVR('1', -0.1)
                    self.Piezo.gcscommands.VEL('3', self.settings.speed)

                    while any(list(self.positioner.gcscommands.IsMoving().values())):
                        time.sleep(0.01)

                        if self.threadInstance.isInterruptionRequested():
                            self.Zstage.gcscommands.HLT(noraise=True)
                            print('[MSG] Approach Interrupted by User!')
                            return
                        
                    time.sleep(1)

                case _:
                    print('[ERROR] Positioner not recognized')
                    return
            
            if record: #Option to record data from positioner
                try:
                    self.recordData()

                except GCSError as err:
                    print(f'[ERROR] **SECM|SECM_PI|approachPI**: {err}.')
                
            #[Event] Signaling positioner ready and waiting until potentiostat is ready
            self.eventPI.set() #PI positioner ready
            self.eventBL.wait() #Wait until bulk current measurement is terminated and coordinate positioner movement with echem measurement
            
            #[Command] Once both potentiostat and positioner are ready start approaching
            self.positioner.gcscommands.MOV(self.axis, 0)

            # Waiting for further commands while positioner are moving except for special case interrupt: 1- Tip approach stoppage, 2- User stoppage
            while any(list(self.positioner.gcscommands.IsMoving().values())):
            
                
                #While the Piezo is moving, stop if **Stop Criteria** is met
                if self.event_stop.is_set():
                    self.positioner.gcscommands.HLT(noraise=True)
                    print('[DEBUG] Landing succesful!?')
                    break
                                
                #While the Piezo is moving, stop if user pressed stop
                if self.threadInstance.isInterruptionRequested():
                    self.positioner.gcscommands.HLT(noraise=True)
                    print('[MSG] Approach Interrupted by User!')
                    break

                #While stage is moving it updates the position
                self.updatePos()
                time.sleep(0.01)

            self.event_stop.set()

            if record:
                try:
                    self.processData()
                except Exception as err:
                    print(f'error with process data {err}')
      
        except GCSError as err:
            print(f'[ERROR] **SECM_PI|approach**: {err}.')
                
        except IOError:
            print('[ERROR]Controller unresponsive, check if its Turned ON.')

        except Exception as err:
            # Handle the exception gracefully
            print(f"[ERROR] **SECM_PI|approach**: {err}")
            # Optional: Return a default fallback value or re-raise with 'raise'
            return None 
        
        finally:
            # This block always runs, even if an exception or return occurred
            print('executing finally block')
            self.Zstage.gcscommands.VEL('1', 1)
            self.Piezo.gcscommands.VEL('3', 5)
            time.sleep(1)
            self.updatePos()
            self.finished.emit()

    #region:utility
    def updatePos(self):
        self.position.emit([-1*round(self.XYstage.qPOS()['1'],3), 
                            round(self.XYstage.qPOS()['2'],3), 
                            round(self.Zstage.qPOS()['1']-25,3), 
                            round(self.Piezo.qPOS()['3'],3)])
    
    #region: record
    def recordData(self):
        self.drec = datarectools.Datarecorder(self.positioner)
        self.drec.samplerate= 200 #Multiple of operating cycle (50 us)
        self.drec.options= datarectools.RecordOptions.ACTUAL_POSITION_2,          
        self.drec.sources= self.axis
        self.drec.trigsources= datarectools.TriggerSources.POSITION_CHANGING_COMMAND_1
        self.drec.arm()

    def processData(self):
        print('Processing Data')
        #print(self.drec.timescale)
        header, data = self.drec.getdata()
        npdata = np.array([data[0]])
        print(npdata)
        np.savetxt('posOutput.txt', npdata, newline='\n', delimiter=',')
        #np.savetxt('timeOutput.txt', timeData, newline='\n', delimiter=',')

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#region: SECM BL
class SECM_BL(QObject): 

    finished= Signal() # Signal that process is over
    echemData= Signal(object) # Echem data sent as a dict {'t':time, 'Ewe':potential, 'Iwe':current, 'cycle':cycle} *exception for OCP only has time and potential
    technique= Signal(object)
    done= Signal()

    def __init__(self, threadInstance:QThread, potentiostat, SECMsettings: UI_Settings.SECM, mapSettings:UI_Settings.Mapping, event:dict[str,threading.Event]):
        super().__init__()

        self.channel:int= potentiostat['channel']
        self.id_= potentiostat['id_']
        self.api:KBIO_api= potentiostat['api']
        self.board_type= potentiostat['board_type']
        self.verbosity:int = 1
        self.threadInstance= threadInstance
      
        self.settings:UI_Settings.SECM= SECMsettings
        self.mapSettings:UI_Settings.Mapping= mapSettings
        self.eventPI:threading.Event= event['PI']
        self.eventBL:threading.Event= event['BL']
        self.event_stop:threading.Event= event['stop']
        self.techniqueList= None

    #region: ApproachBL
    def approach(self):
    
        try:
            #By default coarse approach with Z-stage settings
            expTime=10800
            timestep= 0.01
            nBulk= 50

            #Storage for measuring bulk current
            match self.settings.positioner:
                case 0: #Case for coarse approach with Z-stage
                    pass
                
                case 1: #Case for fine approach with Piezo
                    expTime=3600
                    timestep= 0.01
                    nBulk= 500
            
            #For SECM approach curve for now only chronoamp approach
            approachSettings= UI_Settings.echemSettings('CA', duration=expTime, potential= self.settings.Eapp, dt=timestep, iRange= self.settings.iRange)
            self.technique.emit(approachSettings)
            self.loadTechnique(approachSettings)
            self.api.StartChannel(self.id_, self.channel)

            #Measuring bulk current first
            i=0
            iBulkData= np.zeros(nBulk)
            print('Measuring bulk current')
            while True: 
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
                self.eventBL.set() #Potentiostat ready
                self.eventPI.wait() #Waiting for positioner to be ready for approach
                print('Starting measurement')

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

                    if self.event_stop.is_set():
                        print('[MSG] Reached positioner limit, measurement stopped!')
                        return

                    if self.threadInstance.isInterruptionRequested():
                        return
                
        except Exception as err:
            # Handle the exception gracefully
            print(f"[ERROR] **SECM|SECM_BL|approach**: {exception_brief(err, self.verbosity >= 1)}")
            # Optional: Return a default fallback value or re-raise with 'raise'
            return 
        
        finally:
            # This block always runs, even if an exception or return occurred
            self.finished.emit()

    #region: constDist_BL
    def const_dist(self):

        time=43200
        timestep= 1
        map_data= np.zeros(self.mapSettings.Ndata)
        idx=0
        
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
                    if idx==self.mapSettings.Ndata:
                        self.echemData.emit(map_data)
                        idx=0
                        self.event_stop.is_set()
                        
                    else:
                        map_data[idx]= output['Iwe']
                        idx+=1
        
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

    #region: tipStop
    def tipStop(self, ibulk):
            
            match self.settings.stop:
                case 0: #tip stop based relative current change
                    imax= np.abs(ibulk)*(1+self.settings.limPos/100)
                    imin= np.abs(ibulk)*(1-self.settings.limNeg/100)
                  
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
