import sys
import numpy as np
import pyqtgraph as pg
from datetime import datetime

from PySide6.QtCore import Qt, QEvent
from PySide6.QtWidgets import (QWidget, QApplication, QFileDialog, QMainWindow, QButtonGroup, QPushButton, 
                               QMessageBox, QTextEdit,  QHBoxLayout, QVBoxLayout, QDockWidget,
                               QMainWindow, QStatusBar, QWidget, QFrame, QListWidget,
                               QSplitter, QPlainTextEdit, QLabel, QTreeWidgetItem, QAbstractItemView,
                               QTreeWidget, QComboBox, QLineEdit, QFileDialog, QSizePolicy, QStyle, QSpinBox)

from pyqtgraph.exporters import ImageExporter

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
   c) Extra features: the graph area should be visually pleasant, have options to zoom in part of the graph, save the plog as an image, 
      report the coordinate of each data point, basic plot customization (scatter options, color, trace options, color map, legends) ...

   1st assignment is to do basic live plotting see below plot1D_Live(self)
"""
class Plot(QWidget):
    def __init__(self):
        super().__init__()

        self.mainLayout = QVBoxLayout()
        self.setLayout(self.mainLayout)
        self.setWindowTitle("Main Window")
        
        #electrochem techniques
        self.technique = None
        self.pixel_counter = 0
        self.current_pixel_id = 0
        self.last_position = None

             #Assigns selected techniques to the proper variables as defined in the parsed_row dictionary
        self.technique_axes = {"OCP": ("t", "Ewe"),
                                "CA": ("t", "Iwe"),
                                "CP": ("t", "Ewe"),
                                "CV": ("Ewe", "Iwe")}

        #current data list        
        self.x_data = []
        self.y_data = []
        
        #save datasets in a series
        self.saved_datasets = {}
        
        #controls on top
        self.controlPanel = QFrame()
        self.controlPanel.setSizePolicy(QSizePolicy.Policy.Preferred,
                                        QSizePolicy.Policy.Fixed )
       
        self.controlLayout = QHBoxLayout(self.controlPanel)
        self.mainLayout.addWidget(self.controlPanel)

        #save as image button
        self.saveButton = QPushButton("Save Plot as Image")
        self.saveButton.clicked.connect(self.save_plot)
        self.controlLayout.addWidget(self.saveButton)

        #colour
        self.controlLayout.addWidget(QLabel("Plot Colour"))
        self.colourSelector = QComboBox()
        self.colourSelector.addItems(['Black', 'Red', 'Green', 'Blue'])
        self.colourSelector.currentTextChanged.connect(self.change_colour)
        self.controlLayout.addWidget(self.colourSelector)
        self.color = self.colourSelector.currentText()

        #plot type
        self.controlLayout.addWidget(QLabel("Plot Type"))

        self.plotTypeSelector = QComboBox()
        self.plotTypeSelector.addItems(["Line", "Scatter"])
        self.plotTypeSelector.currentTextChanged.connect(self.change_plot_type)
        self.controlLayout.addWidget(self.plotTypeSelector)

        #add spacing
        self.controlLayout.addSpacing(20)

        #add spacing
        self.controlLayout.addStretch()

        #setup plot
        self.plotSplitter = QSplitter(Qt.Orientation.Horizontal)
        self.mainLayout.addWidget(self.plotSplitter)

        self.framePlot = QFrame()
        self.plotSplitter.addWidget(self.framePlot)
        self.plotSplitter.setSizes([250,900])
        
        self.layoutPlot = QVBoxLayout(self.framePlot)
        self.plotWindow = pg.PlotWidget()
        self.layoutPlot.addWidget(self.plotWindow)

        #coordinate display label
        self.coordinateslabel = QLabel("Coordinates: ")
        self.coordLabel = QLabel(" ")
        self.layoutPlot.addWidget(self.coordinateslabel)
        self.layoutPlot.addWidget(self.coordLabel)

        #track state
        self.plot_type = "Line"
        self.plot_item = None

        #connect mouse movement for line hover support
        self.plotWindow.scene().sigMouseMoved.connect(self.mouse_moved)

        #setup plot
        self.setup_plot()


    def setup_plot(self):
    
        #stylizing the plot
        self.plotWindow.setBackground('w')
        self.plotWindow.setRenderHint(pg.QtGui.QPainter.Antialiasing)
        axis_pen = pg.mkPen(color='k', width=1)

        self.plotWindow.getAxis('left').setPen(axis_pen)
        self.plotWindow.getAxis('bottom').setPen(axis_pen)

        self.plotWindow.getAxis('left').setTextPen('k')
        self.plotWindow.getAxis('bottom').setTextPen('k')

        #set labels of the plot (x and y)
        self.plotWindow.setLabel('left', 'y_var')
        self.plotWindow.setLabel('bottom', 'x_var')

        #turn off the grid
        self.plotWindow.showGrid(x=False, y=False)

        #add vertical hover line (crosshair)
        self.vLine = pg.InfiniteLine(
            angle=90,
            movable=False,
            pen=pg.mkPen((150, 150, 150), width=1, style=Qt.DashLine)
        )
        self.plotWindow.addItem(self.vLine, ignoreBounds=True)

        #add horizontal hover line
        self.hLine = pg.InfiniteLine(
            angle=0,
            movable=False,
            pen=pg.mkPen((150, 150, 150), width=1, style=Qt.DashLine)
        )
        self.plotWindow.addItem(self.hLine, ignoreBounds=True)

        self.create_plot_item()

    def create_plot_item(self):
        self.plotWindow.clear()

        #readd hover lines after clearing plot
        self.plotWindow.addItem(self.vLine, ignoreBounds=True)
        self.plotWindow.addItem(self.hLine, ignoreBounds=True)

        #redraw the plot based on the selected chart type (line or scatter)
        if self.plot_type == "Line":

            self.plot_item = self.plotWindow.plot(
                pen=pg.mkPen(
                    color=self.color,
                    width=1.8,
                    cosmetic=True,
                    cap=Qt.RoundCap,
                    join=Qt.RoundJoin
                ),
                antialias=True
            )

        else:
            self.plot_item = pg.ScatterPlotItem(
                size=5,
                brush=pg.mkBrush(self.color),
                pen=pg.mkPen(None),
                hoverable=True,
                hoverSize=12,
                hoverPen=pg.mkPen('black', width=2)
            )

            self.plotWindow.addItem(self.plot_item)

            #hover only for scatter plots
            self.plot_item.sigHovered.connect(self.show_hover_data)

        if self.x_data:
            self.plot_item.setData(self.x_data, self.y_data)

     #method that updates the graph as data is being acquired from the potentiostat
    def add_dataPoint(self, technique, parsed_row):
        
        #Accounting for possible technique mismatch error
        if technique not in self.technique_axes:
            print(f"Unknown technique: {technique}")
            return

        #update the axes if the technique changes
        if technique != self.technique:

            self.technique = technique

            self.x_data.clear()
            self.y_data.clear()

            self.set_axes(technique)

        x_variable, y_variable = self.technique_axes[technique]

        #verify variables exist
        if x_variable not in parsed_row or y_variable not in parsed_row:
            print("Missing required variables in parsed_row")
            return

        #add the incoming data point to the list
        self.x_data.append(parsed_row[x_variable])
        self.y_data.append(parsed_row[y_variable])

        #update graph
        self.plot_item.setData(self.x_data, self.y_data)
    
    
    #this method uses any change in commanded position to update pixel count
    def update_pixel_count(self, commanded_position):

        if commanded_position is None:
            return

        #detect first position
        if self.last_position is None:
            self.last_position = commanded_position
            self.current_pixel_id = 0
            return

        #detect change in commanded position
        if commanded_position != self.last_position:
            self.current_pixel_id += 1
            self.last_position = commanded_position
    

    def change_colour(self, colour):
        if self.plot_item is None:
            return

        if self.plot_type == "Line":
            self.plot_item.setPen(
                pg.mkPen(
                    color=colour,
                    width=1.8,
                    cosmetic=True,
                    cap=Qt.RoundCap,
                    join=Qt.RoundJoin
                )
            )
        else:
            self.plot_item.setBrush(pg.mkBrush(colour))

    #if plot type is changed, update plot
    def change_plot_type(self, plot_type):
        self.plot_type = plot_type
        self.create_plot_item()
    

    #if "save as image" button is pressed, save plot as image
    def save_plot(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Plot",
            "",
            "PNG Files (*.png);;JPEG Files (*.jpg)"
        )

        if file_name == "":
            return

      #hide crosshairs before export so that they dont show up in the graph
        self.vLine.hide()
        self.hLine.hide()

        exporter = ImageExporter(self.plotWindow.plotItem)
        exporter.parameters()['width'] = 900
        exporter.export(file_name)

    #show crosshairs again after export
        self.vLine.show()
        self.hLine.show()

    #updates the coordinate label based on where the mouse is hovering
    def show_hover_data(self, plot, points):

        if points:

            point = points[0]

            x = point.pos().x()
            y = point.pos().y()

            self.vLine.setPos(x)
            self.hLine.setPos(y)

            self.coordLabel.setText(f"x = {x:.2f}, y = {y:.2f}")

    #hover detection
    def mouse_moved(self, pos):

        if self.plot_type != "Line":
            return

        if len(self.x_data) == 0:
            return

        mouse_point = self.plotWindow.plotItem.vb.mapSceneToView(pos)

        x = mouse_point.x()

        nearest_index = np.argmin(np.abs(np.array(self.x_data) - x))

        x_val = self.x_data[nearest_index]
        y_val = self.y_data[nearest_index]

        #move hover lines
        self.vLine.setPos(x_val)
        self.hLine.setPos(y_val)

        self.coordLabel.setText(f"x = {x_val:.2f}, y = {y_val:.2f}")
    
    def generate_timestamp(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    #set the axes of the plot based on the technique
    def set_axes(self, technique):

        self.timevar = "Time (s)"
        self.potentialvar = "Potential (V)"
        self.currentvar = "Current (A)"
        self.technique = technique
        self.xvar = ""
        self.yvar = ""
        
        if technique == 'Open Circuit Potential -OCP':

            self.xvar = self.timevar 
            self.yvar = self.potentialvar   
        
        elif technique == 'ChronoAmperometry -CA': 
            self.xvar = self.timevar
            self.yvar = self.currentvar
    
        elif technique == 'ChronoPotentiometry -CP': 
            self.xvar = self.timevar
            self.yvar = self.potentialvar
        
        else:
            self.xvar = self.potentialvar
            self.yvar = self.currentvar
        
        self.plotWindow.setLabel('bottom', self.xvar)
        self.plotWindow.setLabel('left', self.yvar)


if __name__ == '__main__':
    app = QApplication([])
    main = Plot()
    
    #temporary
    main.set_axes("Open Circuit Potential -OCP")
    
    main.show()
    app.exec()