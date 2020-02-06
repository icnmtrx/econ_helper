import os

import pandas as pd

from econ_helper.eh_conf import *
from econ_helper.eh_node_base import *
from econ_helper.pandas_model import PandasModel
from nodeeditor.node_node import SOCKET_TYPE_DF
from nodeeditor.utils import dumpException


class XlsReaderContent(QDMNodeContentWidget):
    def initUI(self):
        self.edit = QPlainTextEdit('Excel Reader',
                                            self)
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



@register_node('read_xls', NODE_TYPE_DATA_SOURCE)
class Node_ReadXls(EcoNode):
    op_code = 'read_xls'
    type_code = NODE_TYPE_DATA_SOURCE
    op_title = 'Read XLS'
    content_label_objname = 'node_read_xls'

    def __init__(self, scene):
        self.data = {}
        self.current_page = None
        self.output_value = None
        self.data_filename = None

        self.buttonSelectFile = QPushButton('Source file')

        self.labelFileName = QLabel('File name')
        self.labelFileName.setVisible(False)

        self.dropSelectPage = QComboBox()

        self.onoff_signals(activate=True)

        self.dropSelectPage.setVisible(False)

        super().__init__(scene, inputs=[], outputs=[SOCKET_TYPE_DF])

#        self.eval()

    def initInnerClasses(self):
        self.content = XlsReaderContent(self)
        self.grNode = EcoGraphicsNode(self)

        # self.content.edit = QGraphicsSimpleTextItem('Excel Reader with long line to check how it works',
        #                                      self.grNode.content)
        #self.content.edit.textChanged.connect(self.onInputChanged)

    def adjustTableWidth(self):
        if self.table is None:
            return
        header = self.table.horizontalHeader()
        for column in range(header.count()):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
            width = header.sectionSize(column)
            header.setSectionResizeMode(column, QHeaderView.Interactive)
            header.resizeSection(column, width)

    def evalImplementation(self):
        if self.output_value is not None:
            self.dataModel = PandasModel(self.output_value)
            self.table.setModel(self.dataModel)
            self.adjustTableWidth()

            self.table.show()

            self.markDirty(False)
            self.markInvalid(False)

            self.markDescendantsInvalid(False)

            self.markChildrenDirty()
            #self.markDescendantsDirty()

            self.grNode.setToolTip("")
            self.update_ui_on_data()

            #self.evalChildren()

        return self.output_value

    def onoff_signals(self, activate=True):
        if activate:
            self.buttonSelectFile.clicked.connect(self.buttonSelectFileClicked)
            self.dropSelectPage.currentIndexChanged.connect(self.dropSelectChanged)
        else:
            self.buttonSelectFile.clicked.disconnect(self.buttonSelectFileClicked)
            self.dropSelectPage.currentIndexChanged.disconnect(self.dropSelectChanged)


    def update_ui_on_data(self):
        self.onoff_signals(activate=False)

        if self.data_filename is not None:
            self.labelFileName.setText(f'File name: {self.data_filename}')
            self.labelFileName.setVisible(True)

        pages = self.data.keys()
        self.dropSelectPage.clear()
        self.dropSelectPage.addItems(pages)

        if self.current_page is not None:
            idx = self.dropSelectPage.findText(self.current_page, Qt.MatchExactly)
            if idx >= 0:
                self.dropSelectPage.setCurrentIndex(idx)
            self.dropSelectPage.setVisible(True)

        self.onoff_signals(activate=True)

        # if self.data is not None \
        #     and self.current_page is not None \
        #     and self.current_page in self.data:
        #     self.output_value = self.data[self.current_page]
        #
        # self.eval()
        # self.evalChildren()
    def onMarkedDirty(self):
        pass
        # print(f'{self.__class__.__name__} marked dirty')



    def buttonSelectFileClicked(self):
        fname = QFileDialog.getOpenFileName(None, 'Open file', '.')
        if fname[0]:
            try:
                xlsdata = pd.ExcelFile(fname[0])
                for sheet in xlsdata.sheet_names:
                    self.data[sheet] = xlsdata.parse(sheet)

                self.data_filename = os.path.basename(fname[0])
                self.labelFileName.setText(f'File name: {self.data_filename}')
                self.labelFileName.setVisible(True)

                self.dropSelectPage.addItems(self.data.keys())
                self.dropSelectPage.setVisible(True)

                self.current_page = list(self.data.keys())[0]
                self.output_value = self.data[self.current_page]

                #for c in self.output_value.columns:
                #    print(c, self.output_value[c].dtype)

                self.markDirty()
                #self.markDescendantsDirty()
                self.eval()
            except Exception as e:
                self.markInvalid()
                #self.content = None
                self.data = {}
                self.data_filename = None
                self.dropSelectPage.setVisible(False)
                self.labelFileName.setVisible(False)
                raise

    def dropSelectChanged(self):
        if self.data is None:
            return
        previous_page = self.current_page
        self.current_page = self.dropSelectPage.currentText()
        if previous_page == self.current_page:
            #nothing changed
            return

        self.output_value = self.data[self.current_page]
        self.update_ui_on_data()

        self.markDirty()
        self.markChildrenDirty()

    #        self.eval()
#        self.evalChildren()

    def create_settings_widget(self):
        w = QWidget()
        lo = QVBoxLayout(w)
        lo.addWidget(QLabel(f'{self.title} settings') )

        lo.addWidget(self.buttonSelectFile)
        lo.addWidget(self.labelFileName)
        lo.addWidget(self.dropSelectPage)

        vertSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        lo.addItem(vertSpacer)

        w.setLayout(lo)

        self.update_ui_on_data()

        return w

    def create_output_widget(self):
        w = QWidget()
        lo = QVBoxLayout(w)
        lo.addWidget(QLabel(f'{self.title} output') )

        self.table = QTableView()
#        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.dataModel = PandasModel()
        self.table.setModel(self.dataModel)
        self.table.horizontalHeader().resizeSections(QHeaderView.ResizeToContents)

        self.adjustTableWidth()


        #self.table.show()
        lo.addWidget(self.table)

        w.setLayout(lo)
        self.update_ui_on_data()
        return w

    def serialize(self):
        res = super().serialize()

        res['filename'] = self.data_filename
        res['current_page'] = self.dropSelectPage.currentText()
        serialized_data = {}
        for page in self.data.keys():
            serialized_data[page] = self.data[page].to_json(orient='table')
        res['json_value'] = serialized_data

        return res

    def deserialize(self, data, hashmap={}, restore_id=True, **kwargs):
        res = super().deserialize(data, hashmap)
        try:
            self.data_filename = data['filename']
            self.current_page = data['current_page']
            serialized_data = data['json_value']
            for k in serialized_data.keys():
                self.data[k] = pd.read_json(serialized_data[k], orient='table')

            first_key = list(self.data.keys())[0]
            self.output_value = self.data[self.current_page] if self.current_page in self.data else self.data[first_key]

            #self.update_ui_on_data()

            return True & res
        except Exception as e:
            dumpException(e)
        return res