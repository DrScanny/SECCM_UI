from dataclasses import dataclass
import numpy as np

from PySide6.QtCore import (Qt, QCoreApplication, QMetaObject)
from PySide6.QtGui import (QRegularExpressionValidator, QDoubleValidator, QIntValidator)
from PySide6.QtWidgets import (QGridLayout, QLabel, QWidget,  QLayout, QLineEdit, QSizePolicy, QSpacerItem,
                               QVBoxLayout, QComboBox, QFrame, QApplication, QMessageBox, QStackedWidget,
                               QPushButton, QHBoxLayout, QPlainTextEdit, QGroupBox)

import SECCM_Settings
from pipython import GCSDevice, datarectools, pitools

def addWidgetsGrid(widgetsList, layout:QGridLayout, maxCol:int=4):
     for line, widgetsInLine in enumerate(widgetsList):
        for col, widget in enumerate(widgetsInLine):
            if widgetsInLine[0]=='Sep':
                sep= QFrame()
                sep.setFrameShape(QFrame.Shape.HLine)
                layout.addWidget(sep, line, 0, 1, maxCol)
                break

            elif widget== 'Space':
                        continue
            else:
                layout.addWidget(widget, line,col)

def _mapLandings(settings: SECCM_Settings.MapSettings):
    Xlandings= np.arange(0, settings.dX*settings.nX, settings.nX )
    Ylandings= np.arange(0, settings.dY*settings.nY, settings.nY )

def _update_att(value, att)-> None:
     att= value
     print(value)

sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
sizePolicy.setHorizontalStretch(0)
sizePolicy.setVerticalStretch(0)

