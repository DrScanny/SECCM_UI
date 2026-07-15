class FileWrite():
    def __init__(self):
        super().__init__()
        #placeholder
        self.flushcounter = 1
    
    def writeEchemSettings(self, Settings, file):
        file.write("SECCM Settings\n")
        settingCount = 1
        for name, value in Settings.__dict__.items():
            if settingCount == 1:
                file.write("Technique,")
                file.write(str(value))
            elif settingCount == 2:
                file.write("Potential,")
                file.write(f"{value},V")
            elif settingCount == 3:
                file.write("Current,")
                file.write(f"{value},A")
            elif settingCount == 4:
                file.write("Ref,")
                file.write(f"{value}")
            elif settingCount == 5:
                file.write("Duration,")
                file.write(f"{value},s")
            elif settingCount == 6:
                file.write("dt,")
                file.write(f"{value},s")
            elif settingCount == 7:
                file.write("dE,")
                file.write(f"{value},V")
            elif settingCount == 8:
                file.write("dI,")
                file.write(f"{value},mA")
            elif settingCount == 9:
                file.write("scanRate,")
                file.write(f"{value},V/s")
            elif settingCount == 10:
                file.write("ei,")
                file.write(f"{value},V")
            elif settingCount == 11:
                file.write("e1,")
                file.write(f"{value},V")
            elif settingCount == 12:
                file.write("e2,")
                file.write(f"{value},V")
            elif settingCount == 13:
                file.write("ef,")
                file.write(f"{value},V")
            elif settingCount == 14:
                file.write("cycle,")
                file.write(str(value))
            elif settingCount == 15:
                file.write("iRange,")
                file.write(f"{value},A?")
            elif settingCount == 16:
                file.write("eRange,")
                file.write(f"{value},V")
            elif settingCount == 17:
                file.write("bandwidth,")
                file.write(str(value))
                file.write("\n")
            elif settingCount == 18:
                #write header
                file.write(str(value))
            file.write("\n")
            settingCount += 1

        file.flush()
    
    """
    1technique: str= 'CP'
    2potential: float= 0.1 #Voltage in V
    3current: float= 0.000001 #Current to apply in A
    4ref: str= "RE" #vs OCP or Ref
    5duration: float= 10 #Experiment duration in seconds
    6dt: float= 1 #Record every X second
    7dE: float= 1 #Record every X V
    8dI: float= 1e-3 #record every mA
    9scanRate: float= 0.1 #Scan rate in V/s
    10ei: float= 0 #Set Initial potential vs OCP
    11e1: float= 1 #Set 1st vertex
    12e2: float= -1 #Set 2nd vertex
    13ef: float= 0 #Set final vertex
    14cycle: int=0 #Number of cycle
    15iRange: int= 12 #Current Range by default AUTO
    16eRange: int= 0 #Potential range
    17bandwith: int= 8 #Bandwith: controls the response time of feedback loop; Lower -> more stable, Higher -> Faster speed response to change in cell
    18header: str= "Time (s), E vs Ref (V), I (A), Cycle"
    """

    def writeData(self, dataString, file):
        file.write(dataString)
        file.write("\n")
        self.flushcounter += 1

        #flush every 20 datapoints, might have to increase if there is lag
        if self.flushcounter % 20 == 0:
            file.flush()
    
    def writeSECCMSettings(self, settings, file):
        file.write("SECCM Settings\n")
        settingCount = 1
        for name, value in settings.__dict__.items():
            if settingCount == 1:
                file.write("Approach speed,")
                file.write(f"{value},μm/s")
            elif settingCount == 2:
                file.write("Retract height,")
                file.write(f"{value},μm")
            elif settingCount == 3:
                file.write("Stop technique ID,")
                file.write(f"{value}")
            elif settingCount == 4:
                file.write("E approach,")
                file.write(f"{value}, V")
            elif settingCount == 5:
                file.write("I stop,")
                file.write(f"{value}, A")
                file.write("\n")
            file.write("\n")
            settingCount += 1

        file.flush()

    def writeSECMSettings(self, settings, file):
        file.write("SECM Settings\n")
        settingCount = 1
        for name, value in settings.__dict__.items():
            if settingCount == 1:
                file.write("Approach speed,")
                file.write(f"{value},μm/s")
            elif settingCount == 2:
                file.write("Retract height,")
                file.write(f"{value},μm")
            elif settingCount == 3:
                file.write("Experiment ID,")
                file.write(f"{value}")
            elif settingCount == 4:
                file.write("E approach,")
                file.write(f"{value}, V")
            elif settingCount == 5:
                file.write("Stop,")
                file.write(f"{value}")
            elif settingCount == 6:
                file.write("Positive limit,")
                file.write(f"{value}, A")
            elif settingCount == 7:
                file.write("Negative limit,")
                file.write(f"{value}, A")
            elif settingCount == 8:
                file.write("iRange,")
                file.write(f"{value}, A")
                file.write("\n")
            file.write("\n")
            settingCount += 1

        file.flush()
    
    def writeSECCMLanding(self, xy, file):
        coordinatelist = [float(x) for x in xy]
        coords = ",".join(map(str, coordinatelist))
        file.write(f"Landing, {coords}")
        file.write("\n")