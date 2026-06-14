from PySide6.QtCore import (Qt, QCoreApplication, QMetaObject)
from PySide6.QtGui import (QPixmap, QRegularExpressionValidator, QDoubleValidator, QIntValidator)
from PySide6.QtWidgets import (QGridLayout, QLabel, QWidget,  QLayout, QLineEdit, QSizePolicy, QSpacerItem,
                               QVBoxLayout, QComboBox, QFrame, QApplication, QMessageBox, QStackedWidget, 
                               QPushButton, QHBoxLayout, QPlainTextEdit, QGroupBox, QListWidget, QListWidgetItem)

import UI_Settings
import numpy as np
import re

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

def _mapLandings(settings: UI_Settings.Mapping):
    Xlandings= np.arange(0, settings.dX*settings.nX, settings.nX )
    Ylandings= np.arange(0, settings.dY*settings.nY, settings.nY )

def _verifyMoveLimit(input:float, currentPos:float, negLim:float, posLim:float)-> bool:
    value= currentPos+input
    if value<=posLim and value>=negLim:
        return True
   
    else:
        warning= QMessageBox(None)
        warning.setText("Invalid Input! Movement Exceeeding Positioners Limits")
        warning.exec()
        return False

def _floatFromStr(text:str)-> float|None:
     
     pattern= r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?'
     coordinates= re.findall(pattern, text)
     return coordinates[0]

sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
sizePolicy.setHorizontalStretch(0)
sizePolicy.setVerticalStretch(0)

