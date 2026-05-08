from dataclasses import dataclass

@dataclass
class StageSettings():
    moveX: int= 0 #Distance to move olympus stage in X position can take negative values
    moveY: int= 0 #Distance to move olympus stage in Y position can take negative values
    moveZ: int= 0 #Distance to move olympus stage in Z position can take negative values
    posX: int= 0 #Current Absolute position in X can take negative values
    posY: int= 0 #Current Absolute position in Y can take negative values
    posZ: int= 0 #Current Absolute position in Z can take negative values

@dataclass
class MapSettings():
    pattern: str= 'Snake' #Pattern to follow when mapping
    mode: str= 'Hopping' #Mapping mode
    dX: int= 0 #Distance between landings in X always positive
    dY: int= 0 #Distance between landings in Y always positive
    nX: int= 1 #Number of landings in X must be >=1
    nY: int= 1 #Number of landings in Y must be >=1
    
    # dX=0, dY=0, nX=1, nY=1 -> Approach curve at current position
   
@dataclass
class ApproachSettings():
    speed: float= 1 #Approach speed in um
    retract: int= 50 #Tip retraction height after landing in um
    stop: str= 'Potentiostatic' #Technique to use for approach stop
    Eapp: float= 0.1 #Potentiostatic: Potential to apply during approach
    Istop: float=1e-3 #Potentiostatic: Current treshold to stop tip

@dataclass
class CAsettings():
    technique: str= 'CA'
    potential: float= 0.1 #Potential to Apply 
    ref: str= "RE" #vs OCP or Ref
    duration: float= 10 #Experiment duration in seconds
    dt: float= 1 #Record every X second
    dI: float= 1 #Record every X Amp
    iRange: int=12  #Current Range by default AUTO
    eRange: int= 0 #Potential range
    bandwith: int= 8 #Bandwith: controls the response time of feedback loop; Lower -> more stable, Higher -> Faster speed response to change in cell
    header: str= "Time (s), E vs Ref (V), I (A), Cycle"

@dataclass
class CPsettings():
    technique: str= 'CP'
    current: float= 0.000001 #Current to apply in A
    ref: str= "RE" #vs OCP or Ref
    duration: float= 10 #Experiment duration in seconds
    dt: float= 1 #Record every X second
    dE: float= 1 #Record every X V
    iRange: int= 4 #Current Range by default AUTO
    eRange: int= 0 #Potential range
    bandwith: int= 8 #Bandwith: controls the response time of feedback loop; Lower -> more stable, Higher -> Faster speed response to change in cell
    header: str= "Time (s), E vs Ref (V), I (A), Cycle"

@dataclass
class CVsettings():
    technique: str= 'CV'
    scanRate: float= 0.1 #Scan rate in V/s
    ei: float= 0 #Set Initial potential vs OCP
    e1: float= 1 #Set 1st vertex
    e2: float= -1 #Set 2nd vertex
    ef: float= 0 #Set final vertex
    cycle: int= 0 # Number of additional cycles: 0 correspond to 1 measurement
    iRange: int= 12 #Current Range by default AUTO
    eRange: int=0 #Potential range
    bandwith: int =8 #Bandwith: controls the response time of feedback loop; Lower -> more stable, Higher -> Faster speed response to change in cell
    header: str= "Time (s), E vs Ref (V), I (A), Cycle"

@dataclass
class OCPsettings():
    technique: str= 'OCP'
    duration: float= 10 # Duration of OCP measurement in s
    dt: float= 1 # Record potential at each time increment in s
    dE: float= 1 # Record potential at each potential increment in V
    eRange: int= 0   # E range, int corresponds to a potential range
    header: str= "Time (s), E vs Ref (V)"
