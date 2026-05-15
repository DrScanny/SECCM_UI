from PySide6.QtCore import (QCoreApplication, QMetaObject)
from PySide6.QtGui import (QRegularExpressionValidator, QDoubleValidator, QIntValidator)
from PySide6.QtWidgets import (QGridLayout, QLabel, QWidget,  QLayout, QLineEdit, QSizePolicy, QSpacerItem,
                               QVBoxLayout, QComboBox, QFrame, QApplication, QMessageBox, QStackedWidget,
                               QPushButton, QPlainTextEdit)

from EchemSettings.OCP_Settings import OCPset
from EchemSettings.CA_Settings import CAset
from EchemSettings.CP_Settings import CPset
from EchemSettings.CV_Settings import CVset


class TechSettings(QWidget):
      
    def __init__(self):
        super().__init__()
        self.frame= QFrame()
        self.frameLayout= QVBoxLayout(self.frame)
        self.setLayout(self.frameLayout)

        self.frameStack= QFrame()
        self.frameStack.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Plain)
        self.frameStack_layout= QVBoxLayout(self.frameStack); self.frameLayout.addWidget(self.frameStack)
        self.stack= QStackedWidget()
        self.stack.setFixedWidth(250)

        # Layout for Main Window
        self.frameStack_layout.addWidget(self.stack)
        self.textDefault= QPlainTextEdit()
        self.textDefault.setPlainText("No experiments loaded yet \nAdd techniques to your experiments \nUsing the Add button or by double-click \nThen edit their settings")
        
        self.stack_addWidget(self.textDefault)

        #Signal and slots
        self.stack.widgetRemoved.connect(self.removed_widget)

    def stack_addWidget(self, tech_set:QWidget) -> QWidget:
        page= tech_set
        self.stack.addWidget(page)
        return page
    
    def stack_changeWidget(self, widget):
        page= widget
        self.stack.setCurrentWidget(widget)
        return page
    
    def removed_widget(self, event):
        print(f'stacked removed, remaining stacked pages{self.stack.count()}')
        if self.stack.count()==1:
            self.stack.setCurrentWidget(self.textDefault)

        else:
            self.stack.widget(self.stack.count())

    def techInst(self, technique:str):
        match technique:
            case 'Open Circuit Potential -OCP':
                return OCPset()
            case 'ChronoPotentiometry -CP':
                return CPset()
            case 'ChronoAmperometry -CA':
                return CAset()
            case 'Voltammetry -LSV or CV':
                return CVset()
            case _:
                print("> Failed to find technique")


if __name__ == '__main__':
    app= QApplication([])
    main= TechSettings()
    main.show()
    app.exec()