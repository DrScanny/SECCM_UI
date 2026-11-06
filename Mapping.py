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


class Mapping(QWidget):
      
    def __init__(self):
        super().__init__()
        self.layoutWidget= QVBoxLayout(); self.setLayout(self.layoutWidget)
        self.frame= QFrame(); self.frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Plain)
        self.frame.setFixedWidth(300)
        self.layoutFrame= QVBoxLayout(self.frame); self.layoutWidget.addWidget(self.frame)
        
        self.settingsMove= UI_Settings.Move()
        self.settingsMapping= UI_Settings.Mapping()
        self.settingsSECCM= UI_Settings.SECCM()
        self.settingsSECM= UI_Settings.SECM()

        #Method for UI elements
        self.widgetPositioner()
        self.widgetExperiment()
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

        self.buttonPosition= QPushButton('Pos'); self.layoutPosition.addWidget(self.buttonPosition, 1,0)
        self.labelX= QLabel('X (mm)'); self.layoutPosition.addWidget(self.labelX, 1,1); self.labelX.setStyleSheet("font-weight: bold;")
        self.labelX.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        self.labelY= QLabel('Y (mm)');  self.layoutPosition.addWidget(self.labelY, 1,2); self.labelY.setStyleSheet("font-weight: bold;")
        self.labelY.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        self.labelZ= QLabel('Z (mm)');  self.layoutPosition.addWidget(self.labelZ, 1,3); self.labelZ.setStyleSheet("font-weight: bold;")
        self.labelZ.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        self.labelPz= QLabel('Pz (\u03bcm)');  self.layoutPosition.addWidget(self.labelPz, 1,4); self.labelPz.setStyleSheet("font-weight: bold;")
        self.labelPz.setAlignment(Qt.AlignmentFlag.AlignCenter) 

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

        self.linePzmove= QLineEdit(); self.layoutPosition.addWidget(self.linePzmove, 3,4)
        self.linePzmove.setText('0')
        self.linePzmove.setValidator(QDoubleValidator(-60, 60, 3))
   
        self.labelPosition= QLabel('Position'); self.layoutPosition.addWidget(self.labelPosition, 5,0)
        self.labelPosition.setToolTip("Indicate the current position of the X, Y, Z positioners")
        self.labelXpos= QLabel('0');  self.layoutPosition.addWidget(self.labelXpos, 5,1); self.labelXpos.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        self.labelYpos= QLabel('0'); self.layoutPosition.addWidget(self.labelYpos, 5,2); self.labelYpos.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        self.labelZpos= QLabel('0');  self.layoutPosition.addWidget(self.labelZpos, 5,3); self.labelZpos.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        self.labelPzpos= QLabel('0');  self.layoutPosition.addWidget(self.labelPzpos, 5,4); self.labelPzpos.setAlignment(Qt.AlignmentFlag.AlignCenter) 
       
        self.labelMax= QLabel('Limits'); self.layoutPosition.addWidget(self.labelMax, 6,0)
        self.labelMax.setToolTip("Indicate the maximum range of the X,Y,Z")
        self.labelXmax= QLabel('\u00B165');  self.layoutPosition.addWidget(self.labelXmax, 6,1); self.labelXmax.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        self.labelYmax= QLabel('\u00B150'); self.layoutPosition.addWidget(self.labelYmax, 6,2); self.labelYmax.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        self.labelZmax= QLabel('-25');  self.layoutPosition.addWidget(self.labelZmax, 6,3); self.labelZmax.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        self.labelPzmax= QLabel('100');  self.layoutPosition.addWidget(self.labelPzmax, 6,4); self.labelPzmax.setAlignment(Qt.AlignmentFlag.AlignCenter) 

        self.buttonXYZ= QPushButton('Move XYZ'); self.layoutPosition.addWidget(self.buttonXYZ,7,0,1,3)
        self.buttonXYZ.setToolTip('Move the XYZ stage relative to its current position')
        self.buttonPiezo= QPushButton('Move Pz'); self.layoutPosition.addWidget(self.buttonPiezo,7,3,1,2)
        self.buttonPiezo.setToolTip('Move the piezo to absolute position in the Z axis. Due to the way the piezo is mounted it can only go up from 0 to 100 \u03bcm')

        self.sepPositionSection2= QFrame(); self.layoutPosition.addWidget(self.sepPositionSection2,8,0,1,5) 
        self.sepPositionSection2.setFrameShape(QFrame.Shape.HLine)
        self.sepPositionSection2.setFrameShadow(QFrame.Shadow.Sunken)

        self.labelWaypoints= QLabel('Positions'); self.layoutPosition.addWidget(self.labelWaypoints,9,2,1,2)
        self.labelWaypoints.setStyleSheet('font-weight: bold;')
        self.labelWaypoints.setToolTip('A position of interest can be saved by pressing the Save Position Button. \nReturn to the position of interest by selecting it in the list and by pressing the Set Position Button. \nA location name can be edited by double-click or by pressing F2')
        self.labelWaypoints.setAlignment(Qt.AlignmentFlag.AlignCenter) 

        self.labelCommands= QLabel('Commands'); self.layoutPosition.addWidget(self.labelCommands,9,0,1,2)
        self.labelCommands.setStyleSheet('font-weight: bold;')
        self.labelCommands.setAlignment(Qt.AlignmentFlag.AlignCenter) 

        self.sepPositionSection3= QFrame(); self.layoutPosition.addWidget(self.sepPositionSection3,10,0,1,5) 
        self.sepPositionSection3.setFrameShape(QFrame.Shape.HLine)
        self.sepPositionSection3.setFrameShadow(QFrame.Shadow.Sunken)

        self.listWaypoints= QListWidget(); self.layoutPosition.addWidget(self.listWaypoints,11,2,3,3) 
        self.buttonReset= QPushButton('Reset'); self.layoutPosition.addWidget(self.buttonReset,11,0,1,2)  
        self.buttonReset.setToolTip("Recalibrate and reset the positioners to their original position")  
        self.buttonSave= QPushButton('Save'); self.layoutPosition.addWidget(self.buttonSave,12,0,1,2)
        self.buttonSave.setToolTip("Save a position of interest in the list of waypoints")  
        self.buttonMoveTo= QPushButton('Move To'); self.layoutPosition.addWidget(self.buttonMoveTo,13,0,1,2)    
        self.buttonMoveTo.setToolTip("Return to a position by selecting from the waypoints list")  
                                                                          
        self.lineXmove.editingFinished.connect(lambda: setattr(self.settingsMove, 'moveX', float(self.lineXmove.text())))
        self.lineYmove.editingFinished.connect(lambda: setattr(self.settingsMove, 'moveY', float(self.lineYmove.text())))
        self.lineZmove.editingFinished.connect(lambda: setattr(self.settingsMove, 'moveZ', float(self.lineZmove.text())))

    def widgetExperiment(self):
        self.groupExperiment= QGroupBox('Experiment'); self.groupExperiment.setStyleSheet(""" QGroupBox {font-weight: bold;}  """)
        self.layoutExperiment= QGridLayout(self.groupExperiment)
        self.layoutFrame.addWidget(self.groupExperiment)

        self.labelMethod= QLabel('Method'); self.layoutExperiment.addWidget(self.labelMethod, 4,0)
        self.labelMethod.setToolTip(('Select the Mapping Method \n     - No Map: Echem measurement only \n     - SECCM: Mapping using SECCM \n     - SECM: Mapping or approach curves in SECM '))

        self.comboMap= QComboBox(); self.layoutExperiment.addWidget(self.comboMap, 4,1,1,2)
        self.comboMap.setToolTip(('Select the Mapping Method \n - SECCM: Mapping using SECCM \n     - SECM: Mapping or approach curves in SECM '))
        self.comboMap.addItem('SECM')
        self.comboMap.addItem('SECCM')
        self.comboMap.setCurrentIndex(0)

        self.comboMap.currentIndexChanged.connect(lambda: self.stackMap.setCurrentIndex(self.comboMap.currentIndex()))
        self.comboMap.currentIndexChanged.connect(lambda: setattr(self.settingsMapping, 'mode', self.comboMap.currentIndex()))

        self.buttonMap= QPushButton('Start Map'); self.layoutExperiment.addWidget(self.buttonMap,6,0,1,3) 
        self.buttonMap.setToolTip('Start mapping experiments based on chosen experiment settings and landings coordinates')

    #region: Mapping
    def widgetMapping(self):
        layoutFrame= QGridLayout()

        labelX= QLabel('X'); layoutFrame.addWidget(labelX,0,1)
        labelX.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        labelY= QLabel('Y'); layoutFrame.addWidget(labelY,0,2)
        labelY.setAlignment(Qt.AlignmentFlag.AlignCenter) 

        labelDistance= QLabel('Distance (\u03bcm)'); layoutFrame.addWidget(labelDistance,1,0)
        labelDistance.setToolTip('Distance (\u03bcm) between each landing per direction (X,Y)')

        lineXdistance= QLineEdit(); layoutFrame.addWidget(lineXdistance,1,1)
        lineXdistance.setText('0')
        lineXdistance.setValidator(QDoubleValidator(0, 500,1))

        lineYdistance= QLineEdit(); layoutFrame.addWidget(lineYdistance,1,2)
        lineYdistance.setText('0')
        lineYdistance.setValidator(QDoubleValidator(0, 500, 1))

        labelN= QLabel('Landings'); layoutFrame.addWidget(labelN,2,0)
        labelN.setToolTip('Number of landings per direction (X,Y)')

        lineXlandings= QLineEdit(); layoutFrame.addWidget(lineXlandings,2,1)
        lineXlandings.setText('1')
        lineXlandings.setValidator(QIntValidator(0, 100))

        lineYlandings= QLineEdit(); layoutFrame.addWidget(lineYlandings,2,2)
        lineYlandings.setText('1')
        lineYlandings.setValidator(QIntValidator(0, 100))

        labelPattern= QLabel('Map Pattern'); layoutFrame.addWidget(labelPattern,3,0)
        labelPattern.setToolTip('Set the mapping pattern: \n-Snake: Change line at the position of the last measurement \n-Straight: Return to initial position before changing line')

        comboPattern= QComboBox(); layoutFrame.addWidget(comboPattern,3,1,1,1)
        comboPattern.addItems(['Snake', 'Straight'])
        comboPattern.currentIndexChanged.connect(lambda: setattr(self.settingsMapping, 'pattern', comboPattern.currentIndex()))

        lineXdistance.editingFinished.connect(lambda: setattr(self.settingsMapping, 'dX', float(lineXdistance.text())))
        lineYdistance.editingFinished.connect(lambda: setattr(self.settingsMapping, 'dY', float(lineYdistance.text())))
        lineXlandings.editingFinished.connect(lambda: setattr(self.settingsMapping, 'nX', int(lineXlandings.text())))
        lineYlandings.editingFinished.connect(lambda: setattr(self.settingsMapping, 'nY', int(lineYlandings.text())))

        return layoutFrame
    
    #region: Stack utility
    def widgetStack(self):

        self.stackMap= QStackedWidget()
        self.layoutFrame.addWidget(self.stackMap)
        self.stackMap.addWidget(self.widgetSECM())
        self.stackMap.addWidget(self.widgetSECCM())
        self.stackMap.setCurrentIndex(0)

    def widgetSECCM(self):
        groupSECCM= QGroupBox('SECCM'); groupSECCM.setStyleSheet(""" QGroupBox {font-weight: bold;}  """)
        layoutGroupSECCM= QVBoxLayout(groupSECCM)
        layoutSECCM= QGridLayout(); layoutGroupSECCM.addLayout(layoutSECCM)
        mapping= self.widgetMapping()
        layoutGroupSECCM.addLayout(mapping)
        
        labelSpeed= QLabel('Speed'); layoutSECCM.addWidget(labelSpeed,0,0)
        labelSpeedUnit= QLabel('\u03bcm/s'); layoutSECCM.addWidget(labelSpeedUnit,0,2)
        
        lineSpeed= QLineEdit(); layoutSECCM.addWidget(lineSpeed,0,1)
        labelSpeed.setToolTip('Set the piezo speed for tip approach (0.1 to 5 \u03bcm/s). Higher speed (>1 \u03bcm/s), increases the likelihood of a tip crash!')
        lineSpeed.setText('1')
        lineSpeed.setFixedWidth(110)
        lineSpeed.editingFinished.connect(lambda: setattr(self.settingsSECCM, 'speed', float(lineSpeed.text())))

        labelRetract= QLabel('Retract by'); layoutSECCM.addWidget(labelRetract,1,0)
        labelRetract.setToolTip('Set the height at which to retract the piezo (hopping) between landings.')
        labelRetractUnit= QLabel('\u03bcm'); layoutSECCM.addWidget(labelRetractUnit,1,2)
       
        lineRetract= QLineEdit(); layoutSECCM.addWidget(lineRetract,1,1)
        lineRetract.setText('50')
        lineRetract.setFixedWidth(110)
        lineRetract.editingFinished.connect(lambda: setattr(self.settingsSECCM, 'retract', int(lineRetract.text())))   

        labelApproach=QLabel('Stop Method'); layoutSECCM.addWidget(labelApproach, 2,0)
        labelApproach.setToolTip(
            """Choose the method to evaluate the landing during the tip approach:
        - Open Circuit Potential: Stop the tip based on the absolute change in Open Circuit Potential
        - Potentiostatic: Apply a DC potential and stop the tip based in the absolute change in DC current
        - Alternating Current: Apply a AC potential and stop the tip based in the absolute change in AC current""")
        
        comboSECCM= QComboBox(); layoutSECCM.addWidget(comboSECCM, 2,1)
        comboSECCM.addItem('Open Circuit')
        comboSECCM.addItem('Potentiostatic')
        comboSECCM.addItem('AC')
        comboSECCM.currentIndexChanged.connect(lambda: self.stackSECCM.setCurrentIndex(comboSECCM.currentIndex()))
        comboSECCM.currentIndexChanged.connect(lambda: setattr(self.settingsSECCM, 'stop', comboSECCM.currentIndex()))

        sep1= QFrame(); layoutSECCM.addWidget(sep1,3,0,1,3) 
        sep1.setFrameShape(QFrame.Shape.HLine)
        sep1.setFrameShadow(QFrame.Shadow.Sunken)

        self.stackSECCM= QStackedWidget()
        layoutGroupSECCM.addWidget(self.stackSECCM)
        self.stackSECCM.addWidget(self.SECCM_OCP())
        self.stackSECCM.addWidget(self.SECCM_Pot())
        self.stackSECCM.addWidget(self.SECCM_AC())

        layoutGroupSECCM.addStretch()

        return groupSECCM
    
    def SECCM_OCP(self):
        frame= QFrame()
        return frame
    
    def SECCM_Pot(self):
        frame= QFrame(); 
        layoutFrame= QGridLayout(frame); self.setLayout(layoutFrame)
       
        labelE= QLabel('Applied Potential'); layoutFrame.addWidget(labelE,1,0) 
        labelE.setToolTip('Set the applied potential (negative or positive values) during the tip approach to generate a current when landing on a sample')

        lineE= QLineEdit(); layoutFrame.addWidget(lineE,1,1)
        lineE.setText('0.1')
        lineE.editingFinished.connect(lambda: setattr(self.settingsSECCM, 'Eapp', float(lineE.text())))
        label_E_unit= QLabel("V"); layoutFrame.addWidget(label_E_unit,1,2)

        labelI= QLabel('Current limit'); layoutFrame.addWidget(labelI,2,0) 
        labelI.setToolTip('Set the current threshold in absolute value (positive values only) for stopping the tip approach \nSetting the current too high might cause a tip crash while a current too low might cause false stoppage ')

        labelIrange= QLabel('I range'); layoutFrame.addWidget(labelIrange,3,0) 
        labelIrange.setToolTip('Choose Irange closest to the expected current of your electrode')

        lineI= QLineEdit(); layoutFrame.addWidget(lineI,2,1)
        lineI.setText('1e-3')
        lineI.editingFinished.connect(lambda: setattr(self.settingsSECCM, 'Istop', float(lineI.text())))
        label_I_unit= QLabel("A"); layoutFrame.addWidget(label_I_unit,2,2)

        iRangeCombo= QComboBox(); layoutFrame.addWidget(iRangeCombo, 3,1)
        iRangeCombo.currentIndexChanged.connect(lambda: setattr(self.settingsSECCM, 'iRange', iRangeCombo.currentIndex()))
        iRangeCombo.addItems(('100pA', '1nA', '10nA', '100nA', '1uA', '10uA', '100uA', '1mA'))
      
        return frame
    
    def SECCM_AC(self):
        frame= QFrame(); 
        layoutFrame= QGridLayout(frame); self.setLayout(layoutFrame)
       
        labelE= QLabel('AC approach curve setting placeholder'); layoutFrame.addWidget(labelE,1,0) 
        labelE.setToolTip('Set the applied potential (negative or positive values) during the tip approach to generate a current when landing on a sample')
      
        return frame
    
    #endregion

    #region:SECM
    def widgetSECM(self):
        groupSECM= QGroupBox('SECM'); groupSECM.setStyleSheet(""" QGroupBox {font-weight: bold;}  """)
        layoutGroupSECM= QVBoxLayout(groupSECM)
        layoutSECM= QGridLayout(); layoutGroupSECM.addLayout(layoutSECM)
        
        labelExperiment=QLabel('Measurement'); layoutSECM.addWidget(labelExperiment, 1,0)
        labelExperiment.setToolTip(
            """Choose the method to evaluate the landing during the tip approach:
        - Open Circuit Potential: Stop the tip based on the absolute change in Open Circuit Potential
        - Potentiostatic: Apply a DC potential and stop the tip based in the absolute change in DC current
        - Alternating Current: Apply a AC potential and stop the tip based in the absolute change in AC current""")
        
        comboExperiment= QComboBox(); layoutSECM.addWidget(comboExperiment, 1,1,1,2)
        comboExperiment.addItem('Approach curve')
        comboExperiment.addItem('Constant Distance Map')
        comboExperiment.currentIndexChanged.connect(lambda: self.stackApproach.setCurrentIndex(comboExperiment.currentIndex()))
        comboExperiment.currentIndexChanged.connect(lambda: setattr(self.settingsSECM, 'experiment', comboExperiment.currentIndex()))

        sep1= QFrame(); layoutSECM.addWidget(sep1, 4,0,1,3) 
        sep1.setFrameShape(QFrame.Shape.HLine)
        sep1.setFrameShadow(QFrame.Shadow.Sunken)

        self.stackApproach= QStackedWidget()
        layoutGroupSECM.addWidget(self.stackApproach)
        self.stackApproach.addWidget(self.SECM_approach())
        self.stackApproach.addWidget(self.SECM_mapConstant())

        layoutGroupSECM.addStretch()
      
        return groupSECM
    
    def SECM_approach(self):
        frame= QFrame()
        layoutFrame= QGridLayout(frame)
        self.setLayout(self.layoutFrame)

        labelPositioner= QLabel('Positioner'); layoutFrame.addWidget(labelPositioner, 0,0)
        labelPositioner.setToolTip(
            """Choose a positioner to perform approach curve 
                - Z-Stage is for a coarse approach curve used to determine approximate distance to substrate 
                - Piezo is for a finer approach curve when close to substrate (Max range of 100 \u03bcm)
            """)
                                  
        comboPositioner= QComboBox(); layoutFrame.addWidget(comboPositioner, 0,1,1,2)
        comboPositioner.addItem('Z-stage')
        comboPositioner.addItem('Piezo')
        comboPositioner.currentIndexChanged.connect(lambda: setattr(self.settingsSECM, 'positioner', comboPositioner.currentIndex()))

        labelPotential= QLabel('E (V)'); layoutFrame.addWidget(labelPotential,1,0)
        labelPotential.setToolTip("Set the potential to apply during SECM approach")
        linePotential= QLineEdit(); layoutFrame.addWidget(linePotential,1,1)
        linePotential.setText('0.1')
        linePotential.editingFinished.connect(lambda: setattr(self.settingsSECM, 'Eapp', float(linePotential.text())))

        labelIrange= QLabel('I range'); layoutFrame.addWidget(labelIrange,2,0) 
        labelIrange.setToolTip('Choose Irange closest to the expected current of your electrode')
        iRangeCombo= QComboBox(); layoutFrame.addWidget(iRangeCombo, 2,1)
        iRangeCombo.setFixedWidth(80)
        iRangeCombo.setCurrentIndex(2)
        iRangeCombo.currentIndexChanged.connect(lambda: setattr(self.settingsSECM, 'iRange', iRangeCombo.currentIndex()))
        iRangeCombo.addItems(('100pA', '1nA', '10nA', '100nA', '1uA', '10uA', '100uA', '1mA'))
        

        labelSpeed= QLabel('<i>v</i> (\u03bcm/s)'); layoutFrame.addWidget(labelSpeed,3,0)
        labelSpeed.setToolTip('Set the speed for tip approach (0.1 to 10 \u03bcm/s). Higher speed for coarse approach (>1 \u03bcm/s), increases the likelihood of a tip crash!')
        lineSpeed= QLineEdit(); layoutFrame.addWidget(lineSpeed,3,1)
        lineSpeed.setText('1')
        lineSpeed.editingFinished.connect(lambda: setattr(self.settingsSECM, 'speed', float(lineSpeed.text())))

        labelStop= QLabel('Stop'); layoutFrame.addWidget(labelStop,4,0) 
        labelStop.setToolTip("""Set stop criteria for positive and negative feedback
                             1- Relative current change: For a bulk current of 1e-6 A with a 200% stop criteria, the tip will stop if the current increases above 2e-6 A 
                             2- Absolute change in current: For a bulk current of 1e-6 A with \u0394I of 0.5e-6 A, the tip will stop if the current increases above 1.5e-6 A
                             3- Current limit: Regardless of the bulk current, the tip will stop if the measured current is outside the indicated range""")
        
        comboStop= QComboBox(); layoutFrame.addWidget(comboStop,4,1)
        comboStop.setFixedWidth(90)
        comboStop.addItems(('\u0394I (%)', '\u0394I (A)', 'lim I (A)'))
        comboStop.currentIndexChanged.connect(lambda: setattr(self.settingsSECM, 'limUnit', comboStop.currentIndex()))
        
        labelPosI= QLabel('Positive'); layoutFrame.addWidget(labelPosI,5,0) 
        linePosI= QLineEdit(); layoutFrame.addWidget(linePosI,5,1)
        linePosI.editingFinished.connect(lambda: setattr(self.settingsSECM, 'limPos', float(linePosI.text())))
        linePosI.setText('200'); linePosI.setFixedWidth(60)
        
        labelNegI= QLabel('Negative'); layoutFrame.addWidget(labelNegI,5,2) 
        lineNegI= QLineEdit(); layoutFrame.addWidget(lineNegI,5,3)
        lineNegI.editingFinished.connect(lambda: setattr(self.settingsSECM, 'limNeg', float(lineNegI.text())))
        lineNegI.setText('50'); lineNegI.setFixedWidth(60)

        labelSpacer= QLabel(); layoutFrame.addWidget(labelSpacer,6,0) 

        return frame
    
    def SECM_mapConstant(self):
        frame= QFrame()
        layoutFrame= QVBoxLayout(frame); self.setLayout(self.layoutFrame)
        mapping= self.widgetMapping(); layoutFrame.addLayout(mapping)
        layoutSECMsettings= QGridLayout(); layoutFrame.addLayout(layoutSECMsettings)

        sep1= QFrame(); layoutSECMsettings.addWidget(sep1, 0,0,1,3) 
        sep1.setFrameShape(QFrame.Shape.HLine)
        sep1.setFrameShadow(QFrame.Shadow.Sunken)

        labelPotential= QLabel('E (V)'); layoutSECMsettings.addWidget(labelPotential,1,0,1,1)
        labelPotential.setToolTip("Set the potential to apply during SECM mapping")
        linePotential= QLineEdit(); layoutSECMsettings.addWidget(linePotential,1,1)
        linePotential.setFixedWidth(60); linePotential.setText('0.1')
        linePotential.editingFinished.connect(lambda: setattr(self.settingsSECM, 'Eapp', float(linePotential.text())))

        labelIrange= QLabel('I range'); layoutSECMsettings.addWidget(labelIrange,2,0) 
        labelIrange.setToolTip('Choose Irange closest to the expected current of your electrode')
        iRangeCombo= QComboBox(); layoutSECMsettings.addWidget(iRangeCombo, 2,1)
        iRangeCombo.setFixedWidth(80)
        iRangeCombo.currentIndexChanged.connect(lambda: setattr(self.settingsSECM, 'iRange', iRangeCombo.currentIndex()))
        iRangeCombo.addItems(('100pA', '1nA', '10nA', '100nA', '1uA', '10uA', '100uA', '1mA'))
        iRangeCombo.setCurrentIndex(1)
        
        labelSpeed= QLabel('<i>v<i> (\u03bcm/s)'); layoutSECMsettings.addWidget(labelSpeed,3,0)
        labelSpeed.setToolTip('Set speed for mapping in XY')
        lineSpeed= QLineEdit(); layoutSECMsettings.addWidget(lineSpeed,3,1)
        lineSpeed.setText('5')
        lineSpeed.setFixedWidth(60)
        lineSpeed.editingFinished.connect(lambda: setattr(self.settingsMapping, 'speed', float(lineSpeed.text())))

        labelWait= QLabel('Wait (s)'); layoutSECMsettings.addWidget(labelWait,4,0)
        labelWait.setToolTip('Waiting time before acquiring echem measurement')
        lineWait= QLineEdit(); layoutSECMsettings.addWidget(lineWait,4,1)
        lineWait.setText('1')
        lineWait.setFixedWidth(60)
        lineWait.editingFinished.connect(lambda: setattr(self.settingsMapping, 'wait', float(lineWait.text())))

        labelN= QLabel('N data'); layoutSECMsettings.addWidget(labelN,4,2)
        labelN.setToolTip('Number of echem datapoints to average')
        lineN= QLineEdit(); layoutSECMsettings.addWidget(lineN,4,3)
        lineN.setText('5')
        lineN.setFixedWidth(60)
        lineWait.editingFinished.connect(lambda: setattr(self.settingsMapping, 'Ndata', int(lineN.text())))

        return frame
    
    #endregion
    
    def mapCoordinates(self):

        map=[]

        if self.settingsMapping.dX==0 and self.settingsMapping.dY==0:
            return setattr(self.settingsMapping, 'map', [[0,0]])
        
        else:
            Xlandings= np.arange(0, self.settingsMapping.dX*self.settingsMapping.nX+1, self.settingsMapping.dX)
            Ylandings= np.arange(0, self.settingsMapping.dY*self.settingsMapping.nY+1, self.settingsMapping.dY)

            if self.settingsMapping.pattern== 0:
                
                for idx, y in enumerate(Ylandings):
                    if idx % 2 == 0:
                        for x in Xlandings:
                            map.append([x,y])
                            
                    else:
                        for x in reversed(Xlandings):
                            map.append([x,y])

            elif self.settingsMapping.pattern== 1:

                for y in Ylandings:
                    for x in Xlandings:
                        map.append([x,y])

            setattr(self.settingsMapping, 'map', map)
        
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
  

if __name__ == '__main__':
    app= QApplication([])
    main= Mapping()
    main.show()
    app.exec()