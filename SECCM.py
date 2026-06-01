import os
import sys
import numpy as np
import time
import multiprocessing

from pipython import GCSDevice, datarectools, pitools
from typing import TextIO, Any
from BiologicAPI.Biologic import Biologic
from BiologicAPI.kbio.kbio_tech import get_experiment_data
from BiologicAPI.kbio.kbio_tech import get_info_data
from BiologicAPI.kbio.utils import exception_brief

import UI_Settings

def _stopTip(potentiostatOutput, SECCMsettings: UI_Settings.SECCM)-> bool:
    match SECCMsettings.stop:
        case 0:
            if abs(potentiostatOutput['Ewe'])<=1.5:
                print('Tip stop OCP')
                return True
            else:
                return False
                
        case 1:
            if abs(potentiostatOutput['Iwe'])>SECCMsettings.Istop:
                print('Tip stop Potentiostatic')
                return True
            else:
                return False
        
        case 2:
            print('Not implemented yet')
            return False
        
        case _:
            return False
        
def approachPotentiostat(potentiostat: Biologic, approachTechnique, SECCMsettings, event):

    while True: #Primary While loop -> Continue measurement until trigger or max range hit

        # Measurements are reset each time the piezo hits the limit
        event['reset'].wait() #Wait until all stages have been reset, before starting potentiostat measurement
        print("Starting new approach")
        potentiostat.load_technique(approachTechnique) 
        potentiostat.start_channel()

        event['limit'].clear() #Clear the piezo limit reached event flag
        event['reset'].clear() #Clear the piezo reset done event flag
        event['start'].set() #Set the 'start' event flag. Signal that the echem measurement has started and stages can move at the same time

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
            
                if _stopTip(output, SECCMsettings): # Function that determine if the tip should be stopped based on the stop criteria
                    event['stop'].set() # Set the 'stop' event flag. Signal the end of approach curve: Stop all activity!
                    potentiostat.status= "STOP"
                    break

            # Stop the measurement once the piezo limit is reached
            if event['limit'].is_set():
                print('Piezo reached limit. Relaxing')
                break
            
            if potentiostat.status == "STOP":
                break

def approachPositioner(piezo: GCSDevice, Zstage: GCSDevice, SECCMsettings: UI_Settings.SECCM, event):
    counter=1

    while True:

        event['start'].wait() #Wait until potentiostat has started
        print(f"Piezo descent number: {counter}")
        time.sleep(0.5)
 
        piezo.VEL('3', SECCMsettings.speed)
        piezo.MOV('3', 0) # Move piezo down

        while any(piezo.gcscommands.IsMoving().values()):
            if event['stop'].is_set():
                piezo.gcscommands.STP(noraise=True)
                print('Piezo has been stopped')
                break
        
        if event['stop'].is_set():
            break

        counter+=1
        print("Piezo limit reached")
        event['limit'].set() #Flag set to signal piezo has reached limit, so the potentiostat can stop while positioners reset

        

        # Zstage moved by 60 um, approach has advanced by 60 um
        Zstage.MOV(-0.06) 

        # Resetting piezo
        piezo.VEL('3', 10) 
        piezo.MOV('3', 60) 

        # Waiting for positioner reset to be done
        while not all(list(piezo.qONT().values())):
            time.sleep(0.1)

        while not all(list(Zstage.qONT(1).values())):
            time.sleep(0.1)

        print("Stages have been reset")
        event['start'].clear() #Reset the potentiostat status indicator
        event['reset'].set() #Indicate that the stages position have been reset and ready for another approach 
    
def approachSECCM(potentiostat: Biologic, piezo: GCSDevice, Zstage: GCSDevice, SECCMsettings: UI_Settings.SECCM):

    #Initialize piezo by setting speed to 10 um/s and moving to starting position by raising 60um in the Z-axis
    if piezo.gcscommands.IsConnected(): 
        piezo.VEL('3', 10)
        piezo.MOV('3', 60)
    
    else:
        print('Piezo not connected, aborting procedure')
        return False
      
    #During Approach the Zstage speed is significantly reduced to 10 um/sec
    if Zstage.gcscommands.IsConnected(): #Initialize Zstage 
        Zstage.VEL(1, 0.01)

    else:
        print('Zstage not connected, aborting procedure')
        return False
    
    #Creating the Events necessary for the approach curve
    event_limit= multiprocessing.Event() #Signal that the piezo has reached the limit
    event_reset= multiprocessing.Event() #Signal that the piezo reset is done
    event_start= multiprocessing.Event() #Signal that the potentiostat has started a measurement for the approach
    event_stop= multiprocessing.Event() #Signal that the tip stop has been triggered

    event= {'limit': event_limit, 'start': event_start, 'stop': event_stop, 'reset': event_reset}

    technique= UI_Settings.OCP('OCP', 600, 2e-4, 1, 0)

    #Implementing the stop technique (OCP, CA, AC) based on user selection
    match SECCMsettings.stop:

        case 0: #Open Circuit Potential
            technique= UI_Settings.OCP('OCP', 600, 2e-4, 1, 0)

        case 1: #Potentiostatic
            technique= UI_Settings.CA('CA', potential= SECCMsettings.Eapp, dt= 2e-4, duration= 600)

        case 2: # AC not implemented yet
            pass

    #Waiting for piezo to be done moving
    while not all(list(piezo.qONT().values())):
        time.sleep(0.1)

    #Once ready set the 'reset' event so that the potentiostat can be started
    event['reset'].set() #

    #Both processes are created and then launched
    process_potentiostat= multiprocessing.Process(target= approachPotentiostat, args=(potentiostat, technique, SECCMsettings, event))
    process_piezo= multiprocessing.Process(target= approachPositioner, args=(piezo, Zstage, SECCMsettings, event ))

    process_potentiostat.start()
    process_piezo.start()

    process_potentiostat.join()
    process_piezo.join()

    print('Approach done')

if __name__ == '__main__':
    print('Package for SECCM approach, Does nothing')