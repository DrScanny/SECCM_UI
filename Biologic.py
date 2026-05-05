import os
import sys

from typing import TextIO

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

import SECCM_Settings

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
                return "Time (s), E vs Ref (V), I (A), Cycle"
            case 'OCP':
                tech_file, ecc_parms= ocp_parm(self.board_type, self.api, techniqueSettings)
                return "Time (s), E vs Ref (V)"
            case 'CV':
                tech_file, ecc_parms= cv_parm(self.board_type, self.api, techniqueSettings)
                return "Time (s), E vs Ref (V), I (A), Cycle"
            case 'CP':
                tech_file, ecc_parms= cp_parm(self.board_type, self.api, techniqueSettings)
                return  "Time (s), E vs Ref (V), I (A), Cycle"
            case _:
                return "No header"

        # BL_LoadTechnique
        try: 
            self.api.LoadTechnique(self.id_, self.channel, tech_file, ecc_parms, first=True, last=True, display=(self.verbosity > 1))
        except:
            print("> Invalid technique or settings")


    def start_channel(self):

        self.api.StartChannel(self.id_, self.channel)

    def read_data(self, filename:TextIO | None= None):
        
        self.data= self.api.GetData(self.id_, self.channel)
        self.status, self.tech_name= get_info_data(self.api, self.data)

        for output in get_experiment_data(self.api, self.data, self.tech_name, self.board_type):
            dataline= ','.join(str(item) for item in output.values())
            if filename:
                dataFile.write(dataline)
                dataFile.write('\n')
            else:
                print(dataline)

    def disconnect(self):
        self.api.Disconnect(self.id_)
        print('Disconnected from potentiostat')

    def run_exp(self, filename:str, techList:list[  SECCM_Settings.OCPsettings 
                                                  | SECCM_Settings.CAsettings 
                                                  | SECCM_Settings.CVsettings 
                                                  | SECCM_Settings.CPsettings]):
        
        with open(filename, 'a') as dataFile:
            
            for index, tech in enumerate(techList): 
                header= self.load_technique(tech)
                dataFile.write(f'Technique {index}: {tech.technique} \n')
                dataFile.write(header)
                self.start_channel()

                while True:
                    VMP300.read_data(dataFile)
                    if VMP300.status == "STOP":
                        break
        

if __name__ == '__main__':

    try: 

        ocp= SECCM_Settings.OCPsettings('OCP', 10, 0.1, 1, 0)
        ca= SECCM_Settings.CAsettings()
        cv= SECCM_Settings.CVsettings()
        cp= SECCM_Settings.CPsettings()

        VMP300= Biologic()
        VMP300.connect()

        techList= [ocp, ca]
        
        with open('test_dataFile', 'a') as dataFile:

            for index, tech in enumerate(techList): 
                VMP300.load_technique(tech)
                dataFile.write(f'Technique {index}: {tech.technique} \n')
                VMP300.start_channel()
                while True:
                    VMP300.read_data(dataFile)
                    if VMP300.status == "STOP":
                        break

        VMP300.disconnect()

    except KeyboardInterrupt:
        print(".. interrupted")

    except Exception as e:
        print(f"{exception_brief(e, VMP300.verbosity>=2)}")
