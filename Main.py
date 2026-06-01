from PySide6.QtCore import Qt, QEvent, QObject, Signal, Slot, QThread, QThreadPool, QRunnable, Slot
from PySide6.QtWidgets import (QApplication, QFileDialog, QMainWindow, QButtonGroup, QPushButton, 
                               QMessageBox, QTextEdit,  QHBoxLayout, QVBoxLayout, QDockWidget,
                               QMainWindow, QStatusBar, QWidget, QFrame, QListWidget,
                               QSplitter, QPlainTextEdit, QLabel, QTreeWidgetItem, QAbstractItemView,
                               QTreeWidget, QProgressDialog, QProgressBar, QDialog, QDialogButtonBox)

import sys
import io
import pyqtgraph as pg
import time

from typing import Optional

from BiologicAPI.Biologic import Biologic
from ExpLoad import ExpLoad
from Mapping import Mapping
from EchemSettings.EchemSettings import TechSettings
from Device import Device
from SECCM import approachSECCM
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

class Main(QMainWindow):
   
    def __init__(self):
        super().__init__()

        #Dictionnary that serves as repository for echem techniques using the techSettings.tree as keys
        self.itemTechPair= {}

        #Setting up main window
        self.setWindowTitle("MercaThor: Electrochemical Imaging") #Window title
        self.setStyleSheet("font: 10pt") #Set the font size for eveything in the Main window. Will likely replaced to be able to control each GUI element

        self.mainFrame=QFrame()
        self.mainFrame_layout1= QHBoxLayout(); self.mainFrame.setLayout(self.mainFrame_layout1)
        self.mainFrame_layout2= QVBoxLayout(); self.mainFrame_layout1.addLayout(self.mainFrame_layout2)
        self.setCentralWidget(self.mainFrame)

        #Status bar
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

        #region: Devices Status
        self.frameDevices= QFrame(); self.mainFrame_layout2.addWidget(self.frameDevices)
        self.frameDevices.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        self.devicesLayout= QVBoxLayout(self.frameDevices)
        self.devices= Device(); self.devicesLayout.addWidget(self.devices)
        #self.devices= Device(); self.mainFrame_layout2.addWidget(self.devices)
        
        #endregion

        #region: Experiment Loadout Section
        self.layoutMainHorizontal= QHBoxLayout(); self.mainFrame_layout2.addLayout(self.layoutMainHorizontal)
        self.techFrame= QFrame(); self.layoutMainHorizontal.addWidget(self.techFrame, alignment= Qt.AlignmentFlag.AlignCenter)
        self.techFrame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        self.techFrame.setFixedWidth(270)
        self.techFrame_layout= QVBoxLayout(self.techFrame); self.techFrame.setLayout(self.techFrame_layout)

        self.frameExperiments=QFrame(); self.techFrame_layout.addWidget(self.frameExperiments)
        self.frameExperiments.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Plain)
        self.experimentsLayout= QVBoxLayout(self.frameExperiments)
        self.experiments= ExpLoad(); self.experimentsLayout.addWidget(self.experiments)

        self.techFrame_layout.addStretch()
        #endregion

        #region: Echem Technique Settings Section
        self.settingsFrame= QFrame(); self.layoutMainHorizontal.addWidget(self.settingsFrame)
        self.settingsFrame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        self.settingsLayout= QVBoxLayout(self.settingsFrame)
        self.techSettings= TechSettings(); self.settingsLayout.addWidget(self.techSettings)
        #endregion

        #region: Stage Control and Approach Settings Section
        self.frameMapping= QFrame(); self.mainFrame_layout1.addWidget(self.frameMapping)
        self.frameMapping.setFrameStyle(QFrame.Shape.Box| QFrame.Shadow.Plain)
        self.layoutMapping= QVBoxLayout(self.frameMapping)
        self.mapping= Mapping(); self.layoutMapping.addWidget(self.mapping)
        #endregion

        #region: Logbook Section
        self.logFrame= QFrame()
        self.logLayout= QVBoxLayout(self.logFrame)
        self.mainFrame_layout2.addWidget(self.logFrame)

        self.labelLog= QLabel('Logbook'); self.logLayout.addWidget(self.labelLog)
        self.textLog= QPlainTextEdit(); self.logLayout.addWidget(self.textLog)
        self.textLog.ensureCursorVisible()

        #Transferring message from Python console to the software log
        self.console_stream= ConsoleStream()
        sys.stdout= self.console_stream
        #endregion

        #region: Plotting Section
        self.plotFrame= QFrame(); self.mainFrame_layout1.addWidget(self.plotFrame)
        self.plotLayout= QVBoxLayout(self.plotFrame)
        self.plot= Plot.Plot(); self.plotLayout.addWidget(self.plot)
          
        #endregion

        #region: Signal and event
        self.console_stream.text_written.connect(self.append_text) #Connect the emitted signal to the method append_text, so that all emitted messages are inserted in the log

        self.mapping.buttonMove.clicked.connect(self.PImove)
        self.mapping.buttonMoveTo.clicked.connect(self.PImoveTo)
        self.mapping.buttonReset.clicked.connect(self.PIreset)

        self.experiments.list.itemDoubleClicked.connect(self.Main_AddTechnique)
        self.experiments.addButton.clicked.connect(self.Main_AddTechnique)
        self.experiments.tree.itemClicked.connect(self.Main_ChangeSettingsPage)

        self.experiments.buttonStart.clicked.connect(self.Main_StartExp)
        #endregion

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

    def PImove(self):

        move= [float(self.mapping.lineXmove.text()), float(self.mapping.lineYmove.text()), float(self.mapping.lineZmove.text())]
        print(f'move[2] type is {type(move[2])}')
        
        self.statusAction.setText('Positioner in movement ')
        self.progress.show()
     
        self.PIthread= QThread()
        self.worker= PI()
        self.worker.moveToThread(self.PIthread)
        self.PIthread.started.connect(lambda: self.worker.movePI(self.devices.XYstage, self.devices.Zstage, move))
        self.worker.finished.connect(self.PIthread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.PIthread.finished.connect(self.PIthread.deleteLater)
        self.PIthread.finished.connect(self.progress.hide)
        self.worker.position.connect(lambda p: self.positionUpdate(p))
        self.worker.warning.connect(lambda w: print(w))
        self.PIthread.finished.connect(lambda: self.statusAction.setText('Ready '))

        self.PIthread.start()

        self.mapping.lineXmove.setText('0')
        self.mapping.lineYmove.setText('0')
        self.mapping.lineZmove.setText('0')

    def PIreset(self):

        self.statusAction.setText('Positioner in movement ')
        self.progress.show()

        self.PIthread= QThread()
        self.worker= PI()
        self.worker.moveToThread(self.PIthread)
        self.PIthread.started.connect(lambda: self.worker.resetPI(self.devices.XYstage, self.devices.Zstage))
        self.worker.finished.connect(self.PIthread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.PIthread.finished.connect(self.PIthread.deleteLater)
        self.PIthread.finished.connect(self.progress.hide)
        self.PIthread.finished.connect(lambda: self.statusAction.setText('Ready '))

        self.PIthread.start() 
    
    def PIstop(self):
        self.statusAction.setText('Positioner in movement ')

        self.PIthread= QThread()
        self.worker= PI()
        self.worker.moveToThread(self.PIthread)
        self.PIthread.started.connect(lambda: self.worker.stopPI(self.devices.XYstage, self.devices.Zstage))
        self.worker.finished.connect(self.PIthread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.PIthread.finished.connect(self.PIthread.deleteLater)
        self.PIthread.finished.connect(lambda: self.statusAction.setText('Ready '))

        self.thread.start()

    def PImoveTo(self):
        self.statusAction.setText('Positioner in movement ')
        self.progress.show()

        selection= self.mapping.listWaypoints.currentItem()

        if selection:
            move= selection.data(Qt.ItemDataRole.UserRole)
            self.PIthread= QThread()
            self.worker= PI()
            self.worker.moveToThread(self.PIthread)
            self.PIthread.started.connect(lambda: self.worker.moveToPI(self.devices.XYstage, self.devices.Zstage, move))
            self.worker.finished.connect(self.PIthread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.PIthread.finished.connect(self.PIthread.deleteLater)
            self.PIthread.finished.connect(lambda: self.statusAction.setText('Ready '))
            self.PIthread.finished.connect(self.progress.hide)

            self.PIthread.start()
 
        else:
            print("No position selected!")

    def BiologicRun(self, file, technique, dataStorage:list[str]):
        self.statusAction.setText('Electrochemical Experiments Running ')
        self.progress.show()

        self.biologicThread= QThread()
        self.worker= Biologic(self.devices.potentiostat)
        self.worker.moveToThread(self.biologicThread)
        self.biologicThread.started.connect(lambda: self.worker.runEchem(technique))
        self.worker.echemData.connect(lambda data: print(data))
        self.biologicThread.finished.connect(lambda: print('finished'))
        self.worker.finished.connect(self.biologicThread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.biologicThread.finished.connect(self.biologicThread.deleteLater)
  

        self.biologicThread.start()

    def updateEchemData(self, file, echemData:list[str], technique:str, data:dict[str,float]):
        dataline= ','.join(str(item) for item in data.values())
        file.write(dataline +'\n')
        echemData.append(dataline)
        self.plot.add_dataPoint(technique, data)

    def positionUpdate(self, position):
        self.mapping.labelXpos.setText(position[0])
        self.mapping.labelYpos.setText(position[1])
        self.mapping.labelZpos.setText(position[2]-25)

    def Main_StartExp(self):

        #Create savefile for data measurement
        filePath, _ = QFileDialog.getSaveFileName(
                                                    parent=None,
                                                    caption="Create Save File",
                                                    dir="",
                                                    filter="Text Files (*.txt);;All Files (*)")
        
        with open(filePath, "a") as f:

            # Loading technique from techList
            techList=[self.itemTechPair[tech].settings for tech in self.experiments.getAll()]

            match self.mapping.settingsMap.mode:
                case 0:
                    print("Echem Only")

                    for tech in techList:
                        print(tech)
                        dataStorage=[]
                        f.write(tech.header)
                        self.BiologicRun(f, tech, dataStorage)

                case 1:
                    print("SECCM Mapping")

                case 2:
                    print("SECM Mapping")

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

if __name__ == '__main__':
    
    app= QApplication(sys.argv)
    main= Main()
    main.show()
    app.exec()

