from PySide6.QtCore import Qt, QEvent, QObject, Signal, Slot, QThread, QThreadPool, QRunnable, Slot, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (QApplication, QFileDialog, QMainWindow, QButtonGroup, QPushButton, 
                               QMessageBox, QTextEdit,  QHBoxLayout, QVBoxLayout, QDockWidget,
                               QMainWindow, QStatusBar, QWidget, QFrame, QListWidget,
                               QSplitter, QPlainTextEdit, QLabel, QTreeWidgetItem, QAbstractItemView,
                               QTreeWidget, QProgressDialog, QProgressBar, QDialog, QDialogButtonBox)

import sys
import time
import functools
import os
import threading

from BiologicAPI.Biologic import Biologic
from ExpLoad import ExpLoad
from Mapping import Mapping
from EchemSettings.EchemSettings import TechSettings
import Device
import SECCM
from Plotting import Plot
from PI import PI
import UI_Settings
import SECM
from FileWriter import FileWrite

"""
Main file for the SECCM software
"""

class ConsoleStream(QObject): # A Class to emit any messages from Python console
    text_written= Signal(str) #Predefine a signal (str) to be emitted

    def write(self, text): #method to emit signal
        self.text_written.emit(str(text)) 

    def flush(self):
        # Flush is required for Python 3 compatibility
        pass

class threadInit():
    def __init__(self, workerClass, *arg):
        self.thread= QThread()
        self.worker= workerClass(self.thread, *arg)

        self.worker.moveToThread(self.thread)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

class Main(QMainWindow):
    triggerStop= Signal(str)
   
    def __init__(self):
        super().__init__()

        #Data storage Attributes using Treewidgets as dictionary keys
        #itemTechPair store echem settings UI instance 
        self.itemTechPair= {}

        #Main window initialization
        self.setWindowTitle("MercaThor: Electrochemical Imaging") 

        self.mainFrame=QFrame()
        self.mainFrame_layout1= QHBoxLayout(); self.mainFrame.setLayout(self.mainFrame_layout1)
        self.mainFrame_layout2= QVBoxLayout(); self.mainFrame_layout1.addLayout(self.mainFrame_layout2)
        self.setCentralWidget(self.mainFrame)

        resolution= QGuiApplication.primaryScreen().geometry() #Getting the monitor resolution
        self.setGeometry(0, 0, int(resolution.width()/1.1), int(resolution.height()/1.5)) #Set the window geometry based on the monitor resolution
        self.move(int(resolution.width()/2-self.frameSize().width()/2), int(resolution.height()/1.25-self.frameSize().height()))

        #---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        #region: A- Interface
        #Contains All PySide UI elements and related signals
        # 1-Status bar
        # 2-Device Status
        # 3-Experiment Loadout Section
        # 4-Echem Technique Settings Section
        # 5-Positioner and Mapping Section
        # 6-Logbook Section
        # 7-Plotting Section
        # 8-Signals
        #-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        #region: A1-Status bar
        self.status_bar = self.statusBar() 
        
        self.status_bar.setStyleSheet(""" QStatusBar {font-size: 12px;}    """)                        
        self.statusLabel= QLabel('  Status  '); self.statusLabel.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)
        self.statusAction= QLabel('Ready '); self.statusAction.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)
        self.frameProgress=QFrame(); self.frameProgress.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)
        self.frameLayout= QVBoxLayout(self.frameProgress); self.frameLayout.setContentsMargins(10, 0, 10, 0)
        self.progress= QProgressBar(); self.frameLayout.addWidget(self.progress)
        self.progress.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        self.progress.setRange(0, 0)
        self.progress.hide()

        self.status_bar.addWidget(self.statusLabel)
        self.status_bar.addWidget(self.statusAction)
        self.status_bar.addWidget(self.frameProgress)
   
        #region: A2-Devices
        self.devices= Device.DeviceManager(); self.mainFrame_layout2.addWidget(self.devices)

        #region: A3-Exp Loadout
        self.layoutMainHorizontal= QHBoxLayout(); self.mainFrame_layout2.addLayout(self.layoutMainHorizontal)
        self.experiments= ExpLoad(); self.layoutMainHorizontal.addWidget(self.experiments)

        #region: A4-Echem
        self.techSettings= TechSettings(); self.layoutMainHorizontal.addWidget(self.techSettings)
  
        #region: A5-Positioner
        self.mapping= Mapping(); self.mainFrame_layout1.addWidget(self.mapping)

        #region: A6-Logbook
        self.logFrame= QFrame()
        self.logLayout= QVBoxLayout(self.logFrame)
        self.mainFrame_layout2.addWidget(self.logFrame)

        self.labelLog= QLabel('Logbook'); self.logLayout.addWidget(self.labelLog)
        self.textLog= QPlainTextEdit(); self.logLayout.addWidget(self.textLog)
        self.textLog.ensureCursorVisible()

        #Instantiating a signal that emit text and connect to python standard output file (python console that displays messages)
        self.console_stream= ConsoleStream()
        sys.stdout= self.console_stream
   
        #region: A7-Plotting
        self.plotFrame= QFrame(); self.mainFrame_layout1.addWidget(self.plotFrame)
        self.plotFrame.setFixedWidth(800)
        self.plotLayout= QVBoxLayout(self.plotFrame)
        self.plot= Plot.Plot(); self.plotLayout.addWidget(self.plot)
        self.plot.start_timer()
       
        #region: A8-Signals
        #Displaying messages in UI log by connecting [Signal]:-ConsoleStream- to [Method]: -append_text-
        self.console_stream.text_written.connect(self.append_text) 
        
        #Progress bar start and hide by connecting [Signal]: -devices- to [method]: -_progress-
        self.devices.startCommand.connect(lambda start: self._progress(start))
        self.devices.endCommand.connect(lambda end: self._progress(end))

        #PI positioner commands by connecting [Signal]: -mapping- to [Method]: -PI-
        self.mapping.buttonPosition.clicked.connect(self.PIpos)
        self.mapping.buttonXYZ.clicked.connect(self.PImove)
        self.mapping.buttonMoveTo.clicked.connect(self.PImoveTo)
        self.mapping.buttonReset.clicked.connect(self.PIreset)
        self.mapping.buttonPiezo.clicked.connect(self.PIpiezoMove)

        self.devices.buttonStopAll.clicked.connect(self.stopAll)

        #Experiment Loadout commands
        self.experiments.list.itemDoubleClicked.connect(self.Main_AddTechnique)
        self.experiments.addButton.clicked.connect(self.Main_AddTechnique)
        self.experiments.tree.itemClicked.connect(self.Main_ChangeSettingsPage)
        self.experiments.buttonStart.clicked.connect(self.startEchem)
        self.mapping.buttonMap.clicked.connect(self.startMap)

        #endregion
        #endregion

        self.writer = FileWrite()

    @Slot(str)
    def append_text(self, text):
        self.textLog.insertPlainText(text)


    def Main_AddTechnique(self):
        selection= self.experiments.selection()
        item= QTreeWidgetItem([selection.text()])
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsDropEnabled) 
        self.experiments.tree.addTopLevelItem(item)
        page= self.techSettings.techInst(selection.text())

        if page:
            self.itemTechPair[item]= page
            self.techSettings.stack.addWidget(page)
            self.techSettings.stack_changeWidget(page)
        else:
            print("Failed to load echem technique settings: Main.addTechnique")

    def Main_ChangeSettingsPage(self):
        item= self.experiments.tree.currentItem()
        self.techSettings.stack_changeWidget(self.itemTechPair[item])
    #endregion

    #region: B2-BiologicRun
    def BiologicRun(self):

        #-----------------------------------------------------------------------------------------------------------------------------------
        #Creating new thread and worker class instance to execute method
        #The worker class instance must be self-contained and have everything needed inside: arguments as attribute (including device connection) and method to run in thread
        #device connection
        #Once thread and worker instance are created, the worker is moved inside the thread and connect to the started signal
        #-----------------------------------------------------------------------------------------------------------------------------------
        try:
            self.BL= threadInit(Biologic, self.devices.BL.potentiostat, self.techList)
            self.BL.thread.started.connect(self.BL.worker.runEchem)
            self.BL.worker.technique.connect(lambda techSettings: self.newPlot(techSettings))
            self.BL.worker.echemData.connect(lambda echemData: self.updatePlot(echemData))
            self.BL.worker.done.connect(self.plot.dataTree.storeData)
            self.BL.worker.finished.connect(lambda: self._progress({'end':'0'}))
            self.BL.worker.finished.connect(lambda: self._closeThread())
       
            self.BL.thread.start()
            self._disableAction()
            self._progress({'start': 'Echem Measurement'})

        except Exception as err:
            f'[ERROR] **Main|BiologicRun**: {err}.'
    
    #endregion

    #region: Position update
    def PIpos(self):
        try:
            self.PI= threadInit(PI, self.devices.PIdevices)
            self.PI.thread.started.connect(self.PI.worker.updatePosition)
            self.PI.worker.position.connect(lambda position: self._positionUpdate(position))
            self.PI.worker.finished.connect(lambda: self._progress({'end':'0'}))
            
            if not self.PI.thread.isRunning():
                self.PI.thread.start()
            else:
                print('[ERROR] Positioners are busy, wait before performing another action.')
        
        except Exception as err:
            f'[ERROR] **Main|PIpos**: {err}.'

    #region: B3-PImove
    def PImove(self):

        try:
            move= [float(self.mapping.lineXmove.text()), float(self.mapping.lineYmove.text()), float(self.mapping.lineZmove.text()), float(self.mapping.linePzmove.text())]

            self.PI= threadInit(PI, self.devices.PIdevices, move)
            self.PI.thread.started.connect(self.PI.worker.moveXYZ)
            self.PI.worker.position.connect(lambda position: self._positionUpdate(position))
            self.PI.worker.finished.connect(lambda: self._progress({'end':'0'}))
            self.PI.worker.finished.connect(lambda: self._closeThread())
            
            self.PI.thread.start()
            self._disableAction()
            self._progress({'start': 'Positioner Moving'})
            self.mapping.lineXmove.setText('0'); self.mapping.lineYmove.setText('0'); self.mapping.lineZmove.setText('0')
        
        except Exception as err:
            f'[ERROR] **Main|PImove**: {err}.'

    def PIpiezoMove(self):
    
        try:
            move= [float(self.mapping.lineXmove.text()), float(self.mapping.lineYmove.text()), float(self.mapping.lineZmove.text()), float(self.mapping.linePzmove.text())]

            self.PI= threadInit(PI, self.devices.PIdevices, move)
            self.PI.thread.started.connect(self.PI.worker.movePz)
            self.PI.worker.position.connect(lambda position: self._positionUpdate(position))
            self.PI.worker.finished.connect(lambda: self._progress({'end':'0'}))
            self.PI.worker.finished.connect(lambda: self._closeThread())
            
            self.PI.thread.start()
            self._disableAction()
            self._progress({'start': 'Positioner Moving'})
            self.mapping.linePzmove.setText('0')
        
        except Exception as err:
            f'[ERROR] **Main|PIpiezo**: {err}.'

    #region: B4-PImoveTo
    def PImoveTo(self):

        try:
            selected= self.mapping.listWaypoints.currentItem()
            move= selected.data(Qt.ItemDataRole.UserRole)

            self.PI= threadInit(PI, self.devices.PIdevices, move)
            self.PI.thread.started.connect(self.PI.worker.moveToXYZ)
            self.PI.worker.position.connect(lambda position: self._positionUpdate(position))
            self.PI.worker.finished.connect(lambda: self._progress({'end':'0'}))
            self.PI.worker.finished.connect(lambda: self._closeThread())
            
            self.PI.thread.start()
            self._disableAction()
            self._progress({'start': 'Positioner Moving'})

        except AttributeError:
            print('[ERROR] **Main|PImoveTo** requires a position to be selected')
        
        except Exception as err:
            f'[ERROR] **Main|PImoveTo**: {err}.'

    #region: B5-PIreset
    def PIreset(self):
        try:

            self.PI= threadInit(PI, self.devices.PIdevices)
            self.PI.thread.started.connect(self.PI.worker.resetXYZ)
            self.PI.worker.position.connect(lambda position: self._positionUpdate(position))
            self.PI.worker.finished.connect(lambda: self._progress({'end':'0'}))
            self.PI.worker.finished.connect(lambda: self._closeThread())
            
            self.PI.thread.start()
            self._disableAction()
            self._progress({'start': 'Positioner Reset'})
        
        except Exception as err:
            f'[ERROR] **Main|PIreset**: {err}.'

    #region: Imaging
    def runMap(self):
        
        PImethod= SECM.SECM_PI
        BLmethod= SECM.SECM_BL
        self.mapping.mapCoordinates()
        ExpSettings= self.mapping.settingsSECM
        MapSettings= self.mapping.settingsMapping
       
        #print(f'map:{map} and techList:{self.techList}')
       
        match UI_Settings.Mapping: #Choosing which mapping method to use SECM or SECCM
            case 0: #SECM
                print('[DEBUG] runMap SECM')
           
            case 1: #SECCM
                print('[DEBUG] runMap SECCM')
                PImethod= SECCM.SECCM_PI
                BLmethod= SECCM.SECCM_BL
                ExpSettings= self.mapping.settingsSECCM
                ExpSettings.techList= [self.itemTechPair[tech].settings for tech in self.experiments.getAll()] # Loading echem technique from UI techLost
                 
        self.events= {}
        self.events['ready']= threading.Event()
        self.events['limit']= threading.Event()
        self.events['stop']= threading.Event()

        #Thread assigned to the positioners control during approach
        self.PI= threadInit(PImethod, self.devices.PIdevices, ExpSettings, MapSettings, self.events)
        self.PI.thread.started.connect(self.PI.worker.approach)
        self.PI.worker.position.connect(lambda position: self._positionUpdate(position))
        self.PI.worker.finished.connect(lambda: self._closeThread())
        self.PI.worker.finished.connect(lambda: self._progress({'end':'0'}))

        #Thread assigned to the potentiostat control during approach
        self.BL= threadInit(BLmethod, self.devices.BL.potentiostat, ExpSettings, MapSettings, self.events)
        self.BL.thread.started.connect(self.BL.worker.approach)
        self.BL.worker.technique.connect(lambda settings: self.newPlot(settings, dataTree=False))
        self.BL.worker.echemData.connect(lambda data: self.updatePlot(data))
        
        self.BL.thread.start()
        self.PI.thread.start()
        self._disableAction()
        self._progress({'start': 'SECM Experiment'})
     
    #region: B8-**Run**
    def startEchem(self):
        try:
            #Open and create a file for collected data
            self.createFile()

            # Loading echem technique from UI techLost
            self.techList=[self.itemTechPair[tech].settings for tech in self.experiments.getAll()]

            # Starting in different thread biologic class
            self.BiologicRun()            

        except Exception as err:
            print(f'[ERROR] **Main|startEchem**:{err}')

    def startMap(self):
        try:
            #Open and create a file for collected data
            self.createFile()

            # Starting in different thread SECM class
            print("[DEBUG startSECM] Starting SECM Mapping")
            self.runMap() #Call method to start SECM in new thread

        except Exception as err:
            print(f'[ERROR] **Main|startMAP**:{err}')
        
    def stopAll(self):
        print('[DEBUG] pressed stopAll')
      
        try:
            self.BL.thread.requestInterruption()
        except AttributeError:
            pass
        except Exception as err:
            print(f'[ERROR] **Main|stopAll**:{err}')
            
        try:
            self.PI.thread.requestInterruption()
        except AttributeError:
            pass
        except Exception as err:
            print(f'[ERROR] **Main|stopAll**:{err}')

    #endregion

    #region: C-Utilities
    #Contains secondary methods that are helpful for core methods

    #region: CreateFile
    def createFile(self):
        filePath, _ = QFileDialog.getSaveFileName(
                                                    parent=None,
                                                    caption="Create Save File",
                                                    dir="",
                                                    filter="Text Files (*.txt);;All Files (*)")
        
        self.filename = os.path.basename(filePath)
        self.plot.dataTree.setFilename(self.filename)

        self.data_file= open(filePath, "a", encoding="utf-8-sig")  

    #region: Update Position
    def _positionUpdate(self, position):
        self.mapping.labelXpos.setText(str(position[0]))
        self.mapping.labelYpos.setText(str(position[1]))
        self.mapping.labelZpos.setText(str(position[2]))
        self.mapping.labelPzpos.setText(str(position[3]))

    #region: Progress Bar
    def _progress(self, status:dict[str,str]):
        if 'start' in status:
            self.statusAction.setText(status['start'])
            self.progress.show()

        elif 'end' in status:
            self.statusAction.setText('Ready ')
            self.progress.hide()

    #region: Enable/Disable
    def _disableAction(self):
        self.experiments.buttonStart.setEnabled(False)
        self.mapping.buttonMap.setEnabled(False)
        self.mapping.buttonXYZ.setEnabled(False)
        self.mapping.buttonPiezo.setEnabled(False)
        self.mapping.buttonReset.setEnabled(False)
        self.mapping.buttonMoveTo.setEnabled(False)

    def _enableAction(self):
        self.experiments.buttonStart.setEnabled(True)
        self.mapping.buttonMap.setEnabled(True)
        self.mapping.buttonXYZ.setEnabled(True)
        self.mapping.buttonPiezo.setEnabled(True)
        self.mapping.buttonReset.setEnabled(True)
        self.mapping.buttonMoveTo.setEnabled(True)

    #region: Plotting
    #When a new technique is started from the list of experiments from techList, setup the plot axes and new dataTree entry
    def newPlot(self, echemSettings, dataTree=True):
        self.writer.writeEchemSettings(echemSettings, self.data_file)
        self.plot.setAxes(echemSettings)

        #Create new QTreeWidgetItem based on the 
        if dataTree:
            self.plot.dataTree.newtechniqueEntry(echemSettings.technique)
       
    #From the emitted echem data, plot live data and store it in an instance of UI_Settings.echemData: self.plot.dataTree.active
    def updatePlot(self, data):
        #Update plot with latest data
        self.plot.add_data_point(data)

        #append echemData to current run
        self.plot.dataTree.active.t.append(data['t'])
        self.plot.dataTree.active.Ewe.append(data['Ewe'])
        if 'Iwe' in data:
            self.plot.dataTree.active.Iwe.append(data['Iwe'])
        if 'cycle' in data:
            self.plot.dataTree.active.cycle.append(data['cycle'])
        
        dataToWrite = ",".join(map(str, [data['t'], data['Ewe'], data['Iwe'],data['cycle']]))
        self.writer.writeData(dataString=dataToWrite, file=self.data_file)

    # Function that execute commands when a thread is closed
    def _closeThread(self):
        print('[DEBUG] thread closed')
        self._enableAction()

        try:
            if self.data_file: #checking if file is open
                self.data_file.close()
                print('Datafile closed')
                
        except NameError:
            print('[_closeThread] No datafile found to close')
        else:
            pass   

    """
    def closeEvent(self, event):
        # Create a confirmation dialog
        reply = QMessageBox.question(self, 'Confirm Close',
                                "Are you sure you want to exit?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            # Clean up and allow the window to close

            if self.devices.BL.potentiostat['api']:
                self.devices.disconnectPotentiostat(self.devices.BL)
    
            if self.devices.XY.positioner.gcscommands.IsConnected():
                self.devices.XY.positioner.gcscommands.CloseConnection()
            
            if self.devices.Z.positioner.gcscommands.IsConnected(): 
                self.devices.Z.positioner.gcscommands.CloseConnection()

            if self.devices.Pz.positioner.gcscommands.IsConnected():
                self.devices.Pz.positioner.gcscommands.CloseConnection()

            event.accept() 
        else:
            # Prevent the window from closing
            event.ignore()
   
    #endregion
    """

    #region: Input
    #Contain keyboard or mouse event to execute UI commands
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            treeSelection= self.experiments.tree.currentItem()
            widget= self.itemTechPair[treeSelection]
            self.techSettings.stack.removeWidget(widget)

            if treeSelection:
                parent = treeSelection.parent()
                if parent:
                    parent.removeChild(treeSelection)
                else:
                    idx = self.experiments.tree.indexOfTopLevelItem(treeSelection)
                    self.experiments.tree.takeTopLevelItem(idx)
            
        else:
            super().keyPressEvent(event)
    #endregion

if __name__ == '__main__':
    
    app= QApplication(sys.argv)
    main= Main()
    main.show()
    app.exec()

