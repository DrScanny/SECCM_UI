import sys
from dataclasses import dataclass

import kbio.kbio_types as KBIO
from kbio.kbio_tech import ECC_parm
from kbio.kbio_tech import make_ecc_parm
from kbio.kbio_tech import make_ecc_parms

def cp_parm(board_type, api, cp_param):

    #==============================================================================#
    #Each technique has a specific file and they depend on the potentiostat board
    # They all have the same syntax: the technique name + a number '{technique_name}{digit}.ecc'
    #==============================================================================#
    match board_type:
        case KBIO.BOARD_TYPE.ESSENTIAL.value:
            tech_file = f'cp.ecc'
        case KBIO.BOARD_TYPE.PREMIUM.value:
            tech_file = f'cp4.ecc'
        case KBIO.BOARD_TYPE.DIGICORE.value:
            tech_file = f'cp5.ecc'
        case _:
            print("> Board type detection failed")
            sys.exit(-1)

    #==============================================================================#
    # Dictionary of all parameters labels needed for the technique
    # They serve to create pointer for the ecc file using the make_ecc_parm method 
    # The Label text need to be exact from the manual or it won't work!
    #==============================================================================#
    
    CP_parms = {
    "current_step": ECC_parm("Current_step", float),
    "step_duration": ECC_parm("Duration_step", float),
    "vs_init": ECC_parm("vs_initial", bool),
    "nb_steps": ECC_parm("Step_number", int),
    "record_dt": ECC_parm("Record_every_dT", float),
    "record_dE": ECC_parm("Record_every_dE", float),
    "repeat": ECC_parm("N_Cycles", int),
    "I_range": ECC_parm("I_Range", int),
    }

    #==============================================================================#
    # Creating the ecc_parms for LoadTechnique method of api instance of kbio.kbio_api
    #==============================================================================#

    p_currentStep= make_ecc_parm(api, CP_parms["current_step"], cp_param.current, 0)
    p_stepDuration= make_ecc_parm(api, CP_parms["step_duration"], cp_param.duration, 0)
    p_vsInit = make_ecc_parm(api, CP_parms["vs_init"], False, 0)

    # number of steps is one less than len(steps)
    p_nb_steps = make_ecc_parm(api, CP_parms["nb_steps"], 0, 0)

    # record parameters
    p_record_dt = make_ecc_parm(api, CP_parms["record_dt"], cp_param.dt, 0)
    p_record_dE = make_ecc_parm(api, CP_parms["record_dE"], cp_param.dE, 0)

    # repeating factor
    p_repeat = make_ecc_parm(api, CP_parms["repeat"], 0, 0)
    p_I_range = make_ecc_parm(api, CP_parms["I_range"], cp_param.iRange, 0)

    ecc_parms = make_ecc_parms(api, p_currentStep, p_stepDuration, p_vsInit, p_nb_steps, p_record_dt, p_record_dE, p_I_range, p_repeat)

    return tech_file, ecc_parms