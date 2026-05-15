from dataclasses import dataclass
import numpy as np

from PySide6.QtCore import (Qt, QCoreApplication, QMetaObject)
from PySide6.QtGui import (QRegularExpressionValidator, QDoubleValidator, QIntValidator)
from PySide6.QtWidgets import (QGridLayout, QLabel, QWidget,  QLayout, QLineEdit, QSizePolicy, QSpacerItem,
                               QVBoxLayout, QComboBox, QFrame, QApplication, QMessageBox, QStackedWidget,
                               QPushButton, QHBoxLayout, QPlainTextEdit, QGroupBox)

import UI_Settings
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

def _mapLandings(settings: UI_Settings.Map):
    Xlandings= np.arange(0, settings.dX*settings.nX, settings.nX )
    Ylandings= np.arange(0, settings.dY*settings.nY, settings.nY )

def _update_att(value, att)-> None:
     att= value
     print(att, value)

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

        self.settingsStage= UI_Settings.Stage()
        self.settingsMap= UI_Settings.Map()
        self.settingsApproach= UI_Settings.SECCM()
        
        self.widgetPos()
        self.widgetMapping()
        self.widgetStack()

        #self.setStyleSheet("QLineEdit {border: 1px solid gray; border-radius: 4px; background-color: white; padding: 2px;text-decoration: none;}")
    
    def widgetPos(self):
      
        self.groupStage= QGroupBox('Positioners movement'); self.groupStage.setStyleSheet(""" QGroupBox {font-weight: bold;}  """)
        #self.framePosition.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Plain)
        self.layoutPosition= QGridLayout(self.groupStage)
        self.layoutMain.addWidget(self.groupStage)

        self.sepPositionSection1= QFrame(); self.layoutPosition.addWidget(self.sepPositionSection1,0,0,1,5) 
        self.sepPositionSection1.setFrameShape(QFrame.Shape.HLine)
        self.sepPositionSection1.setFrameShadow(QFrame.Shadow.Sunken)

        self.labelPiezo= QLabel("Stages"); self.layoutPosition.addWidget(self.labelPiezo,1,0,1,1); self.labelPiezo.setStyleSheet("font-weight: bold;")
        self.sepPositionSection2= QFrame(); self.layoutPosition.addWidget(self.sepPositionSection2,2,0,1,5) 
        self.sepPositionSection2.setFrameShape(QFrame.Shape.HLine)
        self.sepPositionSection2.setFrameShadow(QFrame.Shadow.Sunken)
    
        self.labelMove= QLabel('Move'); self.layoutPosition.addWidget(self.labelMove, 3,0)
        self.labelMove.setToolTip("Move the positionner in X, Y axis by up to (-)99 999 \u03bcm at a time and the Z axis by up to (-)1 000 \u03bcm ")

        self.labelPosition= QLabel('Current'); self.layoutPosition.addWidget(self.labelPosition, 4,0)
        self.labelPosition.setToolTip("Indicate the current absolute position in X, Y, Z axis")

        self.labelMax= QLabel('Limits'); self.layoutPosition.addWidget(self.labelMax, 5,0)
        self.labelMax.setToolTip("Indicate the stage limits in X, Y, Z axis")

        self.labelX= QLabel('X'); self.layoutPosition.addWidget(self.labelX, 1,1); self.labelX.setStyleSheet("font-weight: bold;")
        self.labelX.setAlignment(Qt.AlignmentFlag.AlignCenter) 

        self.lineXmove= QLineEdit(); self.layoutPosition.addWidget(self.lineXmove, 3,1)
        self.lineXmove.setText('0')
        self.lineXmove.setValidator(QIntValidator(-99999, 99999))

        self.labelXpos= QLabel('0 \u03bcm');  self.layoutPosition.addWidget(self.labelXpos, 4,1)
        self.labelXmax= QLabel('X');  self.layoutPosition.addWidget(self.labelXmax, 5,1)

        self.labelY= QLabel('Y');  self.layoutPosition.addWidget(self.labelY, 1,2); self.labelY.setStyleSheet("font-weight: bold;")
        self.labelY.setAlignment(Qt.AlignmentFlag.AlignCenter) 

        self.lineYmove= QLineEdit();  self.layoutPosition.addWidget(self.lineYmove, 3,2)
        self.lineYmove.setText('0')
        self.lineYmove.setValidator(QIntValidator(-99999, 99999))

        self.labelYpos= QLabel('0 \u03bcm'); self.layoutPosition.addWidget(self.labelYpos, 4,2)
        self.labelYmax= QLabel('Y'); self.layoutPosition.addWidget(self.labelYmax, 5,2)

        self.labelZ= QLabel('Z');  self.layoutPosition.addWidget(self.labelZ, 1,3); self.labelZ.setStyleSheet("font-weight: bold;")
        self.labelZ.setAlignment(Qt.AlignmentFlag.AlignCenter) 

        self.lineZmove= QLineEdit(); self.layoutPosition.addWidget(self.lineZmove, 3,3)
        self.lineZmove.setText('0')
        self.lineXmove.setValidator(QIntValidator(-1000, 1000))
    
        self.labelZpos= QLabel('0 \u03bcm');  self.layoutPosition.addWidget(self.labelZpos, 4,3)
        self.labelZmax= QLabel('Z');  self.layoutPosition.addWidget(self.labelZmax, 5,3)


        self.buttonMove= QPushButton('Move'); self.layoutPosition.addWidget(self.buttonMove,6,0,1,2)
        self.buttonStop= QPushButton('Stop'); self.layoutPosition.addWidget(self.buttonStop,6,2,1,2)

        self.labelPiezo= QLabel("Piezo"); self.layoutPosition.addWidget(self.labelPiezo,8,0,1,2); self.labelPiezo.setStyleSheet("font-weight: bold;")
        self.sepPositionSection3= QFrame(); self.layoutPosition.addWidget(self.sepPositionSection3,7,0,1,5) 
        self.sepPositionSection3.setFrameShape(QFrame.Shape.HLine)
        self.sepPositionSection3.setFrameShadow(QFrame.Shadow.Sunken)

        self.labelPiezoMove= QLabel('Move'); self.layoutPosition.addWidget(self.labelPiezoMove,11,0)
        self.labelPiezoPos= QLabel('Current'); self.layoutPosition.addWidget(self.labelPiezoPos,12,0)
        self.labelPiezoMax= QLabel('Limit'); self.layoutPosition.addWidget(self.labelPiezoMax,13,0)

        self.sepPositionSection4= QFrame(); self.layoutPosition.addWidget(self.sepPositionSection4,10,0,1,5) 
        self.sepPositionSection4.setFrameShape(QFrame.Shape.HLine) 
        self.sepPositionSection4.setFrameShadow(QFrame.Shadow.Sunken)

        self.linePiezo= QLineEdit(); self.layoutPosition.addWidget(self.linePiezo, 11,1) 
        self.labelPiezoPosValue= QLabel('0 \u03bcm'); self.layoutPosition.addWidget(self.labelPiezoPosValue, 12,1) 
        self.linePiezoMaxValue= QLabel('60 \u03bcm'); self.layoutPosition.addWidget(self.linePiezoMaxValue, 13,1) 

        self.buttonPiezoMove= QPushButton('Move'); self.layoutPosition.addWidget(self.buttonPiezoMove,11,2,1,2)
        self.buttonPiezoRelease= QPushButton('Release'); self.layoutPosition.addWidget(self.buttonPiezoRelease,12,2,1,2)

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
        self.labelXmap.setToolTip('Distance (\u03bcm) between each landing per direction (X,Y)')
        self.lineXdistance= QLineEdit(); self.layoutMapSize.addWidget(self.lineXdistance,1,1)
        self.lineXdistance.setText('0')
        self.lineXdistance.setValidator(QIntValidator(0, 500))

        self.lineXlandings= QLineEdit(); self.layoutMapSize.addWidget(self.lineXlandings,2,1)
        self.lineXlandings.setText('1')
        self.lineXlandings.setValidator(QIntValidator(0, 500))

        self.labelYmap= QLabel('No. of Landings'); self.layoutMapSize.addWidget(self.labelYmap,2,0)
        self.labelYmap.setToolTip('Number of landings per direction (X,Y)')
        self.lineYdistance= QLineEdit(); self.layoutMapSize.addWidget(self.lineYdistance,1,2)
        self.lineYdistance.setText('0')
        self.lineYdistance.setValidator(QIntValidator(0, 100))

        self.lineYlandings= QLineEdit(); self.layoutMapSize.addWidget(self.lineYlandings,2,2)
        self.lineYlandings.setText('1')
        self.lineYlandings.setValidator(QIntValidator(0, 100))

        self.labelPattern= QLabel('Map Pattern'); self.layoutMapSize.addWidget(self.labelPattern,3,0)
        self.labelPattern.setToolTip('Set the mapping pattern: \n-Snake: Change line at the position of the last measurement \n-Straight: Return to initial position before changing line')

        self.comboPattern= QComboBox(); self.layoutMapSize.addWidget(self.comboPattern,3,1,1,2)
        self.comboPattern.addItems(['Snake', 'Straight'])
        self.comboPattern.currentIndexChanged.connect(lambda: _update_att(self.comboPattern.currentText(), self.settingsMap.pattern))

        self.labelMethod= QLabel('Method'); self.layoutMapSize.addWidget(self.labelMethod, 4,0)
        self.labelMethod.setToolTip(('Select the Mapping Method \nNo Map: Echem measurement only \nSECCM: Mapping using SECCM \nSECM: Mapping or approach curves in SECM '))

        self.comboMap= QComboBox(); self.layoutMapSize.addWidget(self.comboMap, 4,1,1,2)
        self.comboMap.setToolTip('Select the Mapping Method \nNo Map: No mapping, direct echem measurement \nSECCM Hopping: Mapping in SECCM by approaching tip \nSECM Hopping: Mapping in SECM using approach curves \nConstant Distance: Mapping with the tip kept at a constant distance')
        self.comboMap.addItem('None')
        self.comboMap.addItem('SECCM')
        self.comboMap.addItem('SECM')
        self.comboMap.setCurrentIndex(0)
        self.comboMap.currentIndexChanged.connect(lambda: self.stackMap.setCurrentIndex(self.comboMap.currentIndex()))
        self.comboMap.currentIndexChanged.connect(lambda: self.groupApproach.setTitle(f'{self.comboMap.currentText()} Settings'))
        self.comboMap.currentIndexChanged.connect(lambda: _update_att(self.comboMap.currentText(), self.settingsMap.mode))
    
        self.lineXdistance.editingFinished.connect(lambda: _update_att(int(self.lineXdistance.text()), self.settingsMap.dX))
        self.lineYdistance.editingFinished.connect(lambda: _update_att(int(self.lineYdistance.text()), self.settingsMap.dY))
        self.lineXlandings.editingFinished.connect(lambda: _update_att(int(self.lineXlandings.text()), self.settingsMap.nX))
        self.lineYlandings.editingFinished.connect(lambda: _update_att(int(self.lineYlandings.text()), self.settingsMap.nY))
   
    def widgetStack(self):

        self.stackMap= QStackedWidget()
        self.layoutMain.addWidget(self.stackMap)
        self.labelDefault= QLabel()
        self.stackMap.addWidget(self.labelDefault)
        self.stackMap.addWidget(self.widgetHopping())
        self.stackMap.setCurrentIndex(0)

    def widgetHopping(self):
        self.groupApproach= QGroupBox('Approach Settings'); self.groupApproach.setStyleSheet(""" QGroupBox {font-weight: bold;}  """)
        self.layoutGroupApproach= QVBoxLayout(); self.groupApproach.setLayout(self.layoutGroupApproach)
        self.layoutApproach= QGridLayout(); self.layoutGroupApproach.addLayout(self.layoutApproach)
        
        self.labelSpeed= QLabel('Speed'); self.layoutApproach.addWidget(self.labelSpeed,0,0)
        self.labelSpeedUnit= QLabel('\u03bcm/s'); self.layoutApproach.addWidget(self.labelSpeedUnit,0,2)
        
        self.lineSpeed= QLineEdit(); self.layoutApproach.addWidget(self.lineSpeed,0,1)
        self.labelSpeed.setToolTip('Set the piezo speed for tip approach (0.1 to 5 \u03bcm/s). Higher speed (>1 \u03bcm/s) can cause tip crash!')
        self.lineSpeed.setText('1')
        self.lineSpeed.setFixedWidth(110)
        self.lineSpeed.editingFinished.connect(lambda: _update_att(float(self.lineSpeed.text()), self.settingsApproach.speed))

        self.labelRetract= QLabel('Retract by'); self.layoutApproach.addWidget(self.labelRetract,1,0)
        self.labelRetract.setToolTip('Set the height at which to retract the piezo (hopping) between landings.')
        self.labelRetractUnit= QLabel('\u03bcm'); self.layoutApproach.addWidget(self.labelRetractUnit,1,2)
       
        self.lineRetract= QLineEdit(); self.layoutApproach.addWidget(self.lineRetract,1,1)
        self.lineRetract.setText('50')
        self.lineRetract.setFixedWidth(110)
        self.lineRetract.editingFinished.connect(lambda: _update_att(int(self.lineRetract.text()), self.settingsApproach.retract))

        self.labelApproach=QLabel('Stop Criteria'); self.layoutApproach.addWidget(self.labelApproach, 2,0)
        self.labelApproach.setToolTip(
            """Choose the method to evaluate the landing during the tip approach:
Open Circuit Potential -> Absolute change in Open Circuit Potential
Potentiostatic -> Apply a DC potential and determine the change in current, absolute (\u0394A) or relative (%)
Alternating Current -> Apply an AC potential and determine the change in current, absolute (\u0394A) or relative (%)
            """)
        
        self.comboApproach= QComboBox(); self.layoutApproach.addWidget(self.comboApproach, 2,1)
        self.comboApproach.addItem('Open Circuit')
        self.comboApproach.addItem('Potentiostatic')
        self.comboApproach.currentIndexChanged.connect(lambda: self.stackApproach.setCurrentIndex(self.comboApproach.currentIndex()))
        self.comboApproach.currentIndexChanged.connect(lambda: _update_att(self.comboApproach.currentText(), self.settingsApproach.stop))

        self.sep1= QFrame(); self.layoutApproach.addWidget(self.sep1,3,0,1,3) 
        self.sep1.setFrameShape(QFrame.Shape.HLine)
        self.sep1.setFrameShadow(QFrame.Shadow.Sunken)

        self.stackApproach= QStackedWidget()
        self.layoutGroupApproach.addWidget(self.stackApproach)
        self.stackApproach.addWidget(self.SECCM_OCP())
        self.stackApproach.addWidget(self.SECCM_Pot())

        return self.groupApproach
    
    
    def SECCM_OCP(self):
        self.framePot= QFrame()
        return self.framePot
    
    def SECCM_Pot(self):
        self.framePot= QFrame()
        self.layoutPot= QGridLayout(self.framePot)
        self.setLayout(self.layoutPot)

        self.labelE= QLabel('Applied Potential'); self.layoutPot.addWidget(self.labelE,1,0) 
        self.labelE.setToolTip('Set the applied potential (negative or positive values) during the tip approach to generate a current when landing on a sample')

        self.lineE= QLineEdit(); self.layoutPot.addWidget(self.lineE,1,1)
        self.lineE.setText('0.1')
        self.lineE.editingFinished.connect(lambda: _update_att(float(self.lineE.text()), self.settingsApproach.Eapp))
        self.label_E_unit= QLabel("V"); self.layoutPot.addWidget(self.label_E_unit,1,2)

        self.labelI= QLabel('Current limit'); self.layoutPot.addWidget(self.labelI,2,0) 
        self.labelI.setToolTip('Set the current threshold in absolute value (positive values only) for stopping the tip approach \nSetting the current too high might cause a tip crash while a current too low might cause false stoppage ')

        self.lineI= QLineEdit(); self.layoutPot.addWidget(self.lineI,2,1)
        self.lineI.setText('1e-3')
        self.lineI.editingFinished.connect(lambda: _update_att(float(self.lineI.text()), self.settingsApproach.Istop))
        self.label_I_unit= QLabel("A"); self.layoutPot.addWidget(self.label_I_unit,2,2)
        
        return self.framePot
    
    """
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
    """

if __name__ == '__main__':
    app= QApplication([])
    main= Mapping()
    main.show()
    app.exec()