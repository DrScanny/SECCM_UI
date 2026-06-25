from PySide6.QtCore import Qt, QEvent, QTimer, Signal, QPoint
from PySide6.QtGui import QColor, QIcon, QAction, QPixmap, QPolygon, QPainter
from PySide6.QtWidgets import (QCheckBox, QWidget, QMenu, QApplication, QFileDialog, QMainWindow, QButtonGroup, QPushButton, 
                               QMessageBox, QTextEdit,  QHBoxLayout, QVBoxLayout, QDockWidget, QColorDialog,
                               QMainWindow, QStatusBar, QWidget, QFrame, QListWidget, QGroupBox,
                               QSplitter, QPlainTextEdit, QLabel, QTreeWidgetItem, QAbstractItemView,
                               QTreeWidget, QComboBox, QLineEdit, QFileDialog, QSizePolicy, QStyle, QSpinBox,)

class ColorMenu(QMenu):
    colorSelected = Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)

        for color in ["black", "red", "blue", "green", "orange", "purple"]:
            action = QAction(color, self)
            action.triggered.connect(lambda checked=False, c=color: self.set_color(c))
            self.addAction(action)

        self.addSeparator()

        more_colors = QAction("More Colors...", self)
        more_colors.triggered.connect(self.open_color_dialog)
        self.addAction(more_colors)

    def set_color(self, color):
        self.selected_color = color
        self.colorSelected.emit(color)   # (you should define a signal)

    def open_color_dialog(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.selected_color = color.name()
            self.colorSelected.emit(self.selected_color)

class ShapeMenu(QMenu):
    shapeSelected = Signal(str)

    def __init__(self, parent=None):
        super().__init__("Marker Shape", parent)

        shapes = [
            ("Circle", "o"),
            ("Square", "s"),
            ("Triangle", "t"),
            ("Diamond", "d"),
            ("Cross", "x"),
        ]

        for name, marker in shapes:
            action = QAction(name, self)
            action.setIcon(self.create_shape_icon(marker))

            action.triggered.connect(
                lambda checked=False, m=marker: self.select_shape(m)
            )

            self.addAction(action)

    def select_shape(self, marker):
        self.shapeSelected.emit(marker)

    def create_shape_icon(self, marker):
        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        if marker == "o":
            painter.drawEllipse(4, 4, 12, 12)

        elif marker == "s":
            painter.drawRect(4, 4, 12, 12)

        elif marker == "t":
            painter.drawPolygon(
                QPolygon([
                    QPoint(10, 3),
                    QPoint(17, 17),
                    QPoint(3, 17)
                ])
            )

        elif marker == "d":
            painter.drawPolygon(
                QPolygon([
                    QPoint(10, 2),
                    QPoint(18, 10),
                    QPoint(10, 18),
                    QPoint(2, 10)
                ])
            )

        elif marker == "x":
            painter.drawLine(4, 4, 16, 16)
            painter.drawLine(16, 4, 4, 16)

        painter.end()

        return QIcon(pixmap)