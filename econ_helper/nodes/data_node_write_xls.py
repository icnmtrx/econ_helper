from econ_helper.eh_node_base import *
from econ_helper.eh_conf import *
from nodeeditor.node_node import SOCKET_TYPE_DF
from nodeeditor.utils import dumpException
from econ_helper.pandas_model import PandasModel

import os
import pandas as pd


class XlsWriterContent(QDMNodeContentWidget):
    def initUI(self):
        self.edit = QPlainTextEdit('Excel Writer', self)
        self.edit.setReadOnly(True)
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


@register_node('write_xls', NODE_TYPE_DATA_DEST)
class Node_WriteXls(EcoNode):
    op_code = 'write_xls'
    type_code = NODE_TYPE_DATA_DEST
    op_title = 'Write XLS'
    content_label_objname = 'node_write_xls'

    def __init__(self, scene, default_node_text=None):
        self.default_node_text = default_node_text
        self.input_value = None

        self.data_filename = None
        self.buttonSelectFile = QPushButton('Save file as..')

        self.labelFileName = QLabel('File name')
        self.labelFileName.setVisible(False)

        self.onoff_signals(activate=True)

        super().__init__(scene, inputs=[SOCKET_TYPE_DF], outputs=[])

    def onoff_signals(self, activate=True):
        if activate:
            self.buttonSelectFile.clicked.connect(self.buttonSelectFileClicked)
        else:
            self.buttonSelectFile.clicked.disconnect(self.buttonSelectFileClicked)

    def initInnerClasses(self):
        self.content = XlsWriterContent(self)
        self.grNode = EcoGraphicsNode(self)
        if self.default_node_text is not None:
            self.content.default_node_text = self.default_node_text

    def adjust_table_width(self):
        if self.table is None:
            return
        header = self.table.horizontalHeader()
        for column in range(header.count()):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
            width = header.sectionSize(column)
            header.setSectionResizeMode(column, QHeaderView.Interactive)
            header.resizeSection(column, width)



    def evalImplementation(self):
        self.input_value = None

        input_value, socket_type = self.get_guarded_input(0)

        if input_value is None \
                or socket_type is not SOCKET_TYPE_DF \
                or not isinstance(input_value, pd.DataFrame):
            #print(f'Input is not valid to node {self.__class__.__name__}')
            self.grNode.setToolTip("Input is not valid")
            self.markInvalid()
            return None

        self.input_value = input_value
        self.output_value = self.input_value
        #print(f'Main node op done for node {self.__class__.__name__}')

        if self.output_value is not None:
            self.dataModel = PandasModel(self.output_value)
            self.table.setModel(self.dataModel)
            self.adjust_table_width()
            self.table.show()

            self.markDirty(False)
            self.markInvalid(False)

            self.grNode.setToolTip("")

        return self.output_value

    def buttonSelectFileClicked(self):
        # TODO: save instantly
        # (now its saved only after explicit button click)

        fname = QFileDialog.getSaveFileName(None, 'Save file', directory='.')
        if fname[0]:
            try:
                self.output_value.to_excel(fname[0], sheet_name='econ_helper-output')
                self.data_filename = os.path.basename(fname[0])
                self.labelFileName.setText(f'File name: {self.data_filename}')
                self.labelFileName.setVisible(True)

                self.markDirty()

            except Exception as e:
                self.markInvalid()
                # self.content = None
                self.output_value = {}
                self.data_filename = None
                self.labelFileName.setVisible(False)
                raise

    def create_settings_widget(self):
        w = QWidget()
        lo = QVBoxLayout(w)
        lo.addWidget(QLabel(f'{self.title} settings'))

        lo.addWidget(self.buttonSelectFile)
        lo.addWidget(self.labelFileName)

        vertSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        lo.addItem(vertSpacer)

        w.setLayout(lo)

        return w

    def create_output_widget(self):
        w = QWidget()
        lo = QVBoxLayout(w)
        lo.addWidget(QLabel(f'{self.title} output'))

        self.table = QTableView()
        self.dataModel = PandasModel()
        self.table.setModel(self.dataModel)
        self.adjust_table_width()

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
