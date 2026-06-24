from PySide6.QtCore import Qt, QEvent, QTimer
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (QCheckBox, QWidget, QApplication, QFileDialog, QMainWindow, QButtonGroup, QPushButton, 
                               QMessageBox, QTextEdit,  QHBoxLayout, QVBoxLayout, QDockWidget, QMenu, QToolButton,
                               QMainWindow, QStatusBar, QWidget, QFrame, QListWidget, QGroupBox,
                               QSplitter, QPlainTextEdit, QLabel, QTreeWidgetItem, QAbstractItemView,
                               QTreeWidget, QComboBox, QLineEdit, QFileDialog, QSizePolicy, QStyle, QSpinBox)

import sys
import numpy as np
import pyqtgraph as pg
import time
from datetime import datetime

from pyqtgraph.exporters import ImageExporter
from itertools import cycle

from Plotting.PlotTree import DataTree
from Plotting.colourpalettepopup import ColorPopup, PaletteButton

from Plotting import UI_Settings
from Plotting.DesignMenu import ColorMenu, ShapeMenu

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
#Popwindow that loads data from datatree (not yet functional)
class DataWindow(QWidget):
    def __init__(self, echemData):
        super().__init__()

        self.setWindowTitle(echemData.name)
        self.resize(800, 600)

        layout = QVBoxLayout(self)

        self.plotWidget = pg.PlotWidget()
        layout.addWidget(self.plotWidget)

        x = echemData.t
        y = echemData.Ewe

        self.plotWidget.plot(x, y, pen='k')



