from pipython import GCSDevice, datarectools, pitools
import SECCM_Settings


"""
Collection of function to control the PI controllers and stage

General Information

    U-781/C867 (Olympus)
    {
        Instance name: self.olympus
        Serial Number: 
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

Template for function
    Assume the controller/stage will already be instantiated (See name above)
    To make the function as general and reusable as possible arguments will be required instead of referenced directly as a class method
        1- Controller (Mandatory): The stage/controller instance
        2- Other variables (speed, coordinates): instance of dataclass like self.mapping.stageSettings, self.mapping.mapSettings, self.mapping.approachSettings


    every function name should start with PI_...
    def PI_function(controller: PIdevice, settings):
        try:
            Whatever your function is supposed to do
            print('Feedback message of success')
        except:
            print('Feedback message of failure (specify file and function)') 

"""

# Instance of settings
stageSettings= SECCM_Settings.StageSettings()
mapSettings= SECCM_Settings.MapSettings()
approachSettings= SECCM_Settings.ApproachSettings()


# Instance of positionner
ncube= GCSDevice()
mercury= GCSDevice()
olympus= GCSDevice()

# General code to connect to device. 
def connect(PIdevice:GCSDevice, serial:str):
    try: 
        PIdevice.ConnectUSB(serial)
        print (f'connected: {ncube.qIDN().strip()}')
        return ncube.qIDN().strip()
    except:
        print('Failed to connect to PI device: PI -> PI_connect()') 


def initZ(PIdevice:GCSDevice, ref:str, servo: bool, vel:float= 1, accel: float | None = None, decel: float | None= None):
    """
        'FRF': References the stage using the reference position.
        'FNL': References the stage using the negative limit switch.
        'FPL': References the stage using the positive limit switch.
        'POS': Sets the current position of the stage to 0.0.
        'ATZ': Runs an auto zero procedure.
    """
    try:
        connect(PIdevice, '0026550002')
        pitools.DeviceStartup(PIdevice, stage=None, refmodes= ref, servostates= servo, controlmodes= None)
        PIdevice.VEL('1', vel)

        if accel:
            pass
        if decel:
            pass

        print('Initialized device successfully')
        return True
    
    except:
        print('Failed to initialize the device')
        return False
    
def initXY(PIdevice:GCSDevice, ref:str, servo: bool, vel:float= 1, accel: float | None = None, decel: float | None= None):
    """
        'FRF': References the stage using the reference position.
        'FNL': References the stage using the negative limit switch.
        'FPL': References the stage using the positive limit switch.
        'POS': Sets the current position of the stage to 0.0.
        'ATZ': Runs an auto zero procedure.
    """
    try:
        connect(PIdevice, '0026550002')
        pitools.DeviceStartup(PIdevice, stage=None, refmodes= ref, servostates= servo, controlmodes= None)
        PIdevice.VEL('1', vel)

        if accel:
            pass
        if decel:
            pass

        print('Initialized device successfully')
        return True
    
    except:
        print('Failed to initialize the device')
        return False

    
# Example of code to move piezo
def piezoMove(PIdevice:GCSDevice, settings: SECCM_Settings.ApproachSettings, axis:str= '3')-> None:
    try:
        device= {PIdevice.qIDN()}
        servoState= PIdevice.qSVO(axis) #Query the specific axis servo state: Servo Off-> open-loop, Servo On-> closed loop
        if not servoState: #If servo is not On, then turn them on
            PIdevice.SVO(axis, 1)
        velocity= PIdevice.VEL(axis, 1) #Set PIdevice velocity in closed-loop to 1 um/s (Unit of speed for each device is different by default)
        PIdevice.MOV(axis, 10)

        print(f'Moved {device} to {PIdevice.qMOV(axis)} at velocity of {velocity} \u03bcm/s')
    
    except:
        # Return error message, still need to intercept the error message from PI packages and incorporate into our own message
        print(f'Failed to move {PIdevice.qIDN()} to {PIdevice.qMOV(axis)}')
    

if __name__ == '__main__':
    # from pipython import PILogger, DEBUG, INFO, WARNING, ERROR, CRITICAL
    # PILogger.setLevel(DEBUG)

    ncube= GCSDevice()
    connect(ncube,'0125021719')
    
  