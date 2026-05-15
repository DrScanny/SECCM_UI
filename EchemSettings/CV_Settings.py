import sys
import os
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent) 

from PySide6.QtCore import     (Qt)
from PySide6.QtGui import      (QBrush, QDoubleValidator, QIntValidator)
from PySide6.QtWidgets import  (QApplication, QComboBox, QFrame, QGridLayout, QHBoxLayout, QGroupBox,
                                QLabel, QLayout, QVBoxLayout,  QLineEdit, QSizePolicy, QWidget, QSpacerItem)
import UI_Settings

#region: Helper functions: , update_att, addWidgetsGrid

def _update_att(value, att)-> None:
        att= value
        print(att)

#endregion

class CVset(QWidget):

    def __init__(self):
        super().__init__()

        self.frame= QFrame()
        self.frameLayout= QVBoxLayout(self.frame)
        self.setLayout(self.frameLayout)

        # Instantiating CV settings dataclass
        self.settings= UI_Settings.CV()
    
        # Setting-up GUI elements
        self.setupUi()

        # Setting-up Signal and Slots to update attribute based on 
        self.update_fields()

        # ---------------- Binding & helpers ----------------

    def setupUi(self):


        self.groupRange=QGroupBox('Voltammetry'); self.groupRange.setStyleSheet(""" QGroupBox {font-weight: bold;}  """)
        self.layoutRange= QGridLayout(self.groupRange)
        self.frameLayout.addWidget(self.groupRange)

        #region: Voltammetry settings
        self.eiLabel= QLabel("Start at"); self.layoutRange.addWidget(self.eiLabel, 0,0)
        self.eiLabel.setToolTip("Set Initial potential V vs OCP (1st cycle only)")

        self.e1Label= QLabel("Scan to E<sub>1</sub>"); self.layoutRange.addWidget(self.e1Label, 1,0)
        self.e1Label.setToolTip("Set potential E1 V vs Ref for scanning range between E1 and E2")

        self.e2Label= QLabel("then to E<sub>2</sub>"); self.layoutRange.addWidget(self.e2Label, 2,0)
        self.e2Label.setToolTip("Set potential E2 V vs Ref for scanning range between E1 and E2")

        self.efLabel= QLabel("End at"); self.layoutRange.addWidget(self.efLabel, 3,0)
        self.efLabel.setToolTip("Set Final potential vs OCP (Last cycle only)")

        self.eiUnitLabel= QLabel('V vs OCP'); self.layoutRange.addWidget(self.eiUnitLabel, 0,2)
        self.e1UnitLabel= QLabel('V vs Ref'); self.layoutRange.addWidget(self.e1UnitLabel, 1,2)
        self.e2UnitLabel= QLabel('V vs Ref'); self.layoutRange.addWidget(self.e2UnitLabel, 2,2)
        self.efUnitLabel= QLabel('V vs OCP'); self.layoutRange.addWidget(self.efUnitLabel, 3,2)

        self.sep1= QFrame(); self.layoutRange.addWidget(self.sep1, 4,0,1,3) 
        self.sep1.setFrameShape(QFrame.Shape.HLine)
        self.sep1.setFrameShadow(QFrame.Shadow.Sunken)

        self.scanLabel= QLabel("Scan rate"); self.layoutRange.addWidget(self.scanLabel, 5,0)
        self.scanLabel.setToolTip("Set Scan rate in Volt per second")
        self.scanUnitLabel= QLabel('V/s'); self.layoutRange.addWidget(self.scanUnitLabel, 5,2)

        self.cycleLabel= QLabel("Repeat"); self.layoutRange.addWidget(self.cycleLabel, 6,0)
        self.cycleLabel.setToolTip("Number of additional cycles: 0 correspond to 1 measurement")

        self.eiLine= QLineEdit(); self.layoutRange.addWidget(self.eiLine, 0,1)
        self.eiLine.setText(str(self.settings.ei))
        self.eiLine.setValidator(QDoubleValidator(-10, 10, 3))
        
        self.e1Line= QLineEdit(); self.layoutRange.addWidget(self.e1Line, 1,1)
        self.e1Line.setText(str(self.settings.e1))
        self.e1Line.setValidator(QDoubleValidator(-10, 10, 3))

        self.e2Line= QLineEdit(); self.layoutRange.addWidget(self.e2Line, 2,1)
        self.e2Line.setText(str(self.settings.e2))
        self.e2Line.setValidator(QDoubleValidator(-10, 10, 3))

        self.efLine= QLineEdit(); self.layoutRange.addWidget(self.efLine, 3,1)
        self.efLine.setText(str(self.settings.ef))
        self.efLine.setValidator(QDoubleValidator(-10, 10, 3))

        self.scanLine= QLineEdit(); self.layoutRange.addWidget(self.scanLine, 5,1)
        self.scanLine.setText(str(self.settings.scanRate))
        self.efLine.setValidator(QDoubleValidator(0.0001, 1, 4))

        self.cycleLine= QLineEdit(); self.layoutRange.addWidget(self.cycleLine, 6,1)
        self.cycleLine.setText(str(self.settings.cycle))
        self.efLine.setValidator(QIntValidator(0, 99))
        #endregion

        #General Settings
        self.groupGen=QGroupBox('General'); self.groupGen.setStyleSheet(""" QGroupBox {font-weight: bold;}  """)
        self.layoutGen= QGridLayout(self.groupGen)
        self.frameLayout.addWidget(self.groupGen)

        self.eRangeLabel= QLabel("E Range"); self.layoutGen.addWidget(self.eRangeLabel, 0,0)
        self.eRangeLabel.setToolTip("Select Potential Range for experiment")

        self.iRangeLabel= QLabel("I Range"); self.layoutGen.addWidget(self.iRangeLabel, 1,0)
        self.iRangeLabel.setToolTip("Select Current Range for experiment")

        self.bandwithLabel= QLabel("Bandwith"); self.layoutGen.addWidget(self.bandwithLabel, 2,0)
        self.bandwithLabel.setToolTip("Bandwith controls the speed of the instrument feedback, higher bandwith reacts quicker at the cost of stability")

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

        self.eRangeCombo= QComboBox(); self.layoutGen.addWidget(self.eRangeCombo, 0,1)
        #region: eRange combo options
        self.eRangeCombo.addItem("\u00B1 2.5 V", 0)
        self.eRangeCombo.addItem("\u00B1 5 V", 1)
        self.eRangeCombo.addItem("\u00B1 10 V", 2)
        self.eRangeCombo.addItem("AUTO", 3)
        #endregion , alignment=Qt.AlignmentFlag.AlignLeft

        self.bandwithCombo= QComboBox(); self.layoutGen.addWidget(self.bandwithCombo, 2,1)
        self.bandwithCombo.addItems(['1', '2', '3', '4', '5', '6', '7', '8', '9'])
        self.bandwithCombo.setCurrentIndex(7)

        spacer = QSpacerItem(10, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.layoutGen.addItem(spacer,0,2)

        #Adding all widgets in the self.frameLayout
   
        self.frameLayout.addStretch()

    def update_fields(self): #Signals to update attribute as widgets are edited
        self.eiLine.editingFinished.connect(lambda: _update_att(float(self.eiLine.text()), self.settings.ei))
        self.e1Line.editingFinished.connect(lambda: _update_att(float(self.e1Line.text()), self.settings.e1))
        self.e2Line.editingFinished.connect(lambda: _update_att(float(self.e2Line.text()), self.settings.e2))
        self.efLine.editingFinished.connect(lambda: _update_att(float(self.efLine.text()), self.settings.ef))

        self.scanLine.editingFinished.connect(lambda: _update_att(float(self.scanLine.text()), self.settings.scanRate))
        self.cycleLine.editingFinished.connect(lambda: _update_att(int(self.cycleLine.text()), self.settings.cycle))

        self.iRangeCombo.currentTextChanged.connect(lambda: _update_att(self.iRangeCombo.currentData(), self.settings.iRange))
        self.eRangeCombo.currentTextChanged.connect(lambda: _update_att(self.eRangeCombo.currentData(), self.settings.eRange))
        self.bandwithCombo.currentTextChanged.connect(lambda: _update_att(int(self.bandwithCombo.currentText()), self.settings.bandwith))

if __name__ == '__main__':
    app= QApplication([])
    main= CVset()
    main.show()
    app.exec()
