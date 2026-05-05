import sys
import time
import numpy as np
import pyqtgraph as pg

from PySide6.QtCore import Qt, QEvent
from PySide6.QtWidgets import (QApplication, QFileDialog, QMainWindow, QButtonGroup, QPushButton, 
                               QMessageBox, QTextEdit,  QHBoxLayout, QVBoxLayout, QDockWidget,
                               QMainWindow, QStatusBar, QWidget, QFrame, QListWidget,
                               QSplitter, QPlainTextEdit, QLabel, QTreeWidgetItem, QAbstractItemView,
                               QTreeWidget)

"""
Section to show data acquired through plots, it will include 2 parts:
   I- Graph area to plot both 1D (scatter/line plots) and 2D (scatter/heat maps) plots
   II- Data management with multiple levels to organize the different measurements acquired at each landing

I- Graph area
   a) Live plotting the data acquired by the potentiostat
      Have the options for each axis to pick the data variable for example in a CV the data is comprised of {t: time, E: potential, I: current, cycle: cycle number}

   b) Plot data from datatree
      i) 1D (scatter/line plots)
      ii) 2D (scatter/heat maps) plots
   c) Extra features: the graph area should be visually pleasant, have options to zoom in part of the graph, save the plot as an image, 
      report the coordinate of each data point, basic plot customization (scatter options, color, trace options, color map, legends) ...

   1st assignment is to do basic live plotting see below plot1D_Live(self)
"""

class Plot(QWidget):
      def __init__(self):
         super().__init__()

         #region: Plot widget layout
         self.layoutWidget= QVBoxLayout()
         self.setLayout(self.layoutWidget)
         
         self.plotSplitter= QSplitter(Qt.Orientation.Vertical); self.layoutWidget.addWidget(self.plotSplitter)

         self.framePlot= QFrame(); self.plotSplitter.addWidget(self.framePlot)
         self.layoutPlot= QVBoxLayout(self.framePlot)
         self.plotWindow= pg.PlotWidget(); self.layoutPlot.addWidget(self.plotWindow)

         self.frameTree= QFrame(); self.plotSplitter.addWidget(self.frameTree)
         self.layoutTree= QVBoxLayout(self.frameTree)
         self.TreePlot= QTreeWidget(); self.layoutTree.addWidget(self.TreePlot)
         #end region
         
         #self.plot1D_Live()

      def plot1D_Live(self):
         data= np.random.default_rng().normal(loc=0.0, scale=1.0, size=50000)
         x,y = np.histogram(data, bins=250)

         #Using pyqtgraph plot the data live through each iteration. 
         # The loop below is to simulate what would happen as data is acquired by the potentiostat
         for index in range(len(x)):
             #Each pair of data for the plots can be accessed by x[index] and y[index]
             time.sleep(0.5)
             pass

        

if __name__ == '__main__':
    app= QApplication([])
    main= Plot()
    main.show()
    app.exec()