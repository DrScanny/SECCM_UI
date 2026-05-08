import multiprocessing
import time
import random
from typing import TextIO, Any

"""

This file has no useful code and serve has a draft to test some code
"""

def simPot(tech:str, events:list[Any]):
    randomList= list(range(1,51))
    index=0
    while True:
        index+=1
        # Biologic.runExperiments()
        print(f'Starting approach number {index} using {tech}') 
        time.sleep(1)
        
        while True:
            events[0].clear()
            events[1].set()
            stopTrigger= random.choice(randomList)
            print(f'measured current {stopTrigger}')
            time.sleep(0.5)
            if stopTrigger==3:
                print("Stop Trigger Activated!")
                time.sleep(1)
                events[2].set()
                break

            if events[0].is_set():
                print('Piezo reached limit. Relaxing')
                time.sleep(1)
                break

        if events[2].is_set():
            print('Approach Done!')
            break


def simPiezo(totalTime:int, events:list[Any]):

    while True:
        events[1].wait()
        print('Piezo moving'); time.sleep(1)
        for i in range(totalTime):
            time.sleep(1)

        events[0].set()
        events[1].clear()

        if events[2].is_set():
            print('Stop Piezo')
            break
  
if __name__ == '__main__':


    event_piezoLimit= multiprocessing.Event()
    event_potStarted= multiprocessing.Event()
    event_triggeredStop= multiprocessing.Event()

    events=[event_piezoLimit, event_potStarted, event_triggeredStop]

    process_potentiostat= multiprocessing.Process(target= simPot, args=('ocp', events))
    process_piezo= multiprocessing.Process(target= simPiezo, args=(5, events))
        
    process_potentiostat.start()
    process_piezo.start()

    process_potentiostat.join()
    process_piezo.join()


    print('Done')

    

