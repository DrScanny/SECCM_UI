import os
import sys
import numpy as np
import time
import multiprocessing

from pipython import GCSDevice, datarectools, pitools
from typing import TextIO, Any
from Biologic import Biologic
from kbio.kbio_tech import get_experiment_data
from kbio.kbio_tech import get_info_data
from kbio.utils import exception_brief

import UI_Settings

def _stopTip(potentiostatOutput, approachSettings: UI_Settings.SECCM)-> bool:
    match approachSettings.stop:
        case 'Open Circuit Potential':
            if abs(potentiostatOutput['Ewe'])<=1.5:
                print('Tip stop OCP')
                return True
            else:
                return False
                
        case 'Potentiostatic':
            if abs(potentiostatOutput['Iwe'])>UI_Settings.SECCM.Istop:
                print('Tip stop Potentiostatic')
                return True
            else:
                return False
        
        case 'Alternating Current':
            print('Not implemented yet')
            return False
        
        case _:
            return False
        
def approachPotentiostat(potentiostat: Biologic, approachTechnique, approachSettings, event):

    while not event['stop'].is_set(): #Primary While loop -> Continue measurement until trigger or max range hit

        # Measurements are reset each time the piezo hits the limit
        event['reset'].wait() #Wait until all stages have been reset, before starting potentiostat measurement
        print("Starting new approach")
        potentiostat.load_technique(approachTechnique) 
        potentiostat.start_channel()

        event['limit'].clear() #Clear the piezo limit reached event flag
        event['reset'].clear() #Clear the piezo reset done event flag
        event['start'].set() #Set the 'start' event flag. Signal that the echem measurement has started and sategs can move at the same time

        """
            Secondary loop -> Runs the technique and acquire data. Once the loops is broken, the technique measurement is considered done
            The loop can be broken in 2 ways
                1- Each time the piezo reaches the limit (60 um). Signaled by the event['piezo']
                2- Once the tip stop has been triggered, the whole approach is stopped. Signaled by event['stop']
        """
        while True: 

            potentiostat.data= potentiostat.api.GetData(potentiostat.id_, potentiostat.channel)
            potentiostat.status, potentiostat.tech_name= get_info_data(potentiostat.api, potentiostat.data) 
        
            for output in get_experiment_data(potentiostat.api, potentiostat.data, potentiostat.tech_name, potentiostat.board_type):
            
                if _stopTip(output, approachSettings): # Function that determine if the tip should be stopped based on the stop criteria
                    print('tip soppage')
                    potentiostat.status= "STOP"
                    event['stop'].set() # Set the 'stop' event flag. Signal the end of approach curve: Stop all activity!
                    break

            # Stop the measurement once the piezo limit is reached
            if event['limit'].is_set():
                print('Piezo reached limit. Relaxing')
                break
            
            if potentiostat.status == "STOP":
                break

        
def approachPositioner(piezo: GCSDevice, Zstage: GCSDevice, approachSettings: UI_Settings.SECCM, event):

    while not event['stop'].is_set():

        event['start'].wait() #Wait until potentiostat has started
        print("Started piezo movement")
        time.sleep(0.5)
 
        piezo.VEL('3', approachSettings.speed)
        piezo.MOV('3', 0) # Move piezo down

        while any(piezo.IsMoving().values()):
            if event['stop'].is_set():
                piezo.HLT()
                print('Piezo has been stopped')
                break
        
        print("Piezo limit reached")
        event['limit'].set() #Flag set to signal piezo has reached limit, so the potentiostat can stop while positioners reset

        if event['stop'].is_set():
            break

        # Zstage moved by 60 um, approach has advanced by 60 um
        Zstage.MOV(-0.06) 
        pitools.waitontarget(Zstage, timeout=900) 

        # Resetting piezo
        piezo.VEL('3', 10) 
        piezo.MOV('3', 60) 
        pitools.waitontarget(piezo, timeout=900) 

        print("Stages have been reset")
        event['start'].clear() #Reset the potentiostat status indicator
        event['reset'].set() #Indicate that the stages position have been reset and ready for another approach 
    
    piezo.HLT()

def approachSECCM(potentiostat: Biologic, piezo: GCSDevice, Zstage: GCSDevice, approachSettings: UI_Settings.SECCM):

    event_limit= multiprocessing.Event() #Signal that the piezo has reached the limit
    event_reset= multiprocessing.Event() #Signal that the piezo has reached the limit
    event_start= multiprocessing.Event() #Signal that the potentiostat has started a measurement for the approach
    event_stop= multiprocessing.Event() #Signal that the tip stop ha sbeen triggered

    event= {'limit': event_limit, 'start': event_start, 'stop': event_stop, 'reset': event_reset}

    if piezo.connected(): #Initialize piezo 
        piezo.VEL('3', 10)
        piezo.MOV('3', 60)

    if Zstage.connected(): #Initialize Zstage 
        Zstage.VEL(1, 0.01)

    process_potentiostat= multiprocessing.Process(target= approachPotentiostat, args=(potentiostat, UI_Settings.SECCM, event))
    process_piezo= multiprocessing.Process(target= approachPositioner, args=(piezo, Zstage, UI_Settings.SECCM, event ))

    process_potentiostat.start()
    process_piezo.start()

    process_potentiostat.join()
    process_piezo.join()

    print('Approach done')


if __name__ == '__main__':
    print('Package for SECCM approach, Does nothing')