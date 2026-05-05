import sys
from dataclasses import dataclass

import kbio.kbio_types as KBIO
from kbio.kbio_tech import ECC_parm
from kbio.kbio_tech import make_ecc_parm
from kbio.kbio_tech import make_ecc_parms

def ca_parm(board_type, api, ca_param):

    #==============================================================================#
    #Each technique has a specific file and they depend on the potentiostat board
    # They all have the same syntax: the technique name + a number '{technique_name}{digit}.ecc'
    #==============================================================================#

    tech_file = None
    match board_type:

        case KBIO.BOARD_TYPE.ESSENTIAL.value:
            tech_file = f'ca.ecc'
        case KBIO.BOARD_TYPE.PREMIUM.value:
            tech_file = f'ca4.ecc'
        case KBIO.BOARD_TYPE.DIGICORE.value:
            tech_file = f'ca5.ecc'
        case _:
            print("> Board type detection failed")
            sys.exit(-1)

    #==============================================================================#
    # Dictionary of all parameters labels needed for the technique
    # They serve to create pointer for the ecc file using the make_ecc_parm method 
    # The Label text need to be exact from the manual or it won't work!
    #==============================================================================#

    CP_parms = {
        "voltage_step": ECC_parm("Voltage_step", float),
        "step_duration": ECC_parm("Duration_step", float),
        "vs_init": ECC_parm("vs_initial", bool),
        "nb_steps": ECC_parm("Step_number", int),
        "record_dt": ECC_parm("Record_every_dT", float),
        "record_dI": ECC_parm("Record_every_dI", float),
        "repeat": ECC_parm("N_Cycles", int),
        "charge": ECC_parm("xctr", int),
        "timebase": ECC_parm("tb", float)
    }

    #==============================================================================#
    # Creating the ecc_parms for LoadTechnique method of api instance of kbio.kbio_api
    #==============================================================================#

    p_voltage_step = make_ecc_parm(api, CP_parms["voltage_step"], ca_param.potential, 0)
    p_step_duration = make_ecc_parm(api, CP_parms["step_duration"], ca_param.duration, 0)
    p_vs_init = make_ecc_parm(api, CP_parms["vs_init"], False, 0)

    # number of steps is one less than len(steps)
    p_nb_steps = make_ecc_parm(api, CP_parms["nb_steps"], 0, 0)

    # record parameters
    p_record_dt = make_ecc_parm(api, CP_parms["record_dt"], ca_param.dt,0)
    p_record_dI = make_ecc_parm(api, CP_parms["record_dI"], ca_param.dI,0)

    # repeating factor
    p_repeat = make_ecc_parm(api, CP_parms["repeat"], 0,0)

    #p_charge = make_ecc_parm(api, CP_parms["charge"], ca_param['charge'])
    #p_timebase = make_ecc_parm(api, CP_parms["timebase"], ca_param['timebase'])

    # make the technique parameter array
    ecc_parms = make_ecc_parms(api, p_voltage_step, p_step_duration, p_vs_init, p_nb_steps, p_record_dt, p_record_dI, p_repeat)

    print('CA technique loaded')
    return tech_file, ecc_parms

