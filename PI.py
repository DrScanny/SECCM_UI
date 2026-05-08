from pipython import GCSDevice, datarectools, pitools
import SECCM_Settings
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
class Positioner:

    def __init__(self, serialnum):

        self.PIdevice= GCSDevice()  # Create PI device object
        self.PIdevice.ConnectUSB(serialnum=serialnum) # Connect through USB
        self.deviceID= self.PIdevice.qIDN().strip() # Print controller information
        print(self.deviceID)
        self.servo= None #Servo Info
        self.axes= len(self.PIdevice.axes) # Get the number of axis

    
    def servo_on(self, axesServo:dict[str,bool]|None= None):
        #The argument must be written as {'AXIS_1': True or False, 'AXIS_2': True or False, ...}
        if axesServo:
            if len(axesServo)<=self.axes:
                self.PIdevice.SVO(axesServo)

            raise Exception(f'Number of axis must be less than {self.axes}')

        else:
            self.PIdevice.SVO(self.axes, True)
        print(self.PIdevice.qSVO(self.axes))


    def reference_axes(self, axesRef:list[str]|None =None):
        #The argument is a list ['AXIS_1', 'AXIS_2', ...]
        if axesRef:
            if len(axesRef)<=self.axes:
                self.PIdevice.FRF(axesRef)

            raise Exception(f'Number of axis must be less than {self.axes}')
        else:
            self.PIdevice.FRF()

        # Wait until referencing complete
        while not all(self.PIdevice.qFRF(self.axes).values()):
            time.sleep(0.1)

    def initialize_stage(self):

        self.servo_on()
        self.reference_axes()

    def wait_until_done(self):
        while any(self.PIdevice.IsMoving().values()):
            time.sleep(0.001)

    def set_motion_parameters(self, velocity=1, acceleration=1, deceleration=1):

        # Set velocity
        self.PIdevice.VEL(self.axes, velocity)
        # Set acceleration
        self.PIdevice.ACC(self.axes, acceleration)
        # Set deceleration
        self.PIdevice.DEC(self.axes, deceleration)

    def moveABS(self, coord:dict[str,float]|None= None):
        #Argument is a dict {'AXIS_1':1.5, 'AXIS_2':10.9}
        if coord:
            if len(coord)<=self.axes:
                self.PIdevice.MOV(coord)
                self.wait_until_done()

            raise Exception(f'Number of axis must be less than {self.axes}')

    def moveREL(self, displacement:dict[str,float]|None= None):
        #Argument is a dict {'AXIS_1':1.5, 'AXIS_2':10.9}
        if displacement:
            if len(displacement)<=self.axes:
                self.PIdevice.MVR(displacement)
                self.wait_until_done()

            raise Exception(f'Number of axis must be less than {self.axes}')

    def get_position(self):

        positions= self.PIdevice.qPOS()

        return positions

    def get_travel_limits(self):

        minimum= self.PIdevice.qTMN()
        maximum= self.PIdevice.qTMX()

        return minimum, maximum

    def stop(self):
        self.PIdevice.STP()

    def close(self):
        self.PIdevice.CloseConnection()

if __name__ == "__main__":

    SERIAL = "0125076674"

    # Create stage object
    XYstage = Positioner(SERIAL)

    # Turn servo on and reference axes
    XYstage.initialize_stage()

    # Print current position
    print("Current position:")
    print(XYstage.get_position())

    # Print travel limits
    print("Travel limits:")
    print(XYstage.get_travel_limits())

    # Set motion parameters
    XYstage.set_motion_parameters()

    # Relative move
    XYstage.moveABS({'AXIS_1':1.5, 'AXIS_2':10.9})

    print("New position:")
    print(XYstage.get_position())

    # Absolute move
    XYstage.moveREL({'AXIS_1':1.5, 'AXIS_2':10.9})

    print("New position:")
    print(XYstage.get_position())

    # Close connection
    XYstage.close()