class Plot(QWidget):
    def __init__(self):
        super().__init__()
        #region: variables
         #electrochem techniques
        self.pixel_counter = 0
        self.current_pixel_id = 0
        self.last_position = None
        self.selected_technique = None
        self.live_curve = None

        #current data list       
        self.x_variable= 't'
        self.y_variable= 'Ewe'
        self.x_data = []
        self.y_data = []

        #region: UI setup
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.setLayout(self.mainLayout)
        self.setWindowTitle("Main Window")
        
        #controls on top
        self.controlPanel = QFrame()
        self.controlPanel.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed
        )
        self.controlLayout = QHBoxLayout(self.controlPanel)
        self.controlLayout.setContentsMargins(5, 5, 0, 0)
        self.controlLayout.setSpacing(2)
        self.mainLayout.addWidget(self.controlPanel)

        #Set style for all buttons
        toolbar_style = """
        QPushButton {
            border: none;
            background: transparent;
            padding: 2px;
        }
        QPushButton:hover {
            background-color: rgba(100,100,100,40);
        }
        QPushButton:pressed {
            background-color: rgba(100,100,100,80);
        }
        """

        #save as image button
        self.saveButton = QPushButton()
        self.saveButton.setIcon(QIcon("icons/save"))
        self.saveButton.clicked.connect(self.save_plot)
        self.controlLayout.addWidget(self.saveButton)
        
        #region: line and scatterplot options layout
        #Line options -------
        #keep track of line parameters
        self.lineChecked = True
        self.lineSize = 2
        self.lineColor = "#ff0000"
        self.lineColorMenu = ColorMenu()
        self.linegroup = QGroupBox("Line Options")
        self.lineplotoptionslayout = QHBoxLayout()
        #Option to disable lines
        self.linedisableoption = QCheckBox()
        self.linedisableoption.setChecked(True)
        self.lineplotoptionslayout.addWidget(self.linedisableoption)
        self.linedisableoption.stateChanged.connect(self.change_line_state)

        #lineplot color selector
        self.linecolourSelector = QToolButton()
        self.linecolourSelector.setStyleSheet(f"""
            QToolButton {{
                background-color: {self.lineColor};
                border-radius: 8px;
                border: 1px solid #444;
            }}
            QToolButton::menu-indicator {{
                image: none;
                width: 0px;
            }}
            QPushButton:hover {{
                border: 2px solid #222;
            }}
        """)
        self.linecolourSelector.setMenu(self.lineColorMenu)
        self.linecolourSelector.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.linecolourSelector.setFixedSize(17,17)
        self.lineColorMenu.colorSelected.connect(self.change_line_color)
        self.lineplotoptionslayout.addWidget(self.linecolourSelector)
        #self.linecolourSelector.clicked.connect(self.show_color_popup)
        #lineplot shape selector
        self.lineshapeSelector = QPushButton()
        self.lineshapeSelector.setIcon(QIcon("icons/dashedline"))
        self.lineplotoptionslayout.addWidget(self.lineshapeSelector)
        # Add the line options to the main layout
        self.linegroup.setLayout(self.lineplotoptionslayout)
        self.controlLayout.addWidget(self.linegroup)
        #Line size selector
        self.linesizeSelector = QSpinBox()
        self.linesizeSelector.setRange(1,20)
        self.linesizeSelector.setValue(2)
        self.lineplotoptionslayout.addWidget(self.linesizeSelector)
        self.linesizeSelector.valueChanged.connect(self.change_line_size)

        #Scatterplot options -------
        #keep track of scatter parameters
        self.scatterChecked = True
        self.scatterSize = 8
        self.scatterShape = 'o'
        self.scatterColor = 'k'
        self.scatterColorMenu = ColorMenu()
        #create layout
        self.scattergroup = QGroupBox("Marker Options")
        self.scatterplotoptionslayout = QHBoxLayout()
        #Option to disable markers
        self.scatterenableoption = QCheckBox()
        self.scatterenableoption.setChecked(True)
        self.scatterenableoption.stateChanged.connect(self.change_scatter_state)
        self.scatterplotoptionslayout.addWidget(self.scatterenableoption)
        #Scatterplot color selector
        self.scattercolourSelector = QToolButton()
        self.scattercolourSelector.setStyleSheet(f"""
            QToolButton {{
                background-color: {self.scatterColor};
                border-radius: 8px;
                border: 1px solid #444;
            }}
            QToolButton::menu-indicator {{
                image: none;
                width: 0px;
            }}
            QPushButton:hover {{
                border: 2px solid #222;
            }}
        """)
        self.scattercolourSelector.setMenu(self.scatterColorMenu)
        self.scattercolourSelector.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.scattercolourSelector.setFixedSize(17,17)
        self.scatterColorMenu.colorSelected.connect(self.change_scatter_color)
        self.scatterplotoptionslayout.addWidget(self.scattercolourSelector)
        #Scatterplot shape selector
        self.scatterShapeMenu = ShapeMenu()
        self.scattershapeSelector = QPushButton()
        self.scattershapeSelector.setIcon(QIcon("icons/markershapeicon"))
        self.scattershapeSelector.setMenu(self.scatterShapeMenu)
        self.scatterShapeMenu.shapeSelected.connect(self.change_scatter_shape)
        self.scatterplotoptionslayout.addWidget(self.scattershapeSelector)
        #Scatterplot marker size selector
        self.markersizeSelector = QSpinBox()
        self.markersizeSelector.setRange(1,20)
        self.markersizeSelector.setValue(8)
        self.scatterplotoptionslayout.addWidget(self.markersizeSelector)
        self.markersizeSelector.valueChanged.connect(self.change_scatter_size)

        # Add the scattergroup box widget to the main layout
        self.scattergroup.setLayout(self.scatterplotoptionslayout)
        self.controlLayout.addWidget(self.scattergroup)
        #endregion

        #zoom in button
        self.zoomInButton = QPushButton()
        self.zoomInButton.setIcon(QIcon("icons/zoomin"))
        #self.zoomInButton.setFixedSize(34, 34)
        self.zoomInButton.setToolTip("Zoom In")
        self.zoomInButton.clicked.connect(self.zoom_in)
        self.controlLayout.addWidget(self.zoomInButton)

        #zoom out button
        self.zoomOutButton = QPushButton()
        self.zoomOutButton.setIcon(QIcon("icons/zoomout"))
        #self.zoomOutButton.setFixedSize(34, 34)
        self.zoomOutButton.setToolTip("Zoom Out")
        self.zoomOutButton.clicked.connect(self.zoom_out)
        self.controlLayout.addWidget(self.zoomOutButton)

        #select zoom
        self.rectZoomButton = QPushButton()
        self.rectZoomButton.setIcon(QIcon("icons/zoomrectangle"))
        #self.rectZoomButton.setFixedSize(34, 34)
        self.rectZoomButton.setToolTip("Rectangle Select Zoom")
        self.rectZoomButton.setCheckable(True)
        self.rectZoomButton.clicked.connect(self.toggle_rect_zoom)
        self.controlLayout.addWidget(self.rectZoomButton)

        #Set default style to all buttons
        self.lineshapeSelector.setStyleSheet(toolbar_style)
        self.scattershapeSelector.setStyleSheet(toolbar_style)
        self.saveButton.setStyleSheet(toolbar_style)
        self.zoomInButton.setStyleSheet(toolbar_style)
        self.zoomOutButton.setStyleSheet(toolbar_style)
        self.rectZoomButton.setStyleSheet(toolbar_style)

        #add spacing
        self.controlLayout.addSpacing(20)

        #add spacing
        self.controlLayout.addStretch()

        #setup plot
        self.plotSplitter = QSplitter(Qt.Orientation.Horizontal)
        self.mainLayout.addWidget(self.plotSplitter)

        #region: datatree
        #creating data tree
        self.dataTree= DataTree()
        self.plotSplitter.addWidget(self.dataTree)

        #if an item in the data tree is clicked, load the relevant dataset
        #self.dataTree.tree.itemClicked.connect(self.tree_item_clicked)
        #endregion
        
        self.framePlot = QFrame()
        self.plotSplitter.addWidget(self.framePlot)
        self.plotSplitter.setSizes([250,900])
        
        self.layoutPlot = QVBoxLayout(self.framePlot)
        self.plotWindow = pg.PlotWidget()
        self.layoutPlot.addWidget(self.plotWindow)
        self.plotWindow.getPlotItem().layout.setContentsMargins(10, 20, 20, 10)

        #coordinate display label
        self.coordinateslabel = QLabel("Coordinates: ")
        self.coordLabel = QLabel(" ")
        self.layoutPlot.addWidget(self.coordinateslabel)
        self.layoutPlot.addWidget(self.coordLabel)

        #track state
        self.plot_type = "Line"
        self.plot_items = []
        #endregion: UI setup

        #connect mouse movement for line hover support
        self.plotWindow.scene().sigMouseMoved.connect(self.mouse_moved)

        #setup plot
        self.setup_plot()

        #region: colour popup options
        #pull palettes from colourpalettepopup.py and put them into a list of lists. Use the format self.palettes[0][2] to get the 3rd colour of the first palette
        self.linecolorpopup = ColorPopup()

        #set default palette to palette1
        self.currentpalette = self.linecolorpopup.palette_data[0]
        #connect selected button to palette_clicked function, which returns the new palette (color list)
        self.linecolorpopup.paletteSelected.connect(self.palette_clicked)

        #endregion
        self.plotrefresh= QTimer(self)
        self.plotrefresh.timeout.connect(self.refreshPlot)

    def setup_plot(self):
    
        #stylizing the plot
        self.plotWindow.setBackground('w')
        self.plotWindow.setRenderHint(pg.QtGui.QPainter.RenderHint.Antialiasing)
        axis_pen = pg.mkPen(color='k', width=1)

        self.plotWindow.getAxis('left').setPen(axis_pen)
        self.plotWindow.getAxis('bottom').setPen(axis_pen)

        self.plotWindow.getAxis('left').setTextPen('k')
        self.plotWindow.getAxis('bottom').setTextPen('k')

        #set labels of the plot (x and y)
        #self.plotWindow.setLabel('left', 'y_var')
        #self.plotWindow.setLabel('bottom', 'x_var')

        #turn off the grid
        self.plotWindow.showGrid(x=False, y=False)

        #add vertical hover line (crosshair)
        self.vLine = pg.InfiniteLine(
            angle=90,
            movable=False,
            pen=pg.mkPen((150, 150, 150), width=1, style=Qt.PenStyle.DashLine)
        )
        self.plotWindow.addItem(self.vLine, ignoreBounds=True)

        #add horizontal hover line
        self.hLine = pg.InfiniteLine(
            angle=0,
            movable=False,
            pen=pg.mkPen((150, 150, 150), width=1, style=Qt.PenStyle.DashLine)
        )
        self.plotWindow.addItem(self.hLine, ignoreBounds=True)

        self.set_pen()
    
    #region: set pen
    def set_pen(self):
        self.clear_plot_curves()
        
        if self.scatterChecked == True:
            symbol = self.scatterShape
            symbolBrush = self.scatterColor
            symbolSize = self.scatterSize
        else:
            symbol = None
            symbolBrush = None
            symbolSize = None
        
        if self.lineChecked == True:
            pen = pg.mkPen(color=self.lineColor, width=self.lineSize)
        else:
            pen = None
    
        
        self.live_curve = self.plotWindow.plot(
            [],
            [],
            pen=pen,
            symbol = symbol,
            symbolSize = symbolSize,
            symbolBrush = symbolBrush,
        ) 
    #endregion
    
    def show_color_popup(self):
        self.linecolorpopup.exec()
    
    #region: main plot update function 
    #method that updates the graph as data is being acquired from the potentiostat
    def add_data_point(self, parsed_row):

        #extract the data value based on the variable name x_variable and y_variable
        x = parsed_row[self.x_variable]
        y = parsed_row[self.y_variable]

        #add the incoming data point to the list
        self.x_data.append(x)
        self.y_data.append(y)

     #set the axes of the plot based on the technique
    
    #endregion

    #region: set axes method
    #method that sets the axes labels based on chosen techniques
    def setAxes(self, technique):
        
        timeLabel = "Time (s)"
        potentialLabel = "Potential (V)"
        currentLabel = "Current (A)"
        
        if technique == 'OCP':
            self.x_variable= 't'
            self.y_variable= 'Ewe'
            xLabel= timeLabel
            yLabel= currentLabel 
        
        elif technique == 'CA': 
            self.x_variable= 't'
            self.y_variable= 'Iwe'  
            xLabel= timeLabel
            yLabel= potentialLabel
    
        elif technique == 'CP': 
            self.x_variable= 't'
            self.y_variable= 'Ewe'  
            xLabel= timeLabel
            yLabel= potentialLabel
        
        else:
            self.x_variable= 'Ewe'
            self.y_variable= 'Iwe'  
            xLabel= potentialLabel
            yLabel= currentLabel
        
        #bottom two lines currently not working due to a threading error that i can't figure out 
        #self.plotWindow.setLabel('bottom', xLabel)
        #self.plotWindow.setLabel('left', yLabel)
    #endregion

    # Both functions below can be replaced by a single dict
        
    #get the index of the technique
    """
    
    def returntechniqueIndex(self, technique):

        if technique == 'OCP':
            return self.ocpcount
        
        elif technique == 'CA':  
            return self.cacount
    
        elif technique == 'CP': 
            return self.cpcount
        
        elif technique == 'CV':
            return self.cvcount
        
        else:
            return None
    """
    
    #if a new technique or run has started, restart plotting
    def clearPlot(self):
        self.x_data.clear()
        self.y_data.clear()
     
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
    

    #region: save plot as image method
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
    
    #endregion
    
    def clear_plot_curves(self):

        for curve in self.plot_items:

            self.plotWindow.removeItem(curve)

        self.plot_items.clear()
        self.plotWindow.removeItem(self.live_curve)
    
    """
    def pixel_visibility_changed(
            self,
            item,
            column
    ):
        parent = item.parent()

        if parent is None:
            return

        if parent == self.dataTree.file_node:
            return

        technique = parent.text(0)

        if technique != self.selected_technique:
            return

        self.load_plot_from_datatree(technique)
    """
    

    #region: load plot from datatree
    def load_plot(self, echemData):
        #self.plotWindow.clear()

        #IMPORTANT: this only works because each new technique node in the datatree is named with the format "CV_2". It does not allow for changing technique IDs currently
        tech_item = self.dataTree.technique_nodes[echemData.name]
        techniqueindex = echemData.index
        self.setAxes(echemData.technique)
        x_var = getattr(echemData, self.x_variable)
        y_var = getattr(echemData, self.y_variable)

        #ReDraw the curve using selected palette. modulo operator causes it to cycle 
        if len(self.currentpalette) == 0:
            pen = pg.mkPen(color="#0A0A0A", width=2)
        else:
            color = self.currentpalette[(techniqueindex - 1) % len(self.currentpalette)]
            pen = pg.mkPen(color=color, width=2)

        curve = self.plotWindow.plot(
            x_var,
            y_var,
            pen=pen
        )

        self.plot_items.append(curve)
    
    #endregion

    def palette_clicked(self, colors):
        self.currentpalette = colors

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
    
    #region: set plot type
    def change_line_state(self, state):
        if state == Qt.CheckState.Checked.value:
            self.lineChecked = True
        else:
            self.lineChecked = False
        
        self.set_pen()
    
    def change_line_size(self, value):
        self.lineSize = value
        self.set_pen()
    
    def change_line_color(self, color):
        self.lineColor = color
        self.linecolourSelector.setStyleSheet(f"""
            QToolButton {{
                background-color: {self.lineColor};
                border-radius: 8px;
                border: 1px solid #444;
            }}
            QToolButton::menu-indicator {{
                image: none;
                width: 0px;
            }}
            QPushButton:hover {{
                border: 2px solid #222;
            }}
        """)
        self.set_pen()

    def change_scatter_state(self, state):
        if state == Qt.CheckState.Checked.value:
            self.scatterChecked = True
        else:
            self.scatterChecked = False
        
        self.set_pen()
    
    def change_scatter_size(self, value):
        self.scatterSize = value
        self.set_pen()
    
    def change_scatter_color(self, color):
        self.scatterColor = color
        self.scattercolourSelector.setStyleSheet(f"""
            QToolButton {{
                background-color: {self.scatterColor};
                border-radius: 8px;
                border: 1px solid #444;
            }}
            QToolButton::menu-indicator {{
                image: none;
                width: 0px;
            }}
            QPushButton:hover {{
                border: 2px solid #222;
            }}
        """)
        self.set_pen()
    
    def change_scatter_shape(self, shape):
        self.scatterShape = shape
        self.set_pen()
    
    #endregion
    
    #region: zoom functions
    def zoom_in(self):

        vb = self.plotWindow.getPlotItem().getViewBox()
        vb.scaleBy((0.8, 0.8))

    def zoom_out(self):

        vb = self.plotWindow.getPlotItem().getViewBox()
        vb.scaleBy((1.25, 1.25))

    def toggle_rect_zoom(self):

        vb = self.plotWindow.getPlotItem().getViewBox()

        if self.rectZoomButton.isChecked():

            vb.setMouseMode(pg.ViewBox.RectMode)

        else:

            vb.setMouseMode(pg.ViewBox.PanMode)
    
    #endregion

    #region: timer functions
    def start_timer(self):
        print("timer started")
        self.plotrefresh.start(500)  

    def refreshPlot(self):
        self.live_curve.setData(self.x_data, self.y_data)
    
    def stop_timer(self):
        self.plotrefresh.stop()
    #endregion


if __name__ == '__main__':
    app = QApplication([])
    main = Plot()
    main.show()

    app.exec()