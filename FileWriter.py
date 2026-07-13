class FileWrite():
    def __init__(self):
        super().__init__()
        #placeholder
        self.flushcounter = 1
    
    def writeEchemSettings(self, Settings, file):
        #Edit this to add units to Echem settings
        settingCount = 1
        for name, value in Settings.__dict__.items():
            if name == "header":
                file.write("\n")
                file.write(value)
                file.write("\n")
            else:
                file.write(f"{name}: {value}\n")

        file.flush()

    def writeData(self, dataString, file):
        file.write(dataString)
        file.write("\n")
        self.flushcounter += 1

        #flush every 20 datapoint, might have to increase if there is lag
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