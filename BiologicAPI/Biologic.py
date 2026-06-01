import os
import sys

from PySide6.QtCore import Qt, QObject, QThread, Signal, Slot

import BiologicAPI.kbio.kbio_types as KBIO
from BiologicAPI.kbio.c_utils import c_is_64b
from BiologicAPI.kbio.kbio_api import KBIO_api

from BiologicAPI.kbio.kbio_tech import get_experiment_data
from BiologicAPI.kbio.kbio_tech import get_info_data
from BiologicAPI.kbio.utils import exception_brief

from BiologicAPI.CA_biologic import ca_parm
from BiologicAPI.OCP_biologic import ocp_parm
from BiologicAPI.CP_biologic import cp_parm
from BiologicAPI.CV_biologic import cv_parm

class Biologic(QObject):

    finished= Signal()
    echemData= Signal(object)
    connection= Signal(object)
    warning= Signal(str)

    def __init__(self, potentiostat):
        super().__init__()

        self.channel= potentiostat['channel']
        self.id_= potentiostat['id_']
        self.api= potentiostat['api']
        self.board_type= potentiostat['board_type']
        self.verbosity= 1

    def connectBiologic(self, ip_address= "192.168.2.2", channel_nb= 1):
        try:
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

            self.connection.emit({'channel':self.channel, 'id_':self.id_, 'api':self.api, 'board_type': self.board_type})
            self.finished.emit()

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

    def runEchem(self, technique):
                        
        self.load_technique(technique)
        self.start_channel()

        while True:
            self.data= self.api.GetData(self.id_, self.channel)
            self.status, self.tech_name= get_info_data(self.api, self.data)
            for output in get_experiment_data(self.api, self.data, self.tech_name, self.board_type):

                self.echemData.emit(output)

            if self.status == "STOP":
                break

if __name__ == '__main__':

    print('Biologic Class')
