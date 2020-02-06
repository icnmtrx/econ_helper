from collections import OrderedDict

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import *

from nodeeditor.node_serializable import Serializable


class QDMNodeContentWidget(QWidget, Serializable):
    def __init__(self, node, parent=None):
        self.node = node
        super().__init__(parent)

        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)
        self.setLayout(self.layout)

        self.wdg_label = QLabel("Some Title")
        self.layout.addWidget(self.wdg_label)
        self.layout.addWidget(QDMTextEdit("foo"))




    def setEditingFlag(self, value):
        self.node.scene.getView().editingFlag = value

    def serialize(self):
        return OrderedDict([

        ])

    def deserialize(self, data, hashmap={}):
        return True

class QDMTextEdit(QTextEdit):
    def focusInEvent(self, event):
        self.parentWidget().setEditingFlag(True)
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self.parentWidget().setEditingFlag(False)
        super().focusOutEvent(event)


class ImprovedPlainTextEdit(QTextEdit):

    def setText(self, p_str):
        self.setFontFamily("Courier New")
        self.setFontPointSize(10)
        self.setPlainText(p_str)
        if self.parent() is not None:
            self.setMaximumWidth(self.parent().width())
        self.update()

    def text(self):
        return self.toPlainText()

