import sys

import kbio.kbio_types as KBIO
from kbio.kbio_tech import ECC_parm
from kbio.kbio_tech import make_ecc_parm
from kbio.kbio_tech import make_ecc_parms

def cv_parm(board_type, api, cv_param):

    #==============================================================================#
    #Each technique has a specific file and they depend on the potentiostat board
    # They all have the same syntax: the technique name + a number '{technique_name}{digit}.ecc'
    #==============================================================================#
    match board_type:

        case KBIO.BOARD_TYPE.ESSENTIAL.value:
            tech_file = f'cv.ecc'
        case KBIO.BOARD_TYPE.PREMIUM.value:
            tech_file = f'cv4.ecc'
        case KBIO.BOARD_TYPE.DIGICORE.value:
            tech_file = f'cv5.ecc'
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
        "scan_rate": ECC_parm("Scan_Rate", float),
        "vs_init": ECC_parm("vs_initial", bool),
        "n_scan": ECC_parm("Scan_number", int),
        "average_dE": ECC_parm("Average_over_dE", bool),
        "record_dE": ECC_parm("Record_every_dE", float),
        "begin_step": ECC_parm('Begin_measuring_I', float),
        "end_step": ECC_parm('End_measuring_I', float),
        "number of cycle": ECC_parm('N_Cycles', int)
    }

    #==============================================================================#
    # Creating the ecc_parms for LoadTechnique method of api instance of kbio.kbio_api
    #==============================================================================#

    p_steps= list()

    p_steps.append(make_ecc_parm(api, CP_parms["voltage_step"], cv_param.ei, 0))
    p_steps.append(make_ecc_parm(api, CP_parms["voltage_step"], cv_param.e1, 1))
    p_steps.append(make_ecc_parm(api, CP_parms["voltage_step"], cv_param.e2, 2))
    p_steps.append(make_ecc_parm(api, CP_parms["voltage_step"], cv_param.ei, 3))
    p_steps.append(make_ecc_parm(api, CP_parms["voltage_step"], cv_param.ef, 4))

    for idx in range(5):
        p_steps.append(make_ecc_parm(api, CP_parms["scan_rate"], cv_param.scanRate, idx))
        p_steps.append(make_ecc_parm(api, CP_parms["vs_init"], False, idx))

    p_scan_number= make_ecc_parm(api, CP_parms["n_scan"], 2, 0)
    p_average_dE= make_ecc_parm(api, CP_parms["average_dE"], True, 0)
    p_record_dE= make_ecc_parm(api, CP_parms["record_dE"], 0.005, 0)
    p_N_cycles= make_ecc_parm(api, CP_parms["number of cycle"], cv_param.cycle, 0)
    p_begin_step= make_ecc_parm(api, CP_parms["begin_step"], 0.5, 0)
    p_end_step= make_ecc_parm(api, CP_parms["end_step"], 1, 0)

    # make the technique parameter array
    ecc_parms = make_ecc_parms(api, *p_steps, p_scan_number, p_average_dE, p_record_dE, p_N_cycles, p_begin_step, p_end_step)

    try:
        return tech_file, ecc_parms

    except:
        print('Issue with ...')
