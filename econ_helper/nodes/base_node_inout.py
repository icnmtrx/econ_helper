import traceback

import pandas as pd

from econ_helper.eh_node_base import *
from econ_helper.pandas_model import PandasModel
from nodeeditor.node_content_widget import ImprovedPlainTextEdit
from nodeeditor.node_node import SOCKET_TYPE_DF
from nodeeditor.utils import dumpException

pd.options.display.float_format = '{:,.4f}'.format


class BaseNodeContent(QDMNodeContentWidget):

    def __init__(self, node, default_node_text=None):
        self.default_node_text = default_node_text
        self.edit = None
        super().__init__(node)

    def initUI(self):
        if self.default_node_text is not None:
            self.edit = ImprovedPlainTextEdit(self.default_node_text, self)
        else:
            self.edit = ImprovedPlainTextEdit('None', self)
        self.edit.setMaximumWidth(self.width())
        self.edit.setObjectName(self.node.content_label_objname)
        pass

    def serialize(self):
        res = super().serialize()
        res['value'] = self.edit.toPlainText()
        return res

    def deserialize(self, data, hashmap={}):
        res = super().deserialize(data, hashmap)
        try:
            value = data['value']
            self.edit.setPlainText(value)
            return True & res
        except Exception as e:
            dumpException(e)
        return res


class BaseInOutNode(EcoNode):

    def __init__(self, scene, default_node_text=None):
        self.default_node_text = default_node_text
        self.input_value = None
        self.content = None
        self.grNode = None

        super().__init__(scene, inputs=[SOCKET_TYPE_DF], outputs=[SOCKET_TYPE_DF])

    def initInnerClasses(self):
        self.content = BaseNodeContent(self)
        self.grNode = EcoGraphicsNode(self)
        if self.default_node_text is not None:
            self.content.default_node_text = self.default_node_text

    def main_node_operation(self, df):
        raise NotImplementedError

    def adjust_table_width(self):
        if self.table is None:
            return
        header = self.table.horizontalHeader()
        for column in range(header.count()):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
            width = header.sectionSize(column)
            header.setSectionResizeMode(column, QHeaderView.Interactive)
            header.resizeSection(column, width)

    def onMarkedInvalid(self):
        if self.input_value is None:
            logging.debug(f'input is none for {self.__class__.__name__}')
        if self.output_value is None:
            logging.debug(f'output is none for {self.__class__.__name__}')
        super().onMarkedInvalid()

    def markInvalid(self, new_value=True, error_message='Something went wrong'):
        super().markInvalid(new_value, error_message)
        if new_value:
            logging.debug(f'invalidate node {self.__class__.__name__} with message {error_message}')
        else:
            logging.debug(f'node {self.__class__.__name__} marked valid')

        if new_value and self.error_message is not None:
            self.content.edit.setText(error_message)

    def evalImplementation(self):
        self.input_value = None
        input_value, socket_type = self.get_guarded_input(0)

        if input_value is None \
                or socket_type is not SOCKET_TYPE_DF \
                or not isinstance(input_value, pd.DataFrame):
            print(f'Input is not valid to node {self.__class__.__name__}')
            self.grNode.setToolTip("Input is not valid")
            self.markInvalid()
            return None

        logging.debug(f'evaluating connection -> {self.__class__.__name__}')

        need_update_children = False
        self.input_value = input_value
        try:
            new_output_value = self.main_node_operation(self.input_value)
            if new_output_value is not None \
                    and isinstance(new_output_value, pd.DataFrame) \
                    and not new_output_value.equals(self.output_value):
                self.output_value = new_output_value
                need_update_children = True

            if new_output_value is None:
                self.markInvalid(error_message='Check node configuration')
        except Exception as e:
            logging.error(e)
            traceback.print_tb(e.__traceback__)
            self.output_value = None
            self.markInvalid(error_message='Internal node error. See log for details')

        logging.debug(f'Main node operation done for node {self.__class__.__name__}')

        if self.output_value is not None:
            self.dataModel = PandasModel(self.output_value)
            self.dataModel.set_paint_callback(self.dataModel.default_paint_callback)
            self.table.setModel(self.dataModel)
            self.adjust_table_width()
            self.table.show()

            self.markDirty(False)
            self.markInvalid(False)

            self.markDescendantsInvalid(False)

            if need_update_children:
                logging.debug(f'Node {self.__class__.__name__} makes descendants dirty')
                # self.markDescendantsDirty()
                self.markChildrenDirty()

            self.grNode.setToolTip("")

        logging.debug(f'evaluation completed for node {self.__class__.__name__}')

        return [self.output_value]

    def update_ui(self):
        pass

    def onUnmarkedInvalid(self):
        super().onUnmarkedInvalid()
        self.update_ui()

    def onMarkedDirty(self):
        super().onMarkedDirty()
        self.eval()
        self.update_ui()

    def create_settings_widget(self):
        pass

    def create_output_widget(self, title=None):
        w = QWidget()
        lo = QVBoxLayout(w)
        if title is None:
            lo.addWidget(QLabel(f'{self.title} output'))
        else:
            lo.addWidget(QLabel(title))

        self.table = QTableView()
        #        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.dataModel = PandasModel()
        self.table.setModel(self.dataModel)
        self.adjust_table_width()
        # self.table.horizontalHeader().resizeSections(QHeaderView.ResizeToContents)

        lo.addWidget(self.table)

        w.setLayout(lo)
        return w

    def serialize(self):
        res = super().serialize()

        # res['json_value'] = self.value.to_json() if self.value is not None else None

        return res

    def deserialize(self, data, hashmap={}, restore_id=True, **kwargs):
        res = super().deserialize(data, hashmap)
        try:
            # self.value = pd.read_json(data['json_value'])
            # self.eval()
            return True & res
        except Exception as e:
            dumpException(e)
        return res
