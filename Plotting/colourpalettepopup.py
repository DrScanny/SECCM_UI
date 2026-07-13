from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import (QDialog, QCheckBox, QWidget, QApplication, QFileDialog, QMainWindow, QButtonGroup, QPushButton, 
                               QMessageBox, QTextEdit,  QHBoxLayout, QVBoxLayout, QDockWidget,
                               QMainWindow, QStatusBar, QWidget, QFrame, QListWidget, QGroupBox,
                               QSplitter, QPlainTextEdit, QLabel, QTreeWidgetItem, QAbstractItemView,
                               QTreeWidget, QComboBox, QLineEdit, QFileDialog, QSizePolicy, QStyle, QSpinBox)

from pyqtgraph.exporters import ImageExporter
from dataclasses import dataclass, field
from PySide6.QtCore import Signal



class PaletteButton(QPushButton):
    paletteSelected = Signal(list)

    def __init__(self, colors, parent=None):
        super().__init__(parent)

        self.colors = colors

        self.clicked.connect(
            lambda: self.paletteSelected.emit(self.colors)
        )

        self.setFixedSize(300, 30)

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)

        square_width = self.width() / len(self.colors)

        for i, color in enumerate(self.colors):
            painter.fillRect(
                int(i * square_width),
                4,
                int(square_width),
                self.height() - 8,
                QColor(color)
            )


class ColorPopup(QDialog):
    paletteSelected = Signal(list)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Colour palette options")

        self.colorpopuplayout = QVBoxLayout(self)
        self.setLayout(self.colorpopuplayout)

        #ALL PALETTES LIVE HERE (hopefully easy to extend, palettes will be changed)
        self.palette_data = [
            ["#1F77B4", "#FF7F0E", "#2CA02C", "#D62728", "#9467BD", "#8C564B", "#E376C2", "#7F7F7F", "#BCBD22", "#17BECF"],
            ["#155d27", "#2f0e07", "#e85d04", "#d62728", "#184e77"],
            ["#560bad", "#f72585", "#17becf", "#ff8700", "#2b9348"]
        ]

        #Create buttons dynamically 
        for colors in self.palette_data:
            button = PaletteButton(colors, self)

            # forward child signal → popup signal
            button.paletteSelected.connect(self.paletteSelected)

            self.colorpopuplayout.addWidget(button)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    popup = ColorPopup()

    def on_palette_selected(colors):
        print("Selected palette:", colors)

    popup.paletteSelected.connect(on_palette_selected)

    popup.show()

    sys.exit(app.exec())