class Mapping(QWidget):
      
    def __init__(self):
        super().__init__()
        self.frameWidget= QFrame()
        self.layoutWidget= QVBoxLayout()
        self.setLayout(self.layoutWidget)
    
        self.frameMain= QFrame()
        self.frameMain.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Plain)
        self.frameMain.setFixedWidth(300)
        self.layoutMain= QVBoxLayout(self.frameMain)
        self.layoutWidget.addWidget(self.frameMain)
        self.frameMain.setSizePolicy(sizePolicy)


        self.settingsStage= SECCM_Settings.StageSettings()
        self.settingsMap= SECCM_Settings.MapSettings()
        self.settingsApproach= SECCM_Settings.ApproachSettings()
        
        self.widgetPos()
        self.widgetMapping()
        self.widgetStack()

        #self.setStyleSheet("QLineEdit {border: 1px solid gray; border-radius: 4px; background-color: white; padding: 2px;text-decoration: none;}")
    
    def widgetPos(self):
      
        self.groupStage= QGroupBox('Stage Control'); self.groupStage.setStyleSheet(""" QGroupBox {font-weight: bold;}  """)
        #self.framePosition.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Plain)
        self.layoutPosition= QGridLayout(self.groupStage)
        self.layoutMain.addWidget(self.groupStage)
    
        self.labelMove= QLabel('Move'); self.layoutPosition.addWidget(self.labelMove, 3,0)
        self.labelMove.setToolTip("Move the positionner in X, Y axis by up to (-)99 999 \u03bcm at a time and the Z axis by up to (-)1 000 \u03bcm ")

        self.labelPosition= QLabel('Position'); self.layoutPosition.addWidget(self.labelPosition, 4,0)
        self.labelPosition.setToolTip("Indicate the current absolute position in X, Y, Z axis")

        self.labelMax= QLabel('Limits'); self.layoutPosition.addWidget(self.labelMax, 5,0)
        self.labelMax.setToolTip("Indicate the stage limits in X, Y, Z axis")

        self.labelX= QLabel('X'); self.layoutPosition.addWidget(self.labelX, 2,1)
        self.labelX.setAlignment(Qt.AlignmentFlag.AlignCenter) 

        self.lineXmove= QLineEdit(); self.layoutPosition.addWidget(self.lineXmove, 3,1)
        self.lineXmove.setText('0')
        self.lineXmove.setValidator(QIntValidator(-99999, 99999))

        self.labelXpos= QLabel('Xpos');  self.layoutPosition.addWidget(self.labelXpos, 4,1)
        self.labelXmax= QLabel('X');  self.layoutPosition.addWidget(self.labelXmax, 5,1)

        self.labelY= QLabel('Y');  self.layoutPosition.addWidget(self.labelY, 2,2)
        self.labelY.setAlignment(Qt.AlignmentFlag.AlignCenter) 

        self.lineYmove= QLineEdit();  self.layoutPosition.addWidget(self.lineYmove, 3,2)
        self.lineYmove.setText('0')
        self.lineYmove.setValidator(QIntValidator(-99999, 99999))

        self.labelYpos= QLabel('Ypos'); self.layoutPosition.addWidget(self.labelYpos, 4,2)
        self.labelYmax= QLabel('Y'); self.layoutPosition.addWidget(self.labelYmax, 5,2)

        self.labelZ= QLabel('Z');  self.layoutPosition.addWidget(self.labelZ, 2,3)
        self.labelZ.setAlignment(Qt.AlignmentFlag.AlignCenter) 

        self.lineZmove= QLineEdit(); self.layoutPosition.addWidget(self.lineZmove, 3,3)
        self.lineZmove.setText('0')
        self.lineXmove.setValidator(QIntValidator(-1000, 1000))
    
        self.labelZpos= QLabel('Zpos');  self.layoutPosition.addWidget(self.labelZpos, 4,3)
        self.labelZmax= QLabel('Z');  self.layoutPosition.addWidget(self.labelZmax, 5,3)

        self.sepPositionSection= QFrame(); self.layoutPosition.addWidget(self.sepPositionSection,6,0,1,5) 
        self.sepPositionSection.setFrameShape(QFrame.Shape.HLine)
        self.sepPositionSection.setFrameShadow(QFrame.Shadow.Sunken)

        self.buttonMove= QPushButton('Move'); self.layoutPosition.addWidget(self.buttonMove,7,0,1,2)
        self.buttonStop= QPushButton('Stop'); self.layoutPosition.addWidget(self.buttonStop,7,2,1,2)
        #self.buttonMove.clicked.connect()

        self.lineXmove.editingFinished.connect(lambda: _update_att(int(self.lineXmove.text()), self.settingsStage.moveX))
        self.lineYmove.editingFinished.connect(lambda: _update_att(int(self.lineYmove.text()), self.settingsStage.moveY))
        self.lineZmove.editingFinished.connect(lambda: _update_att(int(self.lineZmove.text()), self.settingsStage.moveZ))

    def widgetMapping(self):
        self.groupMapSize= QGroupBox('Map Settings'); self.groupMapSize.setStyleSheet(""" QGroupBox {font-weight: bold;}  """)
        self.layoutMapSize= QGridLayout(self.groupMapSize)
        self.layoutMain.addWidget(self.groupMapSize)

        self.labelXdistance= QLabel('X'); self.layoutMapSize.addWidget(self.labelXdistance,0,1)
        self.labelXdistance.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        self.labelYdistance= QLabel('Y'); self.layoutMapSize.addWidget(self.labelYdistance,0,2)
        self.labelYdistance.setAlignment(Qt.AlignmentFlag.AlignCenter) 

        self.labelXmap= QLabel('Distance'); self.layoutMapSize.addWidget(self.labelXmap,1,0)
        self.lineXdistance= QLineEdit(); self.layoutMapSize.addWidget(self.lineXdistance,1,1)
        self.lineXdistance.setText('0')
        self.lineXdistance.setValidator(QIntValidator(0, 500))

        self.lineXlandings= QLineEdit(); self.layoutMapSize.addWidget(self.lineXlandings,2,1)
        self.lineXlandings.setText('1')
        self.lineXlandings.setValidator(QIntValidator(0, 500))

        self.labelYmap= QLabel('No. of Landings'); self.layoutMapSize.addWidget(self.labelYmap,2,0)
        self.lineYdistance= QLineEdit(); self.layoutMapSize.addWidget(self.lineYdistance,1,2)
        self.lineYdistance.setText('0')
        self.lineYdistance.setValidator(QIntValidator(0, 100))

        self.lineYlandings= QLineEdit(); self.layoutMapSize.addWidget(self.lineYlandings,2,2)
        self.lineYlandings.setText('1')
        self.lineYlandings.setValidator(QIntValidator(0, 100))

        self.labelPattern= QLabel('Map Pattern'); self.layoutMapSize.addWidget(self.labelPattern,3,0)
        self.comboPattern= QComboBox(); self.layoutMapSize.addWidget(self.comboPattern,3,1,1,2)
        self.comboPattern.addItems(['Snake', 'Straight'])
        self.comboPattern.currentIndexChanged.connect(lambda: _update_att(self.comboPattern.currentText(), self.settingsMap.pattern))

        self.labelMethod= QLabel('Method'); self.layoutMapSize.addWidget(self.labelMethod, 4,0)
        self.comboMap= QComboBox(); self.layoutMapSize.addWidget(self.comboMap, 4,1,1,2)
        self.comboMap.setToolTip('Select the Mapping Method \nNone: No mapping, direct echem measurement \nHopping: Mapping using approach curves \nConstant Distance: Mapping with the tip kept at a constant distance')
        self.comboMap.addItem('None')
        self.comboMap.addItem('Hopping')
        self.comboMap.addItem('Constant Distance')
        self.comboMap.setCurrentIndex(1)
        self.comboMap.currentIndexChanged.connect(lambda: self.stackMap.setCurrentIndex(self.comboMap.currentIndex()))
        self.comboMap.currentIndexChanged.connect(lambda: _update_att(self.comboMap.currentText(), self.settingsMap.mode))
    
        self.lineXdistance.editingFinished.connect(lambda: _update_att(int(self.lineXdistance.text()), self.settingsMap.dX))
        self.lineYdistance.editingFinished.connect(lambda: _update_att(int(self.lineYdistance.text()), self.settingsMap.dY))
        self.lineXlandings.editingFinished.connect(lambda: _update_att(int(self.lineXlandings.text()), self.settingsMap.nX))
        self.lineYlandings.editingFinished.connect(lambda: _update_att(int(self.lineYlandings.text()), self.settingsMap.nY))
   
    def widgetStack(self):

        self.stackMap= QStackedWidget()
        self.layoutMain.addWidget(self.stackMap)
        self.labelDefault= QLabel('No Mapping: Direct measurement')
        self.stackMap.addWidget(self.labelDefault)
        self.stackMap.addWidget(self.widgetHopping())
        self.stackMap.setCurrentIndex(1)

    def widgetHopping(self):
        self.groupApproach= QGroupBox('Approach Settings'); self.groupApproach.setStyleSheet(""" QGroupBox {font-weight: bold;}  """)
        self.layoutGroupApproach= QVBoxLayout(); self.groupApproach.setLayout(self.layoutGroupApproach)
        self.layoutApproach= QGridLayout(); self.layoutGroupApproach.addLayout(self.layoutApproach)
        
        self.labelSpeed= QLabel('Speed'); self.layoutApproach.addWidget(self.labelSpeed,0,0)
        self.labelSpeedUnit= QLabel('\u03bcm/s'); self.layoutApproach.addWidget(self.labelSpeedUnit,0,2)
        
        self.lineSpeed= QLineEdit(); self.layoutApproach.addWidget(self.lineSpeed,0,1)
        self.lineSpeed.setText('1')
        self.lineSpeed.setFixedWidth(110)
        self.lineSpeed.editingFinished.connect(lambda: _update_att(float(self.lineSpeed.text()), self.settingsApproach.speed))

        self.labelRetract= QLabel('Retract by'); self.layoutApproach.addWidget(self.labelRetract,1,0)
        self.labelRetractUnit= QLabel('\u03bcm'); self.layoutApproach.addWidget(self.labelRetractUnit,1,2)
       
        self.lineRetract= QLineEdit(); self.layoutApproach.addWidget(self.lineRetract,1,1)
        self.lineRetract.setText('50')
        self.lineRetract.setFixedWidth(110)
        self.lineRetract.editingFinished.connect(lambda: _update_att(int(self.lineRetract.text()), self.settingsApproach.retract))

        self.labelApproach=QLabel('Stop Criteria'); self.layoutApproach.addWidget(self.labelApproach, 2,0)
        self.comboApproach= QComboBox(); self.layoutApproach.addWidget(self.comboApproach, 2,1)
        self.comboApproach.addItem('Potentiostatic')
        self.comboApproach.addItem('Galvanostatic')
        self.comboApproach.currentIndexChanged.connect(lambda: self.stackApproach.setCurrentIndex(self.comboApproach.currentIndex()))
        self.comboApproach.currentIndexChanged.connect(lambda: _update_att(self.comboApproach.currentText(), self.settingsApproach.stop))

        self.sep1= QFrame(); self.layoutApproach.addWidget(self.sep1,3,0,1,3) 
        self.sep1.setFrameShape(QFrame.Shape.HLine)
        self.sep1.setFrameShadow(QFrame.Shadow.Sunken)

        self.stackApproach= QStackedWidget()
        self.layoutGroupApproach.addWidget(self.stackApproach)
        self.stackApproach.addWidget(self.widgetPot())
        self.stackApproach.addWidget(self.widgetGal())

        return self.groupApproach
    
    def widgetPot(self):
        self.framePot= QFrame()
        self.layoutPot= QGridLayout(self.framePot)
        self.setLayout(self.layoutPot)

        self.labelDeltaE= QLabel('\u00B1 \u0394E'); self.layoutPot.addWidget(self.labelDeltaE,1,0) 
        self.lineDeltaE= QLineEdit(); self.layoutPot.addWidget(self.lineDeltaE,1,1)
        self.lineDeltaE.setText('0.1')
        self.lineDeltaE.editingFinished.connect(lambda: _update_att(float(self.lineDeltaE.text()), self.settingsApproach.dE))

        self.labelV= QLabel("V"); self.layoutPot.addWidget(self.labelV,1,2)
        spacer = QSpacerItem(10, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum); self.layoutPot.addItem(spacer,2,0,2,2)

        return self.framePot
    
    def widgetGal(self):
        self.frameGal= QFrame()
        self.layoutGal= QGridLayout(self.frameGal)
        self.setLayout(self.layoutGal)

        self.labelPotential= QLabel('Potential'); self.layoutGal.addWidget(self.labelPotential,2,0)
        self.labelPotential.setToolTip("Set the potential to apply during approach")
        self.labelPotentialUnit= QLabel('V'); self.layoutGal.addWidget(self.labelPotentialUnit,2,2)
        self.linePotential= QLineEdit(); self.layoutGal.addWidget(self.linePotential,2,1)
        self.linePotential.editingFinished.connect(lambda: _update_att(float(self.linePotential.text()), self.settingsApproach.potential))
        
        self.labelPosI= QLabel('Positive Feedback'); self.layoutGal.addWidget(self.labelPosI,3,0) 
        self.labelPosI.setToolTip("Set stop criteria for positive feedback (Current increase relative to bulk current) by absolute current or a % " \
                                    "\nExample for a bulk current of 1e-6 A with a 200% stop criteria, the tip will stop if the current increases above 2e-6 A ")
        self.linePosI= QLineEdit(); self.layoutGal.addWidget(self.linePosI,3,1)
        self.linePosI.editingFinished.connect(lambda: _update_att(float(self.linePosI.text()), self.settingsApproach.dI_pos))
        self.linePosI.setText('200')
        
        self.comboPosI= QComboBox(); self.layoutGal.addWidget(self.comboPosI,3,2)
        self.comboPosI.addItem('A', 0)
        self.comboPosI.addItem('%', 1)
        self.comboPosI.setCurrentIndex(1)
        self.comboPosI.currentIndexChanged.connect(lambda: _update_att(self.comboPosI.currentText(), self.settingsApproach.dI_pos_unit))

        self.labelNegI= QLabel('Negative Feedback'); self.layoutGal.addWidget(self.labelNegI,4,0) 
        self.labelNegI.setToolTip("Set stop criteria for negative feedback (Current decrease relative to bulk current) by absolute current or a % " \
                                    "\nExample for a bulk current of 1e-6 A with a 75% stop criteria, the tip will stop if the current decreases below 0.25e-6 A ")
        self.lineNegI= QLineEdit(); self.layoutGal.addWidget(self.lineNegI,4,1)
        self.lineNegI.editingFinished.connect(lambda: _update_att(float(self.lineNegI.text()), self.settingsApproach.dI_neg))
        
        self.comboNegI= QComboBox(); self.layoutGal.addWidget(self.comboNegI,4,2)
        self.lineNegI.setText('75')
        self.comboNegI.addItem('A', 0)
        self.comboNegI.addItem('%', 1)
        self.comboNegI.setCurrentIndex(1)
        self.comboNegI.currentIndexChanged.connect(lambda: _update_att(self.comboNegI.currentText(), self.settingsApproach.dI_neg_unit))

        return self.frameGal

if __name__ == '__main__':
    app= QApplication([])
    main= Mapping()
    main.show()
    app.exec()