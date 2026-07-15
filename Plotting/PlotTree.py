import sys
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QTreeWidget,QTreeWidgetItem)
import UI_Settings

class DataTree(QWidget):
    clickedData = Signal(object, str)
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
        self.data_nodes = {}
        self.currentLanding = None


    #set the filename in the datatree using the filename entered by the user. 

    def setFilename(self, filename):

        #reset references
        #self.pixel_nodes = {}
        self.technique_nodes = {}

        #create filename header
        self.file_node = QTreeWidgetItem(self.tree)
        self.file_node.setText(0, filename)

        #optional: expanded by default
        self.file_node.setExpanded(True)
    
    def newtechniqueEntry(self, settings:UI_Settings.echemSettings):
        tech= settings.technique
        self.techCount[tech]+=1

        self.active= UI_Settings.echemData(technique = tech, 
                                            index = self.techCount[tech], 
                                            name= f"{tech}_{self.techCount[tech]}")

        techniqueNode = QTreeWidgetItem()
        techniqueNode.setText(0, self.active.name)
        techniqueNode.setData(0, Qt.ItemDataRole.UserRole, self.active)

        if self.currentLanding is not None:
            #add technique node to landing node
            self.currentLanding.addChild(techniqueNode)
            self.data_nodes.setdefault("self.currentLanding.text(0)", []).append(techniqueNode)
            techniqueNode.setData(0, Qt.ItemDataRole.UserRole +1, self.currentLanding.text(0))

        else:
            #add a technique node directly to the file node if there is no SECCM mode
            self.file_node.addChild(techniqueNode)
            techniqueNode.setData(0, Qt.ItemDataRole.UserRole +1, "")
        

    def newlandingEntry(self, landing):

        #when a new landing is created, the tech count resets
        self.techCount={'CV':0, 'CA':0, 'OCP':0, 'CP':0}
        coordinatelist = [float(x) for x in landing]
        coords = ",".join(map(str, coordinatelist))

        self.currentLanding = QTreeWidgetItem()
        self.currentLanding.setText(0, coords)

        #add a landing node to the file node
        if self.file_node:
            self.file_node.addChild(self.currentLanding)
        
    def tree_item_clicked(self, item, column):

        if item.data is not None:
            retreived_obj= item.data(0, Qt.ItemDataRole.UserRole)
            retreived_landing = item.data(0, Qt.ItemDataRole.UserRole + 1)
            self.clickedData.emit(retreived_obj, retreived_landing)
        else:
            return None
        

    def storeData(self):
        self.echemData[self.active.name]= self.active
   
if __name__ == '__main__':
    
    app= QApplication(sys.argv)
    main= DataTree()
    main.show()
    app.exec()


    