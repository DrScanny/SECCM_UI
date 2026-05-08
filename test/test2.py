import multiprocessing
import time

def worker_task(stop_event):
    print("Worker process started.")
    # Check the event status at the start of each iteration
    while not stop_event.is_set():
        print("Worker is busy...")
        time.sleep(1)  # Simulate work
    
    print("Event received! Breaking loop and exiting worker.")

if __name__ == "__main__":
    # 1. Create the event
    exit_event = multiprocessing.Event()
    
    # 2. Start the process, passing the event as an argument
    p = multiprocessing.Process(target=worker_task, args=(exit_event,))
    p.start()
    
    # Let the worker run for a few seconds
    time.sleep(3)
    
    # 3. Trigger the break from the main process
    print("Main process: Signaling worker to stop.")
    exit_event.set()
    
    # Wait for the process to finish cleaning up
    p.join()
    print("Main process: Done.")