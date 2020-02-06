import logging
from typing import Tuple

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from nodeeditor.node_node import Node
from nodeeditor.node_content_widget import QDMNodeContentWidget
from nodeeditor.node_graphics_node import QDMGraphicsNode
from nodeeditor.node_socket import LEFT_CENTER, RIGHT_CENTER
from nodeeditor.utils import dumpException


class EcoGraphicsNode(QDMGraphicsNode):

    def initSizes(self):
        super().initSizes()
        self.width = 220
        self.height = 140
        self.edge_roundness = 6
        self.edge_padding = 0
        self.title_horizontal_padding = 8
        self.title_vertical_padding = 10

    def initAssets(self):
        super().initAssets()
        self.icons = QImage("icons/status_icons.png")


    def paint(self, painter, QStyleOptionGraphicsItem, widget=None):
        super().paint(painter, QStyleOptionGraphicsItem, widget)

        offset = 24.0
        if self.node.isDirty():
            offset = 0.0
        if self.node.isInvalid():
            offset = 48.0

        painter.drawImage(
            QRectF(-20, -20, 24.0, 24.0),
            self.icons,
            QRectF(offset, 0, 24.0, 24.0)
        )


class EcoContent(QDMNodeContentWidget):
    def initUI(self):
        lbl = QLabel(self.node.content_label, self)
        lbl.setObjectName(self.node.content_label_objname)


class EcoNode(Node):
    icon = ""
    op_code = 0
    type_code = 'None'
    op_title = "Undefined"
    content_label = ""
    content_label_objname = "eco_node_bg"

    signalMouseRelease = pyqtSignal()

    def __init__(self, scene, inputs=None, outputs=None):
        if outputs is None:
            outputs = [1]
        if inputs is None:
            inputs = [1]
        self.node_settings_widget = None
        self.node_output_widget = None
        self.output_value = None

        super().__init__(scene, self.__class__.op_title, inputs, outputs)

        self.node_settings_widget = self.create_settings_widget()
        self.node_output_widget = self.create_output_widget()

        # it's really important to mark all nodes Dirty by default
        self.markDirty()

    @property
    def settings_widget(self):
        return self.node_settings_widget

    @property
    def output_widget(self):
        return self.node_output_widget

    def create_settings_widget(self):
        w = QWidget()
        lo = QVBoxLayout(w)
        lo.setContentsMargins(0, 0, 0, 0);
        lo.addWidget(QLabel(f'Settings placeholder for {self.title}'))
        w.setLayout(lo)
        return w

    def create_output_widget(self):
        w = QWidget()
        lo = QVBoxLayout(w)
        lo.setContentsMargins(0, 0, 0, 0);
        lo.addWidget(QLabel(f'Output placeholder for {self.title}'))
        w.setLayout(lo)
        return w

    def initInnerClasses(self):
        self.content = EcoContent(self)
        self.grNode = EcoGraphicsNode(self)

    #        self.signalMouseRelease.emit()

    def initSettings(self):
        super().initSettings()
        self.input_socket_position = LEFT_CENTER
        self.output_socket_position = RIGHT_CENTER

    def evalImplementation(self):
        raise NotImplementedError

    def get_guarded_input(self, idx):
        other_socket = self.getInputSocket(idx)

        none_result: Tuple[None, None] = (None, None)

        if other_socket is None:
            #print(f'Input is not connected to node {self.__class__.__name__}')
            self.grNode.setToolTip("Input is not connected")
            self.markInvalid()
            return none_result

        if not (hasattr(other_socket, 'node')
                and hasattr(other_socket, 'index')
                and hasattr(other_socket, 'socket_type')
        ):
            #print(f'Socket is not valid to node {self.__class__.__name__}')
            self.grNode.setToolTip("Connection is not valid")
            self.markInvalid()
            return none_result

        input_node = other_socket.node
        input_idx = other_socket.index
        socket_type = other_socket.socket_type

        if input_node is None \
                or not hasattr(input_node, 'get_output'):
            logging.debug(f'Input is not connected to node {self.__class__.__name__}')
            self.grNode.setToolTip("Input is not connected")
            self.markInvalid(error_message='Input is not connected')
            return none_result

        input_value = input_node.get_output(input_idx)
        return input_value, socket_type

    def get_output(self, socket=0):
        if self.output_value is None:
            return None
        if not self.isDirty() and not self.isInvalid():
            if socket < 0:
                return self.output_value

            if (not isinstance(self.output_value, list)) \
                and (not isinstance(self.output_value, dict)) \
                    and socket == 0:
                return self.output_value

            if isinstance(self.output_value, list) \
                    and 0 <= socket < len(self.output_value):
                return self.output_value[socket]

            if isinstance(self.output_value, dict) \
                    and socket in self.output_value:
                return self.output_value[socket]

        return None

    def eval(self):
        clname = self.__class__.__name__
        logging.debug(f'Requested evaluating {clname}')
        if not self.isDirty() and not self.isInvalid():
            logging.debug(f"no need to eval {self.__class__.__name__}, returning cached %s value" )
            return self.output_value

        #logging.debug(f"performing eval {self.__class__.__name__}")

        try:
            return self.evalImplementation()
        except ValueError as e:
            self.markInvalid()
            self.grNode.setToolTip(str(e))
            raise
            # self.markDescendantsDirty()

        except Exception as e:
            self.markInvalid()
            self.grNode.setToolTip(str(e))
            dumpException(e)

    def markInvalid(self, new_value=True, error_message='Something went wrong'):
        if new_value:
            self.grNode.change_title_color(Qt.red)
        else:
            self.grNode.change_title_color(Qt.white)
        super().markInvalid(new_value, error_message)

    def markDirty(self, new_value=True):
        if new_value:
            self.grNode.change_title_color(Qt.yellow)
        else:
            self.grNode.change_title_color(Qt.white)
        super().markDirty(new_value)

    def onInputChanged(self, new_edge):
        #logging.debug("%s::__onInputChanged" % self.__class__.__name__)
        self.markInvalid()
        self.markDirty()
        self.markDescendantsDirty()

    def serialize(self):
        res = super().serialize()
        res['op_code'] = self.__class__.op_code
        res['type_code'] = self.__class__.type_code
        # logging.debug(f"Serialized EcoNode {self.__class__.__name__}, result {res}" )
        return res

    def deserialize(self, data, hashmap={}, restore_id=True):
        res = super().deserialize(data, hashmap, restore_id)
        # logging.debug(f"Deserialized EcoNode {self.__class__.__name__}, result {res}")
        return res
