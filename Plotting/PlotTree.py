import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QTreeWidget,QTreeWidgetItem)
import UI_Settings

class DataTree(QWidget):
    def __init__(self):
        super().__init__()
        #Store echem data from each measurement using the name of the technique (temporary solution)
        self.echemData={}
        self.active= UI_Settings.echemData()
        
        #count the number of times each technique has been run
        self.techCount={'CV':0, 'CA':0, 'OCP':0, 'CP':0}

        self.layoutWidget= QVBoxLayout(); self.setLayout(self.layoutWidget)
        
        self.tree= QTreeWidget()
        self.tree.setHeaderLabel("Map Datasets")

        self.layoutWidget.addWidget(self.tree)
        self.tree.setIndentation(12)

        #keep references to pixel nodes
        #self.pixel_nodes = {}
        self.file_node = None
        self.technique_nodes = {}

    #add a dataset to the datatree using the technique ID
    #I am considering making a parent technique node and putting techniqueID nodes underneath 
    def addItem(self, name):

        # create technique node
        dataItem = QTreeWidgetItem()
        dataItem.setText(0, name)

        if self.file_node:
            self.file_node.addChild(dataItem)
            self.technique_nodes[name]= dataItem

    #set the filename in the datatree using the filename entered by the user. 
    #This is kind of broken right now because if a user overwrites their old file with a same name, a new element is still created.
    def setFilename(self, filename):

        #reset references
        #self.pixel_nodes = {}
        self.technique_nodes = {}

        #create filename header
        self.file_node = QTreeWidgetItem(self.tree)
        self.file_node.setText(0, filename)

        #optional: expanded by default
        self.file_node.setExpanded(True)
    
    def newEntry(self, technique):
        self.techCount[technique]+=1
        self.active= UI_Settings.echemData(technique = technique, 
                                            index = self.techCount[technique], 
                                            name= f"{technique}_{self.techCount[technique]}")
        self.addItem(self.active.name)

    def storeData(self):
        self.echemData[self.active.name]= self.active
   
if __name__ == '__main__':
    
    app= QApplication(sys.argv)
    main= DataTree()
    main.show()
    app.exec()


    