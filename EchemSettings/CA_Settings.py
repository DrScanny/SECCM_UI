import sys
import os
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent) 

from PySide6.QtGui import      (QBrush, QDoubleValidator, QIntValidator)
from PySide6.QtWidgets import  (QApplication, QComboBox, QFrame, QGridLayout, QHBoxLayout, QGroupBox,
                                QLabel, QLayout, QVBoxLayout,  QLineEdit, QSizePolicy, QWidget, QSpacerItem)
import UI_Settings

"""
File for the CA settings of the GUI
"""

#region: Helper functions: _float_or_none, update_att, addWidgetsGrid

def _update_att(value, att)-> None:
     att= value
     print(value)
        
#endregion

class CAset(QWidget):
    tech="CA"

    def __init__(self):
        super().__init__()

        # Instancing DataClass that contain all information required for echem technique
        self.settings= UI_Settings.CA()
        
        # Setting-up GUI elements
        self.setupUi()

        # Setting-up Signal and Slots to update attribute based on 
        self.update_fields()

        # ---------------- Binding & helpers ----------------

    def setupUi(self):

        self.frame= QFrame()
        self.frameLayout= QVBoxLayout(self.frame)
        self.setLayout(self.frameLayout)

        #region: CA settings groupbox widgets
        self.groupCA=QGroupBox('Chronoamperometry'); self.groupCA.setStyleSheet(""" QGroupBox {font-weight: bold;}  """)
        self.layoutCA= QGridLayout(self.groupCA)
        self.frameLayout.addWidget(self.groupCA)

        self.eLabel= QLabel("Apply E"); self.layoutCA.addWidget(self.eLabel,0,0)
        self.eLabel.setToolTip("Set potential step in Voltage vs a Ref or a CE, up to E range limits")
        self.eLabelUnit= QLabel("V vs Ref"); self.layoutCA.addWidget(self.eLabelUnit,0,2)

        self.tLabel= QLabel("For"); self.layoutCA.addWidget(self.tLabel,1,0)
        self.tLabel.setToolTip("Set experiment duration in seconds; up to 86 400 s")
        self.tLabelUnit= QLabel("s"); self.layoutCA.addWidget(self.tLabelUnit,1,2)

        self.dtLabel= QLabel("Every"); self.layoutCA.addWidget(self.dtLabel,2,0)
        self.dtLabel.setToolTip("Record data every X seconds; down to 0.001 s")
        self.ftLabelUnit= QLabel("s"); self.layoutCA.addWidget(self.ftLabelUnit,2,2)

        self.eLine= QLineEdit(); self.layoutCA.addWidget(self.eLine,0,1)
        self.eLine.setText(str(self.settings.potential))
        self.eLine.setValidator(QDoubleValidator(-5, 5, 3))
        
        self.tLine= QLineEdit(); self.layoutCA.addWidget(self.tLine,1,1)
        self.tLine.setText(str(self.settings.duration))
        self.tLine.setValidator(QDoubleValidator(1.00, 86400.00, 3))

        self.dtLine= QLineEdit(); self.layoutCA.addWidget(self.dtLine,2,1)
        self.dtLine.setText(str(self.settings.dt))
        #endregion

        #region: General settings groupbox widgets
        self.groupGen=QGroupBox('General'); self.groupGen.setStyleSheet(""" QGroupBox {font-weight: bold;}  """)
        self.layoutGen= QGridLayout(self.groupGen)
        self.frameLayout.addWidget(self.groupGen)

        self.eRangeLabel= QLabel("E Range"); self.layoutGen.addWidget(self.eRangeLabel, 0,0)
        self.eRangeLabel.setToolTip("Select Potential Range for experiment")

        self.iRangeLabel= QLabel("I Range"); self.layoutGen.addWidget(self.iRangeLabel, 1,0)
        self.iRangeLabel.setToolTip("Select Current Range for experiment")

        self.bandwithLabel= QLabel("Bandwith"); self.layoutGen.addWidget(self.bandwithLabel, 2,0)
        self.bandwithLabel.setToolTip("Bandwith controls the speed of the instrument feedback, higher bandwith reacts quicker at the cost of stability")

        self.eRangeCombo= QComboBox(); self.layoutGen.addWidget(self.eRangeCombo, 0,1)
        #region: eRange combo options
        self.eRangeCombo.addItem("\u00B1 2.5 V", 0)
        self.eRangeCombo.addItem("\u00B1 5 V", 1)
        self.eRangeCombo.addItem("\u00B1 10 V", 2)
        self.eRangeCombo.addItem("Auto", 3)
        #endregion

        self.iRangeCombo= QComboBox(); self.layoutGen.addWidget(self.iRangeCombo, 1,1)
        #region: iRange combo options
        self.iRangeCombo.addItem('Auto', 12 )
        self.iRangeCombo.addItem('100pA',0 )
        self.iRangeCombo.addItem('1nA',1 )
        self.iRangeCombo.addItem('10nA',2 )
        self.iRangeCombo.addItem('100nA',3 )
        self.iRangeCombo.addItem('1uA',4 )
        self.iRangeCombo.addItem('10uA',5 )
        self.iRangeCombo.addItem('100uA',6 )
        self.iRangeCombo.addItem('1mA',7 )
        self.iRangeCombo.addItem('10mA',8 )
        self.iRangeCombo.addItem('100mA',9 )
        self.iRangeCombo.addItem('1A',10 )
        #endregion

        self.bandwithCombo= QComboBox(); self.layoutGen.addWidget(self.bandwithCombo, 2,1)
        self.bandwithCombo.addItems(['1', '2', '3', '4', '5', '6', '7', '8', '9'])
        self.bandwithCombo.setCurrentIndex(7)

        spacer = QSpacerItem(10, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum); self.layoutGen.addItem(spacer,0,2)
        
        self.frameLayout.addStretch()
        #endregion

    def update_fields(self): #Signals to update attribute as widgets are edited
        self.eLine.editingFinished.connect(lambda: _update_att(float(self.eLine.text()), self.settings.potential))
        self.tLine.editingFinished.connect(lambda: _update_att(float(self.tLine.text()), self.settings.duration))
        self.dtLine.editingFinished.connect(lambda: _update_att(float(self.dtLine.text()), self.settings.dt))

        self.iRangeCombo.currentTextChanged.connect(lambda: _update_att(self.iRangeCombo.currentData(), self.settings.iRange))
        self.eRangeCombo.currentTextChanged.connect(lambda: _update_att(self.eRangeCombo.currentData(), self.settings.eRange))
        self.bandwithCombo.currentTextChanged.connect(lambda: _update_att(int(self.bandwithCombo.currentText()), self.settings.bandwith))

if __name__ == '__main__':
    app= QApplication([])
    main= CAset()
    main.show()
    app.exec()
