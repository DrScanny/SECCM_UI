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
    pattern: int= 0 #Pattern to follow when mapping: 0-> Snake, 1-> Parallel
    mode: int= 0 #Mapping mode: 0-> None, 1-> SECCM, 2-> SECM
    dX: int= 0 #Distance between landings in X always positive
    dY: int= 0 #Distance between landings in Y always positive
    nX: int= 1 #Number of landings in X must be >=1
    nY: int= 1 #Number of landings in Y must be >=1
    map: list[list[int]]= field(default_factory=list) #Coordinates for mapping
    
    # dX=0, dY=0, nX=1, nY=1 -> Approach curve at current position
   
@dataclass
class SECCM():
    speed: float= 1 #Approach speed in um
    retract: float= 50 #Tip retraction height after landing in um
    stop: int= 0 #Technique to use for approach stop: 0->OCP, 1-> DC Potentiostatic, 2-> AC 
    Eapp: float= 0.1 #Potentiostatic: Potential to apply during approach
    Istop: float=1e-3 #Potentiostatic: Current treshold to stop tip
    iRange: int= 0 #Current Range by default AUTO
    #techList: list[echemSettings]= field(default_factory=list)

@dataclass
class SECM():
    speed: float= 1 #Approach speed in um
    retract: float= 50 #Tip retraction height after landing in um
    experiment: int= 0 #SECM technique 0->approach curve, 1-> constant distance map
    Eapp: float= 0.1 #Potentiostatic: Potential to apply during approach
    stop:int=0
    limPos: float=200 #Potentiostatic: Current treshold for negative feedback
    limNeg: float=50 #Potentiostatic: Current treshold for positive feedback
    iRange: int= 1 #Current Range by default AUTO

@dataclass
class echemSettings():
    technique: str= 'CP'
    potential: float= 0.1 #Voltage in V
    current: float= 0.000001 #Current to apply in A
    ref: str= "RE" #vs OCP or Ref
    duration: float= 10 #Experiment duration in seconds
    dt: float= 1 #Record every X second
    dE: float= 1 #Record every X V
    dI: float= 1e-3 #record every mA
    scanRate: float= 0.1 #Scan rate in V/s
    ei: float= 0 #Set Initial potential vs OCP
    e1: float= 1 #Set 1st vertex
    e2: float= -1 #Set 2nd vertex
    ef: float= 0 #Set final vertex
    cycle: int=0 #Number of cycle
    iRange: int= 12 #Current Range by default AUTO
    eRange: int= 0 #Potential range
    bandwith: int= 8 #Bandwith: controls the response time of feedback loop; Lower -> more stable, Higher -> Faster speed response to change in cell
    header: str= "Time (s), E vs Ref (V), I (A), Cycle"

@dataclass
class echemData():
    name: str = ""
    technique: str = ""
    index: int = 0
    t: list[float] = field(default_factory=list)
    Ewe: list[float] = field(default_factory=list)
    Iwe: list[float] = field(default_factory=list)
    cycle: list[int] = field(default_factory=list)
