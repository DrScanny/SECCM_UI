import os
import sys
import time
import random

from PySide6.QtCore import Qt, QObject, QThread, Signal, Slot
import functools

import kbio.kbio_types as KBIO
from kbio.c_utils import c_is_64b
from kbio.kbio_api import KBIO_api

from BiologicAPI.kbio.kbio_tech import get_experiment_data
from BiologicAPI.kbio.kbio_tech import get_info_data
from kbio.utils import exception_brief

from BiologicAPI.CA_biologic import ca_parm
from BiologicAPI.OCP_biologic import ocp_parm
from BiologicAPI.CP_biologic import cp_parm
from BiologicAPI.CV_biologic import cv_parm

def _exception(message:str, finish:bool=False):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(self, *args, **kwargs):
                try:
                    # Attempt to execute the decorated function
                    result = func(self, *args, **kwargs)
                    return result

                except Exception as err:
                    # Handle the exception gracefully
                    print(f"[ERROR] {message}: {exception_brief(err, self.verbosity >= 1)}")
                    # Optional: Return a default fallback value or re-raise with 'raise'
                    return False
           
                finally:
                    if finish:
                        # This block always runs, even if an exception or return occurred
                        method= getattr(self, "_clean")
                        method()
                    pass
                    
            return wrapper
        return decorator


class Biologic(QObject):

    finished= Signal() # Signal that process is over
    echemData= Signal(object) # Echem data sent as a dict {'t':time, 'Ewe':potential, 'Iwe':current, 'cycle':cycle} *exception for OCP only has time and potential
    biologic= Signal(object) # Potentiostat api information to connect to instrument
    connectionStatus= Signal(bool)
    technique= Signal(object)
    done= Signal()

    def __init__(self, threadInstance: QThread, instrument, techniqueList):
        super().__init__()

        self.channel= instrument['channel']
        self.id_= instrument['id_']
        self.api= instrument['api']
        self.board_type= instrument['board_type']
        self.verbosity= 1
        self.techniqueList= techniqueList
        self.threadInstance= threadInstance
        
    #region: loadTechnique
    @_exception('Loading technique: Invalid technique or settings')
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

    def debugEchem(self):

        for techSettings in self.techniqueList:
                        
            print(f'Running: {techSettings}')
            self.technique.emit(techSettings)
            for i in range(1,25):
                self.echemData.emit({'t': i, 'Ewe': round(random.uniform(1.0, 2.0), 2), 'Iwe':round(random.uniform(5, 10.0), 2), 'cycle': 1})
                time.sleep(0.1)

            self.finished.emit()

    @_exception('Starting Channel')
    def startChannel(self):
        self.api.StartChannel(self.id_, self.channel)

    #region: runEchem
    @_exception('Running Echem technique', finish=True)
    def runEchem(self):

        #Do all technique settings obtained from the experiment loadout tree
  
        for tech in self.techniqueList:
                        
            self.loadTechnique(tech)
            self.startChannel()
            self.technique.emit(tech)
            print(f'[VMP-300] Running: {tech.technique}')

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
            
        self.finished.emit()

    def _clean(self):
        self.finished.emit()

if __name__ == '__main__':

    print('Biologic Class')