class Mapping(QWidget):
      
    def __init__(self):
        super().__init__()
        self.layoutWidget= QVBoxLayout(); self.setLayout(self.layoutWidget)
        self.frame= QFrame(); self.frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Plain)
        self.frame.setSizePolicy(sizePolicy); self.frame.setFixedWidth(300)
        self.layoutFrame= QVBoxLayout(self.frame); self.layoutWidget.addWidget(self.frame)
        
        self.settingsMove= UI_Settings.Move()
        self.settingsMapping= UI_Settings.Mapping()
        self.settingsSECCM= UI_Settings.SECCM()
        #self.settingsSECM= UI_Settings.SECM() Future update

        #Method for UI elements
        self.widgetPositioner()
        self.widgetMapping()
        self.widgetStack()

        #self.setStyleSheet("QLineEdit {border: 1px solid gray; border-radius: 4px; background-color: white; padding: 2px;text-decoration: none;}")
    
    #region: Positioner
    def widgetPositioner(self):
      
        self.groupStage= QGroupBox('Positioners'); self.groupStage.setStyleSheet(""" QGroupBox {font-weight: bold;}  """)
        self.layoutPosition= QGridLayout(self.groupStage)
        self.layoutFrame.addWidget(self.groupStage)

        self.sepPositionSection1= QFrame(); self.layoutPosition.addWidget(self.sepPositionSection1,0,0,1,5) 
        self.sepPositionSection1.setFrameShape(QFrame.Shape.HLine)
        self.sepPositionSection1.setFrameShadow(QFrame.Shadow.Sunken)

        self.labelX= QLabel('X (mm)'); self.layoutPosition.addWidget(self.labelX, 1,1); self.labelX.setStyleSheet("font-weight: bold;")
        self.labelX.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        self.labelY= QLabel('Y (mm)');  self.layoutPosition.addWidget(self.labelY, 1,2); self.labelY.setStyleSheet("font-weight: bold;")
        self.labelY.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        self.labelZ= QLabel('Z (mm)');  self.layoutPosition.addWidget(self.labelZ, 1,3); self.labelZ.setStyleSheet("font-weight: bold;")
        self.labelZ.setAlignment(Qt.AlignmentFlag.AlignCenter) 

        self.sepPositionSection2= QFrame(); self.layoutPosition.addWidget(self.sepPositionSection2,2,0,1,5) 
        self.sepPositionSection2.setFrameShape(QFrame.Shape.HLine)
        self.sepPositionSection2.setFrameShadow(QFrame.Shadow.Sunken)
    
        self.labelMove= QLabel('Move'); self.layoutPosition.addWidget(self.labelMove, 3,0)
        self.labelMove.setToolTip(
        """
        Move the X (mm), Y (mm), and Z (mm) (\u03bcm) positionners relative to the current position. 
            -X-axis: Positive Input-> Move to the right, Negative input-> Move to the left
            -Y-axis: Positive Input-> Move away from you, Negative input-> Move toward you
            -Z-axis: Positive Input-> Move up, Negative input-> Move down
        Positioners displacement cannot exceed their maximum range relative to its current position 
        """)
        
        self.lineXmove= QLineEdit(); self.layoutPosition.addWidget(self.lineXmove, 3,1)
        self.lineXmove.setText('0')
        self.lineXmove.setValidator(QDoubleValidator(-65, 65, 3))
        
        self.lineYmove= QLineEdit();  self.layoutPosition.addWidget(self.lineYmove, 3,2)
        self.lineYmove.setText('0')
        self.lineYmove.setValidator(QDoubleValidator(-65, 65, 3))

        self.lineZmove= QLineEdit(); self.layoutPosition.addWidget(self.lineZmove, 3,3)
        self.lineZmove.setText('0')
        self.lineZmove.setValidator(QDoubleValidator(-25, 25, 3))
   
        self.labelPosition= QLabel('Position'); self.layoutPosition.addWidget(self.labelPosition, 5,0)
        self.labelPosition.setToolTip("Indicate the current position of the X, Y, Z positioners")
        self.labelXpos= QLabel('0');  self.layoutPosition.addWidget(self.labelXpos, 5,1); self.labelXpos.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        self.labelYpos= QLabel('0'); self.layoutPosition.addWidget(self.labelYpos, 5,2); self.labelYpos.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        self.labelZpos= QLabel('0');  self.layoutPosition.addWidget(self.labelZpos, 5,3); self.labelZpos.setAlignment(Qt.AlignmentFlag.AlignCenter) 
       
        self.labelMax= QLabel('Limits'); self.layoutPosition.addWidget(self.labelMax, 6,0)
        self.labelMax.setToolTip("Indicate the maximum range of the X,Y,Z")
        self.labelXmax= QLabel('\u00B165');  self.layoutPosition.addWidget(self.labelXmax, 6,1); self.labelXmax.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        self.labelYmax= QLabel('\u00B150'); self.layoutPosition.addWidget(self.labelYmax, 6,2); self.labelYmax.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        self.labelZmax= QLabel('-25');  self.layoutPosition.addWidget(self.labelZmax, 6,3); self.labelZmax.setAlignment(Qt.AlignmentFlag.AlignCenter) 

        self.sepPositionSection2= QFrame(); self.layoutPosition.addWidget(self.sepPositionSection2,7,0,1,5) 
        self.sepPositionSection2.setFrameShape(QFrame.Shape.HLine)
        self.sepPositionSection2.setFrameShadow(QFrame.Shadow.Sunken)

        self.labelWaypoints= QLabel('Positions'); self.layoutPosition.addWidget(self.labelWaypoints,8,2,1,2)
        self.labelWaypoints.setStyleSheet('font-weight: bold;')
        self.labelWaypoints.setToolTip('A position of interest can be saved by pressing the Save Position Button. \nReturn to the position of interest by selecting it in the list and by pressing the Set Position Button. \nA location name can be edited by double-click or by pressing F2')
        self.labelWaypoints.setAlignment(Qt.AlignmentFlag.AlignCenter) 

        self.labelCommands= QLabel('Commands'); self.layoutPosition.addWidget(self.labelCommands,8,0,1,2)
        self.labelCommands.setStyleSheet('font-weight: bold;')
        self.labelCommands.setAlignment(Qt.AlignmentFlag.AlignCenter) 

        self.sepPositionSection3= QFrame(); self.layoutPosition.addWidget(self.sepPositionSection3,9,0,1,5) 
        self.sepPositionSection3.setFrameShape(QFrame.Shape.HLine)
        self.sepPositionSection3.setFrameShadow(QFrame.Shadow.Sunken)

        self.listWaypoints= QListWidget(); self.layoutPosition.addWidget(self.listWaypoints,10,2,4,2) 
        self.listWaypoints.setFixedWidth(130)

        self.buttonMove= QPushButton('Move'); self.layoutPosition.addWidget(self.buttonMove,10,0,1,2)
        self.buttonReset= QPushButton('Reset'); self.layoutPosition.addWidget(self.buttonReset,13,0,1,2)    
        #self.buttonReset.clicked.connect(self.setWaypoint) 
        self.buttonSave= QPushButton('Save'); self.layoutPosition.addWidget(self.buttonSave,12,0,1,2)
        self.buttonSave.clicked.connect(self.saveWaypoint)    
        self.buttonMoveTo= QPushButton('Move To'); self.layoutPosition.addWidget(self.buttonMoveTo,11,0,1,2)    
                                                                          
        self.lineXmove.editingFinished.connect(lambda: setattr(self.settingsMove, 'moveX', float(self.lineXmove.text())))
        self.lineYmove.editingFinished.connect(lambda: setattr(self.settingsMove, 'moveY', float(self.lineYmove.text())))
        self.lineZmove.editingFinished.connect(lambda: setattr(self.settingsMove, 'moveZ', float(self.lineZmove.text())))

    #region: Mapping
    def widgetMapping(self):
        self.groupMapSize= QGroupBox('Map Settings'); self.groupMapSize.setStyleSheet(""" QGroupBox {font-weight: bold;}  """)
        self.layoutMapSize= QGridLayout(self.groupMapSize)
        self.layoutFrame.addWidget(self.groupMapSize)

        self.labelX= QLabel('X'); self.layoutMapSize.addWidget(self.labelX,0,1)
        self.labelX.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        self.labelY= QLabel('Y'); self.layoutMapSize.addWidget(self.labelY,0,2)
        self.labelY.setAlignment(Qt.AlignmentFlag.AlignCenter) 

        self.labelDistance= QLabel('Distance'); self.layoutMapSize.addWidget(self.labelDistance,1,0)
        self.labelDistance.setToolTip('Distance (\u03bcm) between each landing per direction (X,Y)')

        self.lineXdistance= QLineEdit(); self.layoutMapSize.addWidget(self.lineXdistance,1,1)
        self.lineXdistance.setText('0')
        self.lineXdistance.setValidator(QDoubleValidator(0, 500,1))

        self.lineYdistance= QLineEdit(); self.layoutMapSize.addWidget(self.lineYdistance,1,2)
        self.lineYdistance.setText('0')
        self.lineYdistance.setValidator(QDoubleValidator(0, 500, 1))

        self.labelN= QLabel('Landings'); self.layoutMapSize.addWidget(self.labelN,2,0)
        self.labelN.setToolTip('Number of landings per direction (X,Y)')

        self.lineXlandings= QLineEdit(); self.layoutMapSize.addWidget(self.lineXlandings,2,1)
        self.lineXlandings.setText('1')
        self.lineXlandings.setValidator(QIntValidator(0, 100))

        self.lineYlandings= QLineEdit(); self.layoutMapSize.addWidget(self.lineYlandings,2,2)
        self.lineYlandings.setText('1')
        self.lineYlandings.setValidator(QIntValidator(0, 100))

        self.labelPattern= QLabel('Map Pattern'); self.layoutMapSize.addWidget(self.labelPattern,3,0)
        self.labelPattern.setToolTip('Set the mapping pattern: \n-Snake: Change line at the position of the last measurement \n-Straight: Return to initial position before changing line')

        self.comboPattern= QComboBox(); self.layoutMapSize.addWidget(self.comboPattern,3,1,1,1)
        self.comboPattern.addItems(['Snake', 'Straight'])
        self.comboPattern.currentIndexChanged.connect(lambda: setattr(self.settingsMapping, 'pattern', self.comboPattern.currentText()))
       
        self.labelMethod= QLabel('Method'); self.layoutMapSize.addWidget(self.labelMethod, 4,0)
        self.labelMethod.setToolTip(('Select the Mapping Method \n     - No Map: Echem measurement only \n     - SECCM: Mapping using SECCM \n     - SECM: Mapping or approach curves in SECM '))

        self.comboMap= QComboBox(); self.layoutMapSize.addWidget(self.comboMap, 4,1,1,1)
        self.comboMap.setToolTip(('Select the Mapping Method \n     - No Map: Echem measurement only \n     - SECCM: Mapping using SECCM \n     - SECM: Mapping or approach curves in SECM '))
        self.comboMap.addItem('None')
        self.comboMap.addItem('SECCM')
        self.comboMap.addItem('SECM')
        self.comboMap.setCurrentIndex(0)
        self.comboMap.currentIndexChanged.connect(lambda: self.stackMap.setCurrentIndex(self.comboMap.currentIndex()))
        self.comboMap.currentIndexChanged.connect(lambda: self.groupApproach.setTitle(f'{self.comboMap.currentText()} Settings'))
        self.comboMap.currentIndexChanged.connect(lambda: setattr(self.settingsMapping, 'mode', self.comboMap.currentIndex()))
    
        self.lineXdistance.editingFinished.connect(lambda: setattr(self.settingsMapping, 'dX', float(self.lineXdistance.text())))
        self.lineYdistance.editingFinished.connect(lambda: setattr(self.settingsMapping, 'dY', float(self.lineYdistance.text())))
        self.lineXlandings.editingFinished.connect(lambda: setattr(self.settingsMapping, 'nX', int(self.lineXlandings.text())))
        self.lineYlandings.editingFinished.connect(lambda: setattr(self.settingsMapping, 'nY', int(self.lineYlandings.text())))
   
    #region: Stack utility
    def widgetStack(self):

        self.stackMap= QStackedWidget()
        self.layoutFrame.addWidget(self.stackMap)
        self.labelDefault= QLabel()
        self.stackMap.addWidget(self.labelDefault)
        self.stackMap.addWidget(self.widgetSECCM())
        self.stackMap.setCurrentIndex(0)

    #region: SECCM
    def widgetSECCM(self):
        self.groupApproach= QGroupBox('Approach Settings'); self.groupApproach.setStyleSheet(""" QGroupBox {font-weight: bold;}  """)
        self.layoutGroupApproach= QVBoxLayout(); self.groupApproach.setLayout(self.layoutGroupApproach)
        self.layoutApproach= QGridLayout(); self.layoutGroupApproach.addLayout(self.layoutApproach)
        
        self.labelSpeed= QLabel('Speed'); self.layoutApproach.addWidget(self.labelSpeed,0,0)
        self.labelSpeedUnit= QLabel('\u03bcm/s'); self.layoutApproach.addWidget(self.labelSpeedUnit,0,2)
        
        self.lineSpeed= QLineEdit(); self.layoutApproach.addWidget(self.lineSpeed,0,1)
        self.labelSpeed.setToolTip('Set the piezo speed for tip approach (0.1 to 5 \u03bcm/s). Higher speed (>1 \u03bcm/s), increases the likelihood of a tip crash!')
        self.lineSpeed.setText('1')
        self.lineSpeed.setFixedWidth(110)
        self.lineSpeed.editingFinished.connect(lambda: setattr(self.settingsSECCM, 'speed', float(self.lineSpeed.text())))

        self.labelRetract= QLabel('Retract by'); self.layoutApproach.addWidget(self.labelRetract,1,0)
        self.labelRetract.setToolTip('Set the height at which to retract the piezo (hopping) between landings.')
        self.labelRetractUnit= QLabel('\u03bcm'); self.layoutApproach.addWidget(self.labelRetractUnit,1,2)
       
        self.lineRetract= QLineEdit(); self.layoutApproach.addWidget(self.lineRetract,1,1)
        self.lineRetract.setText('50')
        self.lineRetract.setFixedWidth(110)
        self.lineRetract.editingFinished.connect(lambda: setattr(self.settingsSECCM, 'retract', int(self.lineRetract.text())))   

        self.labelApproach=QLabel('Stop Criteria'); self.layoutApproach.addWidget(self.labelApproach, 2,0)
        self.labelApproach.setToolTip(
            """Choose the method to evaluate the landing during the tip approach:
        - Open Circuit Potential: Stop the tip based on the absolute change in Open Circuit Potential
        - Potentiostatic: Apply a DC potential and stop the tip based in the absolute change in DC current
        - Alternating Current: Apply a AC potential and stop the tip based in the absolute change in AC current""")
            
        
        self.comboApproach= QComboBox(); self.layoutApproach.addWidget(self.comboApproach, 2,1)
        self.comboApproach.addItem('Open Circuit')
        self.comboApproach.addItem('Potentiostatic')
        self.comboApproach.addItem('Alternating Current')
        self.comboApproach.currentIndexChanged.connect(lambda: self.stackApproach.setCurrentIndex(self.comboApproach.currentIndex()))
        self.comboApproach.currentIndexChanged.connect(lambda: setattr(self.settingsSECCM, 'stop', self.comboApproach.currentIndex()))

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
        self.lineE.editingFinished.connect(lambda: setattr(self.settingsSECCM, 'Eapp', float(self.lineE.text())))
        self.label_E_unit= QLabel("V"); self.layoutPot.addWidget(self.label_E_unit,1,2)

        self.labelI= QLabel('Current limit'); self.layoutPot.addWidget(self.labelI,2,0) 
        self.labelI.setToolTip('Set the current threshold in absolute value (positive values only) for stopping the tip approach \nSetting the current too high might cause a tip crash while a current too low might cause false stoppage ')

        self.lineI= QLineEdit(); self.layoutPot.addWidget(self.lineI,2,1)
        self.lineI.setText('1e-3')
        self.lineI.editingFinished.connect(lambda: setattr(self.settingsSECCM, 'Istop', float(self.lineI.text())))
        self.label_I_unit= QLabel("A"); self.layoutPot.addWidget(self.label_I_unit,2,2)
        
        return self.framePot
    
    #region saveWaypoints
    def saveWaypoint(self):
         coordinates= [float(self.labelXpos.text()), float(self.labelYpos.text()), float(self.labelZpos.text())]
         listItem= QListWidgetItem(f'Pos[{self.listWaypoints.count()}]: ({self.labelXpos.text()},{self.labelYpos.text()},{self.labelZpos.text()})')
         listItem.setFlags(listItem.flags() | Qt.ItemFlag.ItemIsEditable) 
         listItem.setData(Qt.ItemDataRole.UserRole, coordinates)
         listItem.setToolTip(f'Saved Position: ({self.labelXpos.text()},{self.labelYpos.text()},{self.labelZpos.text()})')
         self.listWaypoints.addItem(listItem)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            row= self.listWaypoints.currentRow()
            if row != -1:
                item= self.listWaypoints.takeItem(row)
                del item

        else:
            super().keyPressEvent(event) 
    
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