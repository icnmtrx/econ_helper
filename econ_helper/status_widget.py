from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *

from econ_helper.eh_node_base import EcoNode


class StatusWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.splitter = QSplitter()
#        self.splitter.addWidget(QWidget())
#        self.splitter.addWidget(QWidget())

        self.stretch = [1, 3]

        self.setLayout(self.layout)

    def initUI(self):
        pass

    # def set_stretch(self, stretch):
    #     self.stretch = stretch

    def nodeListener(self, node):
        self.clear_status()
        if isinstance(node, EcoNode):
    #        spLeft = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
    #        spLeft.setHorizontalStretch( self.stretch[0] )
    #        node.settings_widget.setSizePolicy(spLeft)
            old_settings_widget = self.splitter.widget(0)
            if old_settings_widget is not None:
                self.splitter.replaceWidget(0, node.settings_widget)
            else:
                self.splitter.addWidget(node.settings_widget)
            #self.layout.addWidget(self.splitter_left)

    #        spRight = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
    #        spRight.setHorizontalStretch( self.stretch[1] )
    #        node.output_widget.setSizePolicy(spRight)
            old_output_widget = self.splitter.widget(1)
            if old_output_widget is not None:
                self.splitter.replaceWidget(1, node.output_widget)
            else:
                self.splitter.addWidget(node.output_widget)

            self.splitter.setSizes([self.splitter.size().width() * 0.30,
                                    self.splitter.size().width() * 0.70])
            self.layout.addWidget(self.splitter)

        self.layout.update()

    def clear_status(self):
        self.layout.removeWidget(self.splitter)
        while self.layout.count() > 0:
            item = self.layout.takeAt(0)
            if not item:
                continue
            w = item.widget()
            if w:
                self.layout.removeWidget(w)
                w.setParent(None)

