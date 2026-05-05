""" Bio-Logic OEM package python API.

This module contains support functions when building technique parameters,
and decoding experiment records.

"""

from dataclasses import dataclass

import kbio.kbio_types as KBIO
from kbio.tech_types import TECH_ID


@dataclass
class ECC_parm:
    """ECC param template"""

    label: str
    type_: type


#####################################################################
# This document is a part of the BioLogic OEM Package and is
# protected by the terms of the OEM Package licence as well as
# other intellectual property rights owned by BioLogic SAS.
# This document may only be used for non-commercial purposes
# such as for the integration of BioLogic equipment to larger
# technical solutions manufactured  and/or delivered to end-users.
#####################################################################
"""
functions to build the technique ECC parameters (structure+contents)
"""


def make_ecc_parm(api, ecc_parm, value=0, index=0):
    """Given an ECC_parm template, create and return an EccParam, with its value and optional index."""
    parm = KBIO.EccParam()
    # BL_Define<xxx>Parameter
    # .. value is converted to its proper type, which DefineParameter will use
    api.DefineParameter(ecc_parm.label, ecc_parm.type_(value), index, parm)
    return parm


def make_ecc_parms(api, *ecc_parm_list):
    """Create an EccParam array from an EccParam list, and return an EccParams refering to it."""
    nb_parms = len(ecc_parm_list)
    parms_array = KBIO.ECC_PARM_ARRAY(nb_parms)

    for i, parm in enumerate(ecc_parm_list):
        parms_array[i] = parm

    parms = KBIO.EccParams(nb_parms, parms_array)
    return parms


# function to handle records from a running experiment
def get_info_data(api, data, print=False):
    """Unpack the info data, decode it according to the technique, display it,
    then return the experiment status"""

    current_values, data_info, _ = data

    status = KBIO.PROG_STATE(current_values.State).name
    tech_name = TECH_ID(data_info.TechniqueID).name

    if print:
        # synthetic info for current record
        info = {
            "tb": current_values.TimeBase,
            "ix": data_info.TechniqueIndex,
            "tech": tech_name,
            "proc": data_info.ProcessIndex,
            "loop": data_info.loop,
            "skip": data_info.IRQskipped,
        }
        print("> data info :")
        print(info)
    return status, tech_name


def get_experiment_data(api, data, tech_name, board_type):
    """Unpack the experiment data, decode it according to the technique, display it,
    then return the experiment status"""

    current_values, data_info, data_record = data

    ix = 0

    for _ in range(data_info.NbRows):

        inx = ix + data_info.NbCols
        row = data_record[ix:inx]
        t_high, t_low, *row = data_record[ix:inx]

        t_rel= (t_high << 32) + t_low
        t= current_values.TimeBase * t_rel

        if tech_name == "OCV":

            # Ewe is a float
            Ewe= api.ConvertChannelNumericIntoSingle(row[0], board_type)

            parsed_row = {"t": t, "Ewe": Ewe}

        elif tech_name == "CP" or tech_name == 'CA':

            # Ewe is a float
            Ewe= api.ConvertChannelNumericIntoSingle(row[0], board_type)

            # current is a float
            Iwe= api.ConvertChannelNumericIntoSingle(row[1], board_type)

            # technique cycle is an integer
            cycle= row[2]

            parsed_row= {"t": t, "Ewe": Ewe, "Iwe": Iwe, "cycle": cycle}

        elif tech_name == "CV":
            print(tech_name)

            Ewe= api.ConvertChannelNumericIntoSingle(row[1], board_type)

            # current is a float
            Iwe= api.ConvertChannelNumericIntoSingle(row[0], board_type)

            # technique cycle is an integer
            cycle = row[2]

            parsed_row= {"t": t, "Ewe": Ewe, "Iwe": Iwe, "cycle": cycle}

        else:
            # besides the previous 2 known techniques, this is provided
            # to show a raw dump of the record

            parsed_row = [f"0x{word:08X}" for word in row]

        yield parsed_row

        ix = inx
