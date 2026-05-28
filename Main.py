import sys
import io
import pyqtgraph as pg
import time

from typing import Optional

from PySide6.QtCore import Qt, QEvent, QObject, Signal, Slot, QThread, QThreadPool, QRunnable, Slot
from PySide6.QtWidgets import (QApplication, QFileDialog, QMainWindow, QButtonGroup, QPushButton, 
                               QMessageBox, QTextEdit,  QHBoxLayout, QVBoxLayout, QDockWidget,
                               QMainWindow, QStatusBar, QWidget, QFrame, QListWidget,
                               QSplitter, QPlainTextEdit, QLabel, QTreeWidgetItem, QAbstractItemView,
                               QTreeWidget, QProgressDialog)

from Biologic import Biologic
from ExpLoad import ExpLoad
from Mapping import Mapping
from TechSettings import TechSettings
from Device import Device
from SECCM import approachSECCM
from Plotting import Plot

"""
Main file for the SECCM software
"""
class Worker(QRunnable):
    def __init__(self, func):
        super().__init__()
        self.function= func

    @Slot()
    def runFunc(self):
        self.function

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

        #region: Devices Status
        self.frameDevices= QFrame(); self.mainFrame_layout2.addWidget(self.frameDevices)
        self.frameDevices.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Plain)
        self.devicesLayout= QVBoxLayout(self.frameDevices)
        self.devices= Device(); self.devicesLayout.addWidget(self.devices)
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
        self.console_stream.text_written.connect(self.append_text) #Connect the emitted signal to the method append_text, so that all emitted messages are inserted in the log
        sys.stdout= self.console_stream

        #endregion

        #region: Plotting Section
        self.plotFrame= QFrame(); self.mainFrame_layout1.addWidget(self.plotFrame)
        self.plotLayout= QVBoxLayout(self.plotFrame)
        self.plot= Plot.Plot(); self.plotLayout.addWidget(self.plot)
          
        #endregion

        #region: Signal and event
        self.thread_pool = QThreadPool.globalInstance()

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

    @Slot(list)
    def PIupdatePosition(self, coordinates):
        self.mapping.labelXpos= coordinates[0]
        self.mapping.labelYpos= coordinates[1]
        self.mapping.labelZpos= coordinates[2]

    @Slot(float)
    def progress(self, value):
        print(value)

    
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

        self.devices.positioner.Xmove= self.mapping.settingsStage.moveX
        self.devices.positioner.Ymove= self.mapping.settingsStage.moveY
        self.devices.positioner.Zmove= self.mapping.settingsStage.moveZ

        XYZpos= self.devices.positioner.move()

        if isinstance(XYZpos,str):
            QMessageBox.warning(self, 'Warning', XYZpos)

        else:
            self.mapping.labelXpos.setText(str(round(XYZpos[0],2))) 
            self.mapping.labelYpos.setText(str(round(XYZpos[1],2))) 
            self.mapping.labelZpos.setText(str(round(XYZpos[2],2))) 

            self.mapping.lineXmove.setText('0')
            self.mapping.lineYmove.setText('0')
            self.mapping.lineZmove.setText('0')

        """
        progressBar= QProgressDialog("Moving positioners, please wait until all movement is stopped!", 'Cancel', 0, 100)
        progressBar.setWindowModality(Qt.WindowModality.WindowModal)

        self.PIthread= QThread()

        self.devices.positioner.moveToThread(self.PIthread)
        self.PIthread.started.connect(self.devices.positioner.movePositioners())
        self.devices.positioner.finished.connect(self.PIthread.quit)
        self.devices.positioner.finished.connect(self.devices.positioner.deleteLater)
        self.PIthread.finished.connect(self.PIthread.deleteLater)

        self.devices.positioner.progress.connect(progressBar.setValue)
        self.devices.positioner.position.connect(self.PIupdatePosition)

        self.PIthread.start()
        """
    def PIreset(self):
        self.devices.positioner.reset()
    
    def PIstop(self):
        self.devices.positioner.stop()

    def PImoveTo(self):
        selection= self.mapping.listWaypoints.currentItem()

        if selection:
            coordinates= selection.data(Qt.ItemDataRole.UserRole)
            print(coordinates)
            #self.devices.positioner.moveTo(coordinates)
        else:
            print("No position selected!")


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
            data=[]

            match self.mapping.settingsMap.mode:
                case 0:
                    print("Echem Only")

                    for tech in techList:
                        for output in self.devices.potentiostat.runExperiment(tech):

                            dataline= ','.join(str(item) for item in output.values())
                            data.append(dataline)
                            f.write(dataline)

                            self.plot.add_dataPoint(tech.technique, output)

                case 1:
                    print("SECCM Mapping")

                case 2:
                    print("SECM Mapping")

if __name__ == '__main__':
    
    app= QApplication(sys.argv)
    main= Main()
    main.show()
    app.exec()

