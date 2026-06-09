import os
import sys
import random
import time

from PySide6.QtCore import Qt, QObject, QThread, Signal, Slot
from typing import TypedDict
import functools

import kbio.kbio_types as KBIO
from kbio.c_utils import c_is_64b
from kbio.kbio_api import KBIO_api

from BiologicAPI.kbio.kbio_tech import get_experiment_data
from BiologicAPI.kbio.kbio_tech import get_info_data

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
                    print(f"[ERROR] {message}")
                    # Optional: Return a default fallback value or re-raise with 'raise'
                    return None 
           
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
    message= Signal(str) # Any 'str' to communicate with user 

    def __init__(self, instrument, techniqueList=None):
        super().__init__()

        self.channel= instrument['channel']
        self.id_= instrument['id_']
        self.api= instrument['api']
        self.board_type= instrument['board_type']
        self.verbosity= 1
        self.techniqueList= techniqueList
        self.runBiologic= True

    #region: connectBiologic
    @_exception('Connection to VMP-300: Check if instrument if turned ON.', finish=True)
    def connectBiologic(self, ip_address= "192.168.2.2", channel_nb= 1):

        address= ip_address
        self.channel= channel_nb

        binary_path= os.getcwd()
        force_load_firmware = True

        # determine library file according to Python version (32b/64b)
        if c_is_64b:
            DLL_file = "EClib64.dll"
        else:
            DLL_file = "EClib.dll"

        DLL_path = f"{binary_path}{os.sep}BiologicAPI{os.sep}lib{os.sep}{DLL_file}"

        # ==============================================================================#

        # API initialize
        self.api = KBIO_api(DLL_path)

        # BL_GetLibVersion
        version = self.api.GetLibVersion()
        print()
        # BL_Connect

        self.id_, device_info = self.api.Connect(address)
        print(device_info)
        print()

        # based on board_type, determine firmware filenames
        self.board_type = self.api.GetChannelBoardType(self.id_, self.channel)
        match self.board_type:
            case KBIO.BOARD_TYPE.ESSENTIAL.value:
                firmware_path = "kernel.bin"
                fpga_path = "Vmp_ii_0437_a6.xlx"
            case KBIO.BOARD_TYPE.PREMIUM.value:
                firmware_path = "kernel4.bin"
                fpga_path = "vmp_iv_0395_aa.xlx"
            case KBIO.BOARD_TYPE.DIGICORE.value:
                firmware_path = "kernel.bin"
                fpga_path = ""
            case _:
                print("> Board type detection failed")
                sys.exit(-1)

        # Load firmware
        print(f"> Loading {firmware_path} ...")
        # create a map from channel set
        channel_map = self.api.channel_map({self.channel})
        # BL_LoadFirmware
        self.api.LoadFirmware(self.id_, channel_map, firmware=firmware_path, fpga=fpga_path, force=force_load_firmware)
        print("> ... firmware loaded")
        print()

        # BL_GetChannelInfos
        channel_info = self.api.GetChannelInfo(self.id_, self.channel)
        print(f"> Channel {self.channel} info :")
        print(channel_info)
        print()

        if not channel_info.is_kernel_loaded:
            print("> kernel must be loaded in order to run the experiment")
            sys.exit(-1)

        self.biologic.emit({'api':self.api, 'channel':1, 'board_type': self.board_type, 'id_': self.id_})
        print('[EVENT] Connected to VMP-300!')
  
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

        if tech_file and ecc_parms:
            self.api.LoadTechnique(self.id_, self.channel, tech_file, ecc_parms, first=True, last=True, display=(self.verbosity > 1))

    @_exception('Starting Channel')
    def startChannel(self):
        self.api.StartChannel(self.id_, self.channel)

    def disconnectBiologic(self):
        self.api.Disconnect(self.id_)
        print('[VMP-300] Disconnected')

    #region: runEchem
    @_exception('Running Echem technique', finish=True)
    def runEchem(self):
        
        #Do all technique settings obtained from the experiment loadout tree
        if self.techniqueList:
            for tech in self.techniqueList:
                            
                self.loadTechnique(tech)
                self.startChannel()
                print(f'[VMP-300] Running: {tech.technique}')

                #while loop will emit echem data while potentiostat is running
                while True:
                    data= self.api.GetData(self.id_, self.channel)
                    status, self.tech_name= get_info_data(self.api, data)
                    for output in get_experiment_data(self.api, data, self.tech_name, self.board_type):

                        self.echemData.emit(output)

                    if status == "STOP":
                        print(f'[VMP-300] Succesful {tech.technique} Measurement')
                        break
                    if not self.runBiologic:
                        print(f'[VMP-300] {tech.technique} Measurement Stopped by User')
                        break
        
            self.finished.emit()

    def stopBiologic(self):
        self.runBiologic= False

    def _clean(self):
        self.finished.emit()

    

if __name__ == '__main__':

    print('Biologic Class')
