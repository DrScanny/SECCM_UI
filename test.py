import time
import sys

def animate_dots(duration_seconds=5):
    start_time = time.time()
    while time.time() - start_time < duration_seconds:
        for i in range(4):
            # \r moves the cursor to the start of the line
            # end='' prevents a new line
            # flush=True ensures the text appears immediately
            print(f"\rLoading{'.' * i}", end='', flush=True)
            time.sleep(0.5)
            # Clear the dots by printing spaces if needed, 
            # though \r usually handles it by overwriting.
            print("\r          ", end='', flush=True) 


def _dots():
    #print(f'Connecting to {deviceName}', end="")

    for i in range(5):
        for i in range(4):
                print(f"\rConnecting {'.' * i}",  end='', flush=True) 
                time.sleep(0.5)

_dots()
print("\rDone!          ")