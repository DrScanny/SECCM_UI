from dataclasses import dataclass, field

@dataclass
class Move():
    moveX: float= 0.0 #Distance to move olympus stage in X position -65-65
    moveY: float= 0.0 #Distance to move olympus stage in Y position -65-65
    moveZ: float= 0.0 #Distance to move mercury stage in Z position 0-25
    XYspeed: float= 5.0 #Speed for XY stage
    Zspeed: float= 1.0 #Speed for Zstage

@dataclass
class Mapping():
    pattern: str= 'Snake' #Pattern to follow when mapping
    mode: int= 0 #Mapping mode: 0-> None, 1-> SECCM, 2-> SECM
    dX: int= 0 #Distance between landings in X always positive
    dY: int= 0 #Distance between landings in Y always positive
    nX: int= 1 #Number of landings in X must be >=1
    nY: int= 1 #Number of landings in Y must be >=1
    
    # dX=0, dY=0, nX=1, nY=1 -> Approach curve at current position
   
@dataclass
class SECCM():
    speed: float= 1 #Approach speed in um
    retract: float= 50 #Tip retraction height after landing in um
    stop: int= 0 #Technique to use for approach stop: 0->OCP, 1-> DC Potentiostatic, 2-> AC 
    Eapp: float= 0.1 #Potentiostatic: Potential to apply during approach
    Istop: float=1e-3 #Potentiostatic: Current treshold to stop tip

@dataclass
class SECM():
    speed: float= 1 #Approach speed in um

@dataclass
class CA():
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
class CP():
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
class CV():
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
class OCP():
    technique: str= 'OCP'
    duration: float= 10 # Duration of OCP measurement in s
    dt: float= 1 # Record potential at each time increment in s
    dE: float= 1 # Record potential at each potential increment in V
    eRange: int= 0   # E range, int corresponds to a potential range
    header: str= "Time (s), E vs Ref (V)"

@dataclass
class echemData():
    name: str = ""
    technique: str = ""
    index: int = 0
    t: list[float] = field(default_factory=list)
    Ewe: list[float] = field(default_factory=list)
    Iwe: list[float] = field(default_factory=list)
    cycle: list[int] = field(default_factory=list)
