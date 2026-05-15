import multiprocessing
import time

"""

This file has no useful code and serve has a draft to test some code
"""

def simPot(tech:str, start, eventTrigger, eventLimit):
    print(f'Starting approach using {tech}')

    index=0
    while not eventLimit.is_set():
        index+=1
        time.sleep(0.001)

        if index>500:
            start.value = time.perf_counter_ns()
            eventTrigger.set()

    print(f'Stopped Measurement at {index}')


def simPiezo(totalTime:int, end, eventTrigger, eventLimit):
    print('Piezo moving')

    for i in range(totalTime):
        time.sleep(0.001)
        if eventTrigger.is_set():
            end.value = time.perf_counter_ns()
            print("Stop triggered")
            break

    eventLimit.set()
    print('Piezo reached limit. Relaxing')
    
  
if __name__ == '__main__':

    start= multiprocessing.Value('d', 0)
    end= multiprocessing.Value('d', 0)

    event_piezoLimit= multiprocessing.Event()
    event_triggeredStop= multiprocessing.Event()

    process_potentiostat= multiprocessing.Process(target= simPot, args=('ocp', start, event_triggeredStop, event_piezoLimit))
    process_piezo= multiprocessing.Process(target= simPiezo, args=(1000, end, event_triggeredStop, event_piezoLimit))

    process_potentiostat.start()
    process_piezo.start()

    process_potentiostat.join()
    process_piezo.join()

    print(f"Elapsed: {end.value - start.value} nanoseconds")
    print('Done')

    

