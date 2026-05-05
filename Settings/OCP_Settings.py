import sys
import os
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent) 

from PySide6.QtCore import (QCoreApplication, QMetaObject)
from PySide6.QtGui import (QRegularExpressionValidator, QDoubleValidator, QIntValidator)
from PySide6.QtWidgets import (QGridLayout, QLabel, QWidget,  QLayout, QLineEdit, QSizePolicy, QSpacerItem,
                               QVBoxLayout, QComboBox, QFrame, QApplication, QMessageBox, QGroupBox)
import SECCM_Settings
   
def _update_att(input_value, att)-> None:

    att= input_value
    print(att)

class OCPset(QWidget):
    tech= "OCP"

    def __init__(self):
        super().__init__()
        self.frame= QFrame()
        self.frameLayout= QVBoxLayout(self.frame)
        self.setLayout(self.frameLayout)
        
        #Attributes for OCP
        self.settings= SECCM_Settings.OCPsettings()

        self.setup_UI()
        self.update_fields()

    def setup_UI(self):
        self.groupOCP=QGroupBox('Open Circuit Potential'); self.groupOCP.setStyleSheet(""" QGroupBox {font-weight: bold;}  """)
        self.layoutOCP= QGridLayout(self.groupOCP)
        self.frameLayout.addWidget(self.groupOCP)

        self.label_1 = QLabel("Duration"); self.layoutOCP.addWidget(self.label_1, 0, 0)
        self.label_1.setToolTip("Set experiment duration in seconds up to 86 400")
        self.labelUnit1 = QLabel("s"); self.layoutOCP.addWidget(self.labelUnit1, 0, 2)

        self.lineEdit_1 = QLineEdit()
        self.layoutOCP.addWidget(self.lineEdit_1, 0, 1)
        self.lineEdit_1.setText(str(self.settings.duration))
        self.lineEdit_1.setValidator(QDoubleValidator(1.00, 86400.00, 3))

        self.label_2= QLabel("Every"); self.layoutOCP.addWidget(self.label_2, 1, 0)
        self.labelUnit2 = QLabel("s"); self.layoutOCP.addWidget(self.labelUnit2, 1, 2)

        self.label_2.setToolTip("Measure every (s), fastest rate is every 1 ms")
        self.lineEdit_2 = QLineEdit()
        self.layoutOCP.addWidget(self.lineEdit_2, 1, 1)
        self.lineEdit_2.setText(str(self.settings.dt))
        self.lineEdit_2.setValidator(QDoubleValidator(0.001, 60.000, 3))

        self.label_3= QLabel("E range (V)")
        self.layoutOCP.addWidget(self.label_3, 3, 0)
        self.eRangeCombo= QComboBox()
        self.layoutOCP.addWidget(self.eRangeCombo, 3, 1)
        #region: ComboBox options
        self.eRangeCombo.addItem("\u00B1 2.5 V", 0)
        self.eRangeCombo.addItem("\u00B1 5 V", 1)
        self.eRangeCombo.addItem("\u00B1 10 V", 2)
        self.eRangeCombo.addItem("AUTO", 3)
        #endregion
        
        #self.layoutOCP.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding), 4,1)
        self.frameLayout.addStretch()
        
    def update_fields(self): #Signals to update attribute as widgets are edited
        self.lineEdit_1.editingFinished.connect(lambda: _update_att(float(self.lineEdit_1.text()), self.settings.duration))
        self.lineEdit_2.editingFinished.connect(lambda: _update_att(float(self.lineEdit_2.text()), self.settings.dt))
        self.eRangeCombo.currentTextChanged.connect(lambda: _update_att(self.eRangeCombo.currentData(), self.settings.eRange))

if __name__ == '__main__':
    app= QApplication([])
    main= OCPset()
    main.show()
    app.exec()

        


       