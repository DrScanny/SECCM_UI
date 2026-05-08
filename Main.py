import sys
import io
import pyqtgraph as pg

from PySide6.QtCore import Qt, QEvent, QObject, Signal, Slot
from PySide6.QtWidgets import (QApplication, QFileDialog, QMainWindow, QButtonGroup, QPushButton, 
                               QMessageBox, QTextEdit,  QHBoxLayout, QVBoxLayout, QDockWidget,
                               QMainWindow, QStatusBar, QWidget, QFrame, QListWidget,
                               QSplitter, QPlainTextEdit, QLabel, QTreeWidgetItem, QAbstractItemView,
                               QTreeWidget)

from Biologic import Biologic
from ExpLoad import ExpLoad
from Mapping import Mapping
from TechSettings import TechSettings
from Devices import Device

"""
Main file for the SECCM software
"""

class ConsoleStream(QObject):
    text_written= Signal(str)

    def write(self, text):
        self.text_written.emit(str(text))

    def flush(self):
        # Flush is required for Python 3 compatibility
        pass

class Main(QMainWindow):
   
    def __init__(self):
        super().__init__()

        self.itemTechPair= {}

        #Setting up main window
        self.setWindowTitle("MercaThor: Electrochemical Imaging") #Window title
        self.setStyleSheet("font: 10pt")

        self.mainFrame=QFrame()
        self.mainFrame_layout1= QHBoxLayout(); self.mainFrame.setLayout(self.mainFrame_layout1)
        self.mainFrame_layout2= QVBoxLayout(); self.mainFrame_layout1.addLayout(self.mainFrame_layout2)
        self.setCentralWidget(self.mainFrame)

        self.layoutMainHorizontal= QHBoxLayout(); self.mainFrame_layout2.addLayout(self.layoutMainHorizontal)

        #region: Experiment Loadout Section
        self.techFrame= QFrame(); self.layoutMainHorizontal.addWidget(self.techFrame, alignment= Qt.AlignmentFlag.AlignCenter)
        self.techFrame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        self.techFrame.setFixedWidth(270)
        self.techFrame_layout= QVBoxLayout(self.techFrame); self.techFrame.setLayout(self.techFrame_layout)

        self.frameDevices= QFrame(); self.techFrame_layout.addWidget(self.frameDevices)
        self.frameDevices.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Plain)
        self.devicesLayout= QVBoxLayout(self.frameDevices)
        self.devices= Device(); self.devicesLayout.addWidget(self.devices)

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
        self.frameMapping= QFrame(); self.layoutMainHorizontal.addWidget(self.frameMapping)
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

        self.console_stream= ConsoleStream()
        self.console_stream.text_written.connect(self.append_text)
        sys.stdout= self.console_stream

        #endregion

        #region: Plotting Section
        self.plotFrame= QFrame(); self.mainFrame_layout1.addWidget(self.plotFrame)
        self.plotLayout= QVBoxLayout(self.plotFrame)
        self.plotLabel= QLabel('Plotting Section Placeholder'); self.plotLayout.addWidget(self.plotLabel)
          
        #endregion

        #Signal and event
        self.experiments.list.itemDoubleClicked.connect(self.Main_AddTechnique)
        self.experiments.addButton.clicked.connect(self.Main_AddTechnique)
        self.experiments.tree.itemClicked.connect(self.Main_ChangeSettingsPage)

        self.experiments.buttonStart.clicked.connect(self.Main_StartExp)

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
            self.textLog.appendPlainText("Failed to load echem technique settings: Main.addTechnique")

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
    
    def Main_StartExp(self):
        """
        1- Preliminary testing

            1- Verify Connection to all devices
            2- Verify nothing else is happening
            3- Open file dialog and create file to save data to
        """
        file_path, _ = QFileDialog.getSaveFileName(
                                                    parent=None,
                                                    caption="Create Save File",
                                                    dir="",
                                                    filter="Text Files (*.txt);;All Files (*)")
        
        

        """
        2- Set map landing coordinates and move to coordinates

            1- Determine landing coordinates
            2- Move stage to coordinate

        """

        """
        3- Setup and start approach curve

            1- Load echem approach method
            2- Initialize Coarse Z and nanocube settings and starting positions
            3- Start approach curve
            4- Stop when threshold reached


        """
        


        """
        3- Start measurements from experiment loadout

            1- Load echem approach method
            2- Initialize Coarse Z and nanocube settings and starting positions

        """
        # Loading technique from techList
        techList=[self.itemTechPair[tech].settings for tech in self.experiments.getAll()]
        print(techList)

if __name__ == '__main__':
    
    app= QApplication(sys.argv)
    main= Main()
    main.show()
    app.exec()

