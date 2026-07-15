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

from Plotting.PlotTree import DataTree
from Plotting.colourpalettepopup import ColorPopup, PaletteButton
from Plotting.DesignMenu import ColorMenu, ShapeMenu

class DataWindow(QWidget):

    def __init__(self, echemData, landing):
        super().__init__()
        
        windowtitle = ", ".join([str(landing), echemData.name])

        self.setWindowTitle(windowtitle)
        self.resize(800, 600)
        self.x_variable = ""
        self.y_variable = ""
        self.xdata = None
        self.ydata = None
        self.plotline = None

        #region: UI setup
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.setLayout(self.mainLayout)
        
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
        self.linesizeSelector.setValue(self.lineSize)
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
        self.markersizeSelector.setValue(self.scatterSize)
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

        """
        #region: datatree
        #creating data tree
        self.dataTree= DataTree()
        self.plotSplitter.addWidget(self.dataTree)

        #if an item in the data tree is clicked, load the relevant dataset
        self.dataTree.tree.itemClicked.connect(self.dataTree.tree_item_clicked)
        self.dataTree.clickedData.connect(lambda obj, landing: self.open_plot_window(obj, landing))
        #endregion
        """
        
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

        """
        #track state
        self.plot_type = "Line"
        self.plot_items = []
        #endregion: UI setup

        #connect mouse movement for line hover support
        self.plotWindow.scene().sigMouseMoved.connect(self.mouse_moved)
        """

        #setup plot
        self.setData(echemData)
        self.setup_plot()
    
    def setData(self, echemData):
        
        timeLabel = "Time (s)"
        potentialLabel = "Potential (V)"
        currentLabel = "Current (A)"
        
        if echemData.technique == 'OCP':
            self.x_variable= 't'
            self.y_variable= 'Ewe'
            xLabel= timeLabel
            yLabel= currentLabel 
        
        elif echemData.technique == 'CA': 
            self.x_variable= 't'
            self.y_variable= 'Iwe'  
            xLabel= timeLabel
            yLabel= potentialLabel
    
        elif echemData.technique == 'CP': 
            self.x_variable= 't'
            self.y_variable= 'Ewe'  
            xLabel= timeLabel
            yLabel= potentialLabel
        
        else:
            self.x_variable= 'Ewe'
            self.y_variable= 'Iwe'  
            xLabel= potentialLabel
            yLabel= currentLabel
        
        self.plotWindow.setLabel('bottom', xLabel)
        self.plotWindow.setLabel('left', yLabel)

        self.xdata = getattr(echemData, self.x_variable)
        self.ydata = getattr(echemData, self.y_variable)

        self.set_pen()



    def setup_plot(self):
    
        #stylizing the plot
        self.plotWindow.setBackground('w')
        self.plotWindow.setRenderHint(pg.QtGui.QPainter.RenderHint.Antialiasing)
        axis_pen = pg.mkPen(color='k', width=1)

        self.plotWindow.getAxis('left').setPen(axis_pen)
        self.plotWindow.getAxis('bottom').setPen(axis_pen)

        self.plotWindow.getAxis('left').setTextPen('k')
        self.plotWindow.getAxis('bottom').setTextPen('k')

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

        if self.plotline is not None:
            self.plotWindow.removeItem(self.plotline)
        
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
        
        self.plotline = self.plotWindow.plot(
            self.xdata,
            self.ydata,
            pen=pen,
            symbol = symbol,
            symbolSize = symbolSize,
            symbolBrush = symbolBrush,
        ) 
    #endregion

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