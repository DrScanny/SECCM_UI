from PySide6.QtCore import Qt, QEvent, QObject, Signal, Slot, QRect, QPoint
from PySide6.QtGui import QPaintEvent, QPainter, QColor, QFont
from PySide6.QtWidgets import (QCheckBox)

class QToggle(QCheckBox):
    def __init__(self, width:int= 70, 
                 height:int= 20, 
                 bgColor:str='#777777', 
                 circleColor:str='#FFFFFF', 
                 activeColor:str='#00E200'):
        
        super().__init__()

        self.rectWidth= width
        self.rectHeight= height
        self.circleRadius= 16

        self.bgColor= bgColor
        self.circleColor= circleColor
        self.activeColor= activeColor 

        self.alignment= Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap
        self.textOff= 'Off'
        self.textOn= 'On'

        self.setFixedSize(self.rectWidth, self.rectHeight)

    def hitButton(self, pos: QPoint):
        return self.contentsRect().contains(pos)
        
    def paintEvent(self, e):
        p= QPainter(self)   
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)

        if not self.isChecked():
            
            #Rectangle body of the toggle when *Unchecked*
            rect= QRect(0,0, self.rectWidth, self.rectHeight)
            p.setBrush(QColor(self.bgColor))
            p.drawRoundedRect(0,0, rect.width(), rect.height(), rect.height()/2, rect.height()/2)

            p.setPen(QColor("#FFFFFF"))               # Text color
            p.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            p.drawText(rect, self.alignment, self.textOff)
         
            #Circle body of the toggle when *Unchecked*
            p.setBrush(QColor(self.circleColor))
            p.drawEllipse(2,2, self.circleRadius, self.circleRadius)

        else:
            #Rectangle body of the toggle when *Checked*
            rect= QRect(0,0, self.rectWidth, self.rectHeight)
            p.setBrush(QColor(self.activeColor))
            p.drawRoundedRect(0,0, rect.width(), rect.height(), rect.height()/2, rect.height()/2)
         
            #Circle body of the toggle when *Unchecked*
            p.setBrush(QColor(self.circleColor))
            p.drawEllipse(rect.width()-self.circleRadius-2,
                          2, 
                          self.circleRadius, 
                          self.circleRadius)
            
            p.setPen(QColor("#FFFFFF"))             
            p.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            p.drawText(rect, self.alignment, self.textOn)

        p.end