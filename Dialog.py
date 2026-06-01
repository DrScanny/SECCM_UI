from PySide6.QtCore import Qt, QEvent, QObject, Signal, Slot, QThread, QThreadPool, QRunnable, Slot
from PySide6.QtWidgets import (QApplication, QFileDialog, QMainWindow, QButtonGroup, QPushButton, 
                               QMessageBox, QTextEdit,  QHBoxLayout, QVBoxLayout, QDockWidget,
                               QMainWindow, QStatusBar, QWidget, QFrame, QListWidget,
                               QSplitter, QPlainTextEdit, QLabel, QTreeWidgetItem, QAbstractItemView,
                               QTreeWidget, QProgressDialog, QProgressBar, QDialog, QDialogButtonBox)


class LoadingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Processing...")
        self.setModal(True) # Blocks input to the main window
        self.setFixedSize(250, 100)
        
        layout = QVBoxLayout()
        self.label = QLabel("Please wait while the process completes...")
        self.progress = QProgressBar()
        self.progress.setRange(0, 0) # Indefinite progress animation

          # Create a ButtonBox with a Cancel button
        self.buttonStop = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        
        # Change the text from "Cancel" to "Stop" if desired
        self.buttonStop.button(QDialogButtonBox.StandardButton.Cancel).setText("Stop")
        
        layout.addWidget(self.label)
        layout.addWidget(self.progress)
        layout.addWidget(self.buttonStop)
        self.setLayout(layout)