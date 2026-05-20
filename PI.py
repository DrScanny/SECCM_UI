from pipython import GCSDevice, datarectools, pitools
import UI_Settings
import time

"""
Collection of function to control the PI controllers and stage

General Information

    U-781/C867 (Olympus)
    {
        Instance name: self.olympus
        Serial Number: 0125076674
        Axis: [X:1, Y:2]
        Default Distance unit: mm (to be confirmed)
        
    }

    M-112/C863 (Mercury)
    {
        Instance name: self.mercury
        Serial Number: 0026550002
        Axis: [1]
        Default Distance unit: mm (to be confirmed)
        
    }

    P-611/E727 (Nanocube) 
    {
        Instance name: self.nanocube
        Serial Number: 0125021719
        Axis: [X:1, Y:2, Z:3]
        Default Distance unit: um
        
    }

"""
def connect(PIdevice, serialnum):
    PIdevice.ConnectUSB(serialnum=serialnum) # Connect through USB
    print(PIdevice.deviceID.strip() )





if __name__ == "__main__":

    SERIAL = "0125076674"



