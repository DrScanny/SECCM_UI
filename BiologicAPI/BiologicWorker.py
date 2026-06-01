import os
import sys

from PySide6.QtCore import Qt, QObject, QThread, Signal, Slot

from BiologicAPI.kbio.kbio_tech import get_experiment_data
from BiologicAPI.kbio.kbio_tech import get_info_data
from BiologicAPI.kbio.utils import exception_brief

from Biologic import Biologic
from BiologicAPI.CA_biologic import ca_parm
from BiologicAPI.OCP_biologic import ocp_parm
from BiologicAPI.CP_biologic import cp_parm
from BiologicAPI.CV_biologic import cv_parm

class BiologicWorker(QObject):

    finished= Signal()
    echemData= Signal(object)
    connection= Signal(list)
    warning= Signal(str)

    def __init__(self, potentiostat:Biologic):
        super().__init__()

        self.channel= potentiostat.channel
        self.id_= potentiostat.id_
        self.api= potentiostat.api
        self.board_type= potentiostat.board_type
        self.verbosity= 1

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

    def runExperiment(self, technique):
                        
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

    print('Biologic Worker Class')
