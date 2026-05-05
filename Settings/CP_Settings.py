import sys
import os
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent) 

from PySide6.QtGui import      (QBrush, QDoubleValidator, QIntValidator)
from PySide6.QtWidgets import  (QApplication, QComboBox, QFrame, QGridLayout, QLineEdit, QSpacerItem,
                                QHBoxLayout, QLabel, QVBoxLayout,QSizePolicy, QWidget, QGroupBox)
import SECCM_Settings
                                 

#region: Helper functions:  _update_att, _addWidgetsGrid

def _update_att(value, att)-> None:
        att= value
        print(att)

#endregion

class CPset(QWidget):
    tech="CP"

    def __init__(self):
        super().__init__()

        self.frame= QFrame()
        self.frameLayout= QVBoxLayout(self.frame)
        self.setLayout(self.frameLayout)

        # Instantiating CP settings dataclass
        self.settings= SECCM_Settings.CPsettings()

        # Setting-up GUI elements
        self.setupUi()

        # Setting-up Signal and Slots to update attribute based on 
        self.update_fields()

    def setupUi(self):

        self.groupCP=QGroupBox('Chronopotentiometry'); self.groupCP.setStyleSheet(""" QGroupBox {font-weight: bold;}  """)
        self.layoutCP= QGridLayout(self.groupCP)
        self.frameLayout.addWidget(self.groupCP)

        #region: All widgets from column 0 (Mostly labels)
        self.iLabel= QLabel("Set I"); self.layoutCP.addWidget(self.iLabel,0,0)
        self.iLabel.setToolTip("Set current step in Ampere; up to \u00B11 A")
        self.iLabelUnit= QLabel("A"); self.layoutCP.addWidget(self.iLabelUnit,0,2)
        
        self.tLabel= QLabel("for"); self.layoutCP.addWidget(self.tLabel,1,0)
        self.tLabel.setToolTip("Set experiment duration in seconds; up to 86 400 s")
        self.tLabelUnit= QLabel("s"); self.layoutCP.addWidget(self.tLabelUnit,1,2)

        self.dtLabel= QLabel("Every"); self.layoutCP.addWidget(self.dtLabel,2,0)
        self.dtLabel.setToolTip("Record data every X seconds; down to 0.001 s")
        self.dtLabelUnit= QLabel("s"); self.layoutCP.addWidget(self.dtLabelUnit,2,2)

        self.iLine= QLineEdit(); self.layoutCP.addWidget(self.iLine,0,1)
        self.iLine.setText(str(self.settings.current))
        self.iLine.setValidator(QDoubleValidator(-1e1, 1e1, 9))
        
        self.tLine= QLineEdit(); self.layoutCP.addWidget(self.tLine,1,1)
        self.tLine.setText(str(self.settings.duration))
        self.tLine.setValidator(QDoubleValidator(1.00, 86400.00, 3))

        self.dtLine= QLineEdit(); self.layoutCP.addWidget(self.dtLine,2,1)
        self.dtLine.setText(str(self.settings.dt))

        #endregion

        #region: All widgets from column 1 (Mostly inputs)
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
        self.eRangeCombo.addItem("AUTO", 3)
        #endregion

        self.iRangeCombo= QComboBox(); self.layoutGen.addWidget(self.iRangeCombo, 1,1)
        #region: iRange combo options
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

        spacer = QSpacerItem(10, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.layoutGen.addItem(spacer,0,2)
        #endregion

        self.frameLayout.addStretch()

    def update_fields(self): #Signals to update attribute as widgets are edited
        self.iLine.editingFinished.connect(lambda: _update_att(float(self.iLine.text()), self.settings.current))
        self.tLine.editingFinished.connect(lambda: _update_att(float(self.tLine.text()), self.settings.duration))
        self.dtLine.editingFinished.connect(lambda: _update_att(float(self.dtLine.text()), self.settings.dt))

        self.iRangeCombo.currentTextChanged.connect(lambda: _update_att(self.iRangeCombo.currentData(), self.settings.iRange))
        self.eRangeCombo.currentTextChanged.connect(lambda: _update_att(self.eRangeCombo.currentData(), self.settings.eRange))
        self.bandwithCombo.currentTextChanged.connect(lambda: _update_att(int(self.bandwithCombo.currentText()), self.settings.bandwith))

if __name__ == '__main__':
    app= QApplication([])
    main= CPset()
    main.show()
    app.exec()
