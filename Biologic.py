import os
import sys
import numpy as np
import time
import multiprocessing

from typing import TextIO, Any

import kbio.kbio_types as KBIO
from kbio.c_utils import c_is_64b
from kbio.kbio_api import KBIO_api
from kbio.kbio_tech import get_experiment_data
from kbio.kbio_tech import get_info_data
from kbio.utils import exception_brief

from BiologicAPI.CA_biologic import ca_parm
from BiologicAPI.OCP_biologic import ocp_parm
from BiologicAPI.CP_biologic import cp_parm
from BiologicAPI.CV_biologic import cv_parm

import UI_Settings

def _stopTip(potentiostatOutput, approachSettings: UI_Settings.SECCM)-> bool:
    match approachSettings.stop:
        case 'Open Circuit Potential':
            if abs(potentiostatOutput['Ewe'])<=1.5:
                return True
            else:
                return False
                
        case 'Potentiostatic':
            if abs(potentiostatOutput['Iwe']<UI_Settings.SECCM.Istop):
                return True
            else:
                return False
        
        case 'Alternating Current':
            print('Not implemented yet')
            return False
        
        case _:
            return False

class Biologic():
    
    def __init__(self):
        self.channel= None
        self.id_= None
        self.api= None
        self.board_type= None
        self.verbosity= 1

    def connect(self, ip_address= "192.168.2.2", channel_nb= 1):
        try:
            address= ip_address
            self.channel= channel_nb

            # In the software, you might need to have input for changing address and channel
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

            return True

        except:
            print("\nConnection to VMP-300 Failed: Biologic -> connect")
            return False

    def load_technique(self, techniqueSettings):

        match techniqueSettings.technique:
            case 'CA':
                tech_file, ecc_parms= ca_parm(self.board_type, self.api, techniqueSettings)
            case 'OCP':
                tech_file, ecc_parms= ocp_parm(self.board_type, self.api, techniqueSettings)
            case 'CV':
                tech_file, ecc_parms= cv_parm(self.board_type, self.api, techniqueSettings)
            case 'CP':
                tech_file, ecc_parms= cp_parm(self.board_type, self.api, techniqueSettings)
            case _:
                print("> Invalid technique or settings")

        # BL_LoadTechnique
        try: 
            self.api.LoadTechnique(self.id_, self.channel, tech_file, ecc_parms, first=True, last=True, display=(self.verbosity > 1))
        except:
            print("> Invalid technique or settings")

    def start_channel(self):
        self.api.StartChannel(self.id_, self.channel)

    def disconnect(self):
        self.api.Disconnect(self.id_)
        print('Disconnected from potentiostat')

    def runExperiments(self, *techniques:  UI_Settings.OCP
                                          |UI_Settings.CA
                                          |UI_Settings.CV
                                          |UI_Settings.CP
                            ,dataFile:TextIO|None= None):
                            
        echemData={}
        for index, tech in enumerate(techniques):
            data=[]
            self.load_technique(tech)
            self.start_channel()

            if dataFile:
                dataFile.write(tech.header+'\n')

            while True:
                self.data= self.api.GetData(self.id_, self.channel)
                self.status, self.tech_name= get_info_data(self.api, self.data)
                for output in get_experiment_data(self.api, self.data, self.tech_name, self.board_type):

                    dataline= ','.join(str(item) for item in output.values())
                    data.append(dataline)

                    if dataFile:
                        dataFile.write(dataline +'\n')
                    else:
                        print(dataline)

                if self.status == "STOP":
                    echemData[index]= data
                    break

        return echemData
     
if __name__ == '__main__':

    try: 

        ocp= UI_Settings.OCP('OCP', 10, 0.1, 1, 0)
        ca= UI_Settings.CA()
        cv= UI_Settings.CV()
        cp= UI_Settings.CP()

        VMP300= Biologic()
        VMP300.connect()
   
        VMP300.disconnect()

    except KeyboardInterrupt:
        print(".. interrupted")

    except Exception as e:
        print(f"{exception_brief(e, VMP300.verbosity>=2)}")
