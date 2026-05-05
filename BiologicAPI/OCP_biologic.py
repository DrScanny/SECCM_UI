import sys

import kbio.kbio_types as KBIO
from kbio.kbio_tech import ECC_parm
from kbio.kbio_tech import make_ecc_parm
from kbio.kbio_tech import make_ecc_parms

def ocp_parm(board_type, api, ocp_settings):

    #==============================================================================#
    #Each technique has a specific file and they depend on the potentiostat board
    # They all have the same syntax: the technique name + a number '{technique_name}{digit}.ecc'
    #==============================================================================#
    match board_type:
        case KBIO.BOARD_TYPE.ESSENTIAL.value:
            tech_file = f'ocv.ecc'
        case KBIO.BOARD_TYPE.PREMIUM.value:
            tech_file = f'ocv4.ecc'
        case KBIO.BOARD_TYPE.DIGICORE.value:
            tech_file = f'ocv5.ecc'
        case _:
            print("> Board type detection failed")
            sys.exit(-1)

    #==============================================================================#
    # Dictionary of all parameters labels needed for the technique
    # They serve to create pointer for the ecc file using the make_ecc_parm method 
    # The Label text need to be exact from the manual or it won't work!
    #==============================================================================#

    OCV_parms = {
    "duration": ECC_parm("Rest_time_T", float),
    "record_dt": ECC_parm("Record_every_dT", float),
    "record_dE": ECC_parm("Record_every_dE", float),
    "E_range": ECC_parm("E_Range", int),
    "timebase": ECC_parm("tb", int),
    }

    #==============================================================================#
    # Creating the ecc_parms for LoadTechnique method of api instance of kbio.kbio_api
    #==============================================================================#

    p_duration= make_ecc_parm(api, OCV_parms["duration"], ocp_settings.duration)
    p_record_dt= make_ecc_parm(api, OCV_parms["record_dt"], ocp_settings.dt)
    p_record_dE= make_ecc_parm(api, OCV_parms["record_dE"], ocp_settings.dE)
    p_erange= make_ecc_parm(api, OCV_parms["E_range"], ocp_settings.eRange)
    
    ecc_parms = make_ecc_parms(api, p_duration, p_record_dt, p_record_dE, p_erange)

    print('OCP technique loaded')

    return tech_file, ecc_parms