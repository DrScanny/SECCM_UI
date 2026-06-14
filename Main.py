from PySide6.QtCore import Qt, QEvent, QObject, Signal, Slot, QThread, QThreadPool, QRunnable, Slot
from PySide6.QtWidgets import (QApplication, QFileDialog, QMainWindow, QButtonGroup, QPushButton, 
                               QMessageBox, QTextEdit,  QHBoxLayout, QVBoxLayout, QDockWidget,
                               QMainWindow, QStatusBar, QWidget, QFrame, QListWidget,
                               QSplitter, QPlainTextEdit, QLabel, QTreeWidgetItem, QAbstractItemView,
                               QTreeWidget, QProgressDialog, QProgressBar, QDialog, QDialogButtonBox)

import sys
import time
import functools

from BiologicAPI.Biologic import Biologic
from ExpLoad import ExpLoad
from Mapping import Mapping
from EchemSettings.EchemSettings import TechSettings
import Device
from SECCM import SECCM_approach
from Plotting import Plot
from PI import PI

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
        print(self.thread)
        self.worker= workerClass(*arg)
        print(self.worker)

        self.worker.moveToThread(self.thread)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
 
class Main(QMainWindow):
   
    def __init__(self):
        super().__init__()

        #Data storage Attributes using Treewidgets as dictionary keys
        #itemTechPair store echem settings UI instance 
        self.itemTechPair= {}
        self.echemData={}

        #Main window initialization
        self.setWindowTitle("MercaThor: Electrochemical Imaging") 

        self.mainFrame=QFrame()
        self.mainFrame_layout1= QHBoxLayout(); self.mainFrame.setLayout(self.mainFrame_layout1)
        self.mainFrame_layout2= QVBoxLayout(); self.mainFrame_layout1.addLayout(self.mainFrame_layout2)
        self.setCentralWidget(self.mainFrame)

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
        self.plotLayout= QVBoxLayout(self.plotFrame)
        self.plot= Plot.Plot(); self.plotLayout.addWidget(self.plot)
       
        #region: A8-Signals
        #Displaying messages in UI log by connecting [Signal]:-ConsoleStream- to [Method]: -append_text-
        self.console_stream.text_written.connect(self.append_text) 
        
        #Progress bar start and hide by connecting [Signal]: -devices- to [method]: -_progress-
        self.devices.startCommand.connect(lambda start: self._progress(start))
        self.devices.endCommand.connect(lambda end: self._progress(end))

        #PI positioner commands by connecting [Signal]: -mapping- to [Method]: -PI-
        self.mapping.buttonMove.clicked.connect(self.PImove)
        self.mapping.buttonMoveTo.clicked.connect(self.PImoveTo)
        self.mapping.buttonReset.clicked.connect(self.PIreset)

        #Experiment Loadout commands
        self.experiments.list.itemDoubleClicked.connect(self.Main_AddTechnique)
        self.experiments.addButton.clicked.connect(self.Main_AddTechnique)
        self.experiments.tree.itemClicked.connect(self.Main_ChangeSettingsPage)
        self.experiments.buttonStart.clicked.connect(self.startMap)
        self.experiments.buttonStop.clicked.connect(self.stopMap)
        #endregion
        #endregion
        
    #region: B-Core Methods
    #Contains all the core methods for critical operation of the SECCM/SECM
    # 1-UI
    # 2-Potentiostat
    # 3-Positioner
    # 4-Mapping

    @Slot(str)
    def append_text(self, text):
        self.textLog.insertPlainText(text)

    #region: B1-UI
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
    def BiologicRun(self, techniqueList):

        #-----------------------------------------------------------------------------------------------------------------------------------
        #Creating new thread and worker class instance to execute method
        #The worker class instance must be self-contained and have everything needed inside: arguments as attribute (including device connection) and method to run in thread
        #device connection
        #Once thread and worker instance are created, the worker is moved inside the thread and connect to the started signal
        #-----------------------------------------------------------------------------------------------------------------------------------
        try:
            
            self.BL= threadInit(Biologic, self.devices.BL.potentiostat, techniqueList)
            self.BL.thread.started.connect(self.BL.worker.runEchem)
            self.BL.worker.echemData.connect(lambda echemData: self._updatePlot(echemData))
            self.BL.worker.finished.connect(lambda: self._progress({'end':'0'}))
            self.BL.thread.start()

        except Exception as err:
            f'[ERROR] **Main|BiologicRun**: {err}.'
    
    #endregion


    #region: B3-PImove
    def PImove(self):

        try:
            move= [float(self.mapping.lineXmove.text()), float(self.mapping.lineYmove.text()), float(self.mapping.lineZmove.text())]

            self.PI= threadInit(PI, {'XY':self.devices.XY.positioner, 'Z':self.devices.Z.positioner, 'Pz':self.devices.Pz.positioner}, move)
            self.PI.thread.started.connect(self.PI.worker.moveXYZ)
            self.PI.worker.position.connect(lambda position: self._positionUpdate(position))
            self.PI.worker.finished.connect(lambda: self._progress({'end':'0'}))
            self.PI.thread.start()

            self._progress({'start': 'Positioner in movement... '})
            self.mapping.lineXmove.setText('0'); self.mapping.lineYmove.setText('0'); self.mapping.lineZmove.setText('0')
        
        except Exception as err:
            f'[ERROR] **Main|PImoveTo**: {err}.'

    #region: B4-PImoveTo
    def PImoveTo(self):

        try:
            selected= self.mapping.listWaypoints.currentItem()
            move= selected.data(Qt.ItemDataRole.UserRole)

            self.PI= threadInit(PI, self.devices.PIdevices, move)
            self.PI.thread.started.connect(self.PI.worker.moveToXYZ)
            self.PI.worker.position.connect(lambda position: self._positionUpdate(position))
            self.PI.worker.finished.connect(lambda: self._progress({'end':'0'}))
            self.PI.thread.start()

            self._progress({'start': 'Positioner in movement... '})

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
            self.PI.thread.start()
            
            self._progress({'start': 'Resetting Positioners... '})
        
        except Exception as err:
            f'[ERROR] **Main|PIreset**: {err}.'

    #region: B6-PIstop
    def PIstop(self):
        try:
            self.PI= threadInit(PI, self.devices.PIdevices)
            self.PI.thread.started.connect(self.PI.worker.resetXYZ)
            self.PI.worker.position.connect(lambda position: self._positionUpdate(position))
            self.PI.thread.start()

        except Exception as err:
            f'[ERROR] **Main|PIstop**: {err}.'

    #endregion

    #region: B7-**Mapping**
    def startMap(self):

        # Loading technique from techList
        techList=[self.itemTechPair[tech].settings for tech in self.experiments.getAll()]

        match self.mapping.settingsMapping.mode:
            case 0:
                print("[TESTING] Echem only")
                self.BiologicRun(techList)
                    
            case 1:
                print("[TESTING] SECCM tip down only")
                self.runSECCM= SECCM_approach(self.devices.PIdevices, self.devices.potentiostat, self.mapping.settingsSECCM)
                
            case 2:
                print("SECM Mapping")

    def stopMap(self):
        try:
            self.BL.worker.stopBiologic()
        
        except Exception as err:
            print(f'[ERROR] **Main|stopMap**:{err}')
        
        
    #endregion

    #region: C-Utilities
    #Contains secondary methods that are helpful for core methods
    # 1-
    # 2-
    # 3-
    # 4-
    
    #region: C1-Positioner
    def _positionUpdate(self, position):
        self.mapping.labelXpos.setText(str(position[0]))
        self.mapping.labelYpos.setText(str(position[1]))
        self.mapping.labelZpos.setText(str(position[2]))

    #region: C2-Progress Bar
    def _progress(self, status:dict[str,str]):
        if 'start' in status:
            self.statusAction.setText(status['start'])
            self.progress.show()

        elif 'end' in status:
            self.statusAction.setText('Ready ')
            self.progress.hide()

    #region: C3-Plotting
    def _updatePlot(self, data):
        self.plot.x_data.append(data['t'])
        self.plot.y_data.append(data['Ewe'])
        if self.plot.plot_item:
            self.plot.plot_item.setData(self.plot.x_data, self.plot.y_data)

    """
    def closeEvent(self, event):
        # Create a confirmation dialog
        reply = QMessageBox.question(self, 'Confirm Close',
                                "Are you sure you want to exit?",
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Clean up and allow the window to close
            try:
                self.devices.potentiostat.disconnect()
                print("Disconnected from VMP-300")
            except:
                print('Error')

            if self.devices.XYstage.gcscommands.IsConnected():
                self.devices.XYstage.gcscommands.CloseConnection()
            
            if self.devices.Zstage.gcscommands.IsConnected(): 
                self.devices.Zstage.gcscommands.CloseConnection()

            if self.devices.piezo.gcscommands.IsConnected():
                self.devices.piezo.gcscommands.CloseConnection()

            event.accept() 
        else:
            # Prevent the window from closing
            event.ignore()
        """
    #endregion

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

