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
class Positioner:

    def __init__(self):

        self.PI= GCSDevice()  # Create PI device object
        self.deviceID= None # Print controller information
        self.servo= None #Servo Info
        self.axes= self.PI.axes # Get the number of axis
        self.nAxes= len(self.axes)

    def connect(self, serialnum):
        self.PI.ConnectUSB(serialnum=serialnum) # Connect through USB
        self.deviceID= self.PI.qIDN().strip() 
        print(self.deviceID)

    
    def servo_on(self, axesServo:dict[str,bool]|None= None):
        #The argument must be written as {'AXIS_1': True or False, 'AXIS_2': True or False, ...}
        if axesServo:
            if len(axesServo)<=self.nAxes:
                self.PI.SVO(axesServo)

            raise Exception(f'Number of axis must be less than {self.axes}')

        else:
            self.PI.SVO(self.axes, True)
        print(self.PI.qSVO(self.axes))


    def reference_axes(self, axesRef:list[str]|None =None):
        #The argument is a list ['AXIS_1', 'AXIS_2', ...]
        if axesRef:
            if len(axesRef)<=self.nAxes:
                self.PI.FRF(axesRef)

            raise Exception(f'Number of axis must be less than {self.axes}')
        else:
            self.PI.FRF()

        # Wait until referencing complete
        while not all(self.PI.qFRF(self.axes).values()):
            time.sleep(0.1)

    def initialize_stage(self):

        self.servo_on()
        self.reference_axes()

    def wait_until_done(self):
        while any(self.PI.IsMoving().values()):
            time.sleep(0.001)

    def set_motion_parameters(self, velocity=1, acceleration=1, deceleration=1):

        # Set velocity
        self.PI.VEL(self.axes, velocity)
        # Set acceleration
        self.PI.ACC(self.axes, acceleration)
        # Set deceleration
        self.PI.DEC(self.axes, deceleration)

    def moveABS(self, coord:dict[str,float]|None= None):
        #Argument is a dict {'AXIS_1':1.5, 'AXIS_2':10.9}
        if coord:
            if len(coord)<=self.nAxes:
                self.PI.MOV(coord)
                self.wait_until_done()

            raise Exception(f'Number of axis must be less than {self.axes}')

    def moveREL(self, displacement:dict[str,float]|None= None):
        #Argument is a dict {'AXIS_1':1.5, 'AXIS_2':10.9}
        if displacement:
            if len(displacement)<=self.nAxes:
                self.PI.MVR(displacement)
                self.wait_until_done()

            raise Exception(f'Number of axis must be less than {self.axes}')

    def get_position(self):

        positions= self.PI.qPOS()

        return positions

    def get_travel_limits(self):

        minimum= self.PI.qTMN()
        maximum= self.PI.qTMX()

        return minimum, maximum

    def stop(self):
        self.PI.STP()

    def close(self):
        self.PI.CloseConnection()

if __name__ == "__main__":

    SERIAL = "0125076674"

    # Create stage object
    XYstage= Positioner()

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


