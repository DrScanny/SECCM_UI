from PySide6.QtWidgets import (QApplication, QWidget,QTreeWidget,QTreeWidgetItem,QPushButton,QHBoxLayout,
                               QLabel,QMainWindow,QTabWidget, QTabBar,QDockWidget,QVBoxLayout, QPlainTextEdit,
                               QFrame, QWidget, QTreeWidgetItemIterator, QButtonGroup, QGroupBox, QListWidget) 

from PySide6.QtCore import QSize, Qt, QEvent,QMimeData,QModelIndex,QPoint
from PySide6.QtWidgets import QAbstractItemView 
from PySide6.QtGui import QMouseEvent,QDrag,QFont

class ExpLoad(QWidget):

    def __init__(self):
        super().__init__()

        # Setting-up Frame that contains all widgets(Label, QtreeWidget, PushButton)
        self.frame= QFrame()
        self.frameLayout= QVBoxLayout(self.frame)
        self.setLayout(self.frameLayout)

        #region Technique List section -------------------------------------------------------------------------------------------------------------------------------
        self.groupList= QGroupBox('Techniques List'); self.groupList.setStyleSheet(""" QGroupBox {font-weight: bold;}  """)
        self.groupList.setToolTip('Choose Echem Techniques to Add to Experiment Loadout')
        self.groupLayout= QVBoxLayout()
        self.groupList.setLayout(self.groupLayout)
        self.frameLayout.addWidget(self.groupList)
  
        self.list= QListWidget()
        self.groupLayout.addWidget(self.list)
        self.list.addItems(['Open Circuit Potential -OCP', 'ChronoAmperometry -CA', 'ChronoPotentiometry -CP', 'Voltammetry -LSV or CV'])

        height= self.list.sizeHintForRow(0) * self.list.count() + 2 * self.list.frameWidth()+10
        self.list.setFixedHeight(height)

        self.addButton= QPushButton("Add")
        self.groupLayout.addWidget(self.addButton)
        #endregion ----------------------------------------------------------------------------------------------------------------------------------------------------

        #region: QTreeWidget initialization --------------------------------------------------------------------------------------------------------------------------
        self.groupLoadout= QGroupBox("Experiment Loadout"); self.groupLoadout.setStyleSheet(""" QGroupBox {font-weight: bold;}  """)
        self.groupLoadout.setToolTip('Echem Techniques to be Performed during Experiment; Open the Technique Settings by Selecting it')
        self.layoutLoadout= QVBoxLayout()
        self.groupLoadout.setLayout(self.layoutLoadout)
        self.frameLayout.addWidget(self.groupLoadout)
     
        self.tree= QTreeWidget()
        self.layoutLoadout.addWidget(self.tree)
        self.tree.setHeaderHidden(True)
        self.tree.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.setDropIndicatorShown(False)
        self.tree.setDragDropOverwriteMode(False)
     
        #endregion -----------------------------------------------------------------------------------------------------------------------------------------------------

        #region: Start Experiment section ------------------------------------------------------------------------------------------------------------------------------
        self.groupStart= QGroupBox ("Channels"); self.groupStart.setStyleSheet(""" QGroupBox {font-weight: bold;}  """)
        self.groupStart.setToolTip('Select Potentiostat channel to perform experiment')
        self.layoutStart= QVBoxLayout()
        self.groupStart.setLayout(self.layoutStart)
        self.frameLayout.addWidget(self.groupStart)

        self.layoutChButton= QHBoxLayout(); self.layoutStart.addLayout(self.layoutChButton)
        self.buttonStart= QPushButton("Start"); self.layoutChButton.addWidget(self.buttonStart)
        self.buttonStop= QPushButton("Stop"); self.layoutChButton.addWidget(self.buttonStop)
        #endregion ---------------------------------------------------------------------------------------------------------------------------------------------------------

    
    def selection(self):
        return self.list.currentItem()

    def getAll(self):
        iterator = QTreeWidgetItemIterator(self.tree)
        allItems = []
        while iterator.value():
            item= iterator.value()
            allItems.append(item)
            iterator += 1  # Advance the iterator

        return allItems

if __name__ == '__main__':
    app= QApplication([])
    main= ExpLoad()
    main.show()
    app.exec()