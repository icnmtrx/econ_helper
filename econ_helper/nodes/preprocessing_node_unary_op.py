from econ_helper.eh_conf import register_node, NODE_TYPE_PREPROCESSING
from econ_helper.nodes.base_node_inout import *

import numpy as np
from pandas.api.types import is_numeric_dtype


@register_node('unary', NODE_TYPE_PREPROCESSING)
class Node_UnaryOp(BaseInOutNode):
    op_code = 'unary'
    type_code = NODE_TYPE_PREPROCESSING
    op_title = 'Unary'
    content_label_objname = 'node_unary'

    operation_name = 'unary'

    def __init__(self, scene, default_node_text='Unary op on'):

        self.available_ops = ['log', 'negate']
        self.op_column = None
        self.op_operation = None

        #GUI
        self.labelColumn = QLabel('Unary op on column')

        self.targetColumn = QComboBox()

        self.operationLabel = QLabel('Available operations')

        self.operationCombo = QComboBox()
        self.operationCombo.addItems(self.available_ops)

        self.addOrReplaceButton = QPushButton('Replace with new value')
        self.addOrReplaceButton.setCheckable(True)

        self.onoff_signals(activate=True)

        super().__init__(scene, default_node_text)

    def onoff_signals(self, activate=True):
        if activate:
            self.targetColumn.currentIndexChanged.connect(self.targetColumnChanged)
            self.operationCombo.currentIndexChanged.connect(self.targetColumnChanged)
            self.addOrReplaceButton.toggled.connect(self.targetColumnChanged)
        else:
            self.targetColumn.currentIndexChanged.disconnect(self.targetColumnChanged)
            self.operationCombo.currentIndexChanged.disconnect(self.targetColumnChanged)
            self.addOrReplaceButton.toggled.disconnect(self.targetColumnChanged)

    def main_node_operation(self, df):
        column = self.targetColumn.currentText()
        op = self.operationCombo.currentText()
        replace = self.addOrReplaceButton.isChecked()

        if column == '' or column not in df.columns:
            column = self.op_column

        if op == '':
            op = self.op_operation

        self.op_column = column if (column != '' and column in df.columns) else None
        self.op_operation = op if op != '' else None

        if column == '' or column not in df.columns:
            return None

        self.op_column = column

        self.operation_name = op
        new_column = None
        new_value = None
        if op == 'log':
            new_column = f'{self.operation_name}({column})'
            new_value = np.log(df[column]).fillna(0)
        elif op == 'negate':
            new_column = f'{self.operation_name}({column})'
            new_value = -1 * df[column]
        else:
            pass

        dfc = df.copy()

        if new_column is not None and new_value is not None:
            dfc.insert(0, new_column, new_value)
            if replace:
                dfc = dfc.drop(columns=[column])

#        self.op_column = column
#        self.op_operation = op

        return dfc

    def update_ui(self):
        self.onoff_signals(activate=False)

        self.targetColumn.clear()

        if self.input_value is not None:
            self.targetColumn.addItems(self.input_value.columns)
            for i in range(self.targetColumn.count()):
                item = self.targetColumn.itemText(i)
                if item in self.input_value.columns and is_numeric_dtype(self.input_value[item]):
                    self.targetColumn.model().item(i).setEnabled(True)
                else:
                    self.targetColumn.model().item(i).setEnabled(False)
        else:
            self.markInvalid(error_message='Input is not connected')

        self.targetColumn.setCurrentIndex(-1)

        if self.op_column is not None:
            idx = self.targetColumn.findText(self.op_column, Qt.MatchExactly)
            if idx >= 0:
                self.targetColumn.setCurrentIndex(idx)
                self.op_column = self.targetColumn.currentText()
        else:
            self.markInvalid(error_message='Select column')

        self.operationCombo.setCurrentIndex(-1)
        if self.op_operation is not None:
            idx = self.operationCombo.findText(self.op_operation, Qt.MatchExactly)
            if idx >= 0:
                self.operationCombo.setCurrentIndex(idx)
                self.op_operation = self.operationCombo.currentText()
        else:
            #pass
            self.markInvalid(error_message='Select operation')

        if not self.isInvalid():
            op = self.operationCombo.currentText().capitalize()
            self.content.default_node_text = op
            new_text = self.content.default_node_text + ' ' + self.targetColumn.currentText()
            self.content.edit.setText(new_text)

        self.onoff_signals(activate=True)

    def targetColumnChanged(self):
        self.markInvalid()
        self.eval()
        self.update_ui()

    def create_settings_widget(self):
        w = QWidget()
        lo = QVBoxLayout(w)

        lo.addWidget(self.labelColumn)
        lo.addWidget(self.targetColumn)
        lo.addWidget(self.operationLabel)
        lo.addWidget(self.operationCombo)
        lo.addWidget(self.addOrReplaceButton)

        vertSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        lo.addItem(vertSpacer)

        w.setLayout(lo)

        return w


    def serialize(self):
        res = super().serialize()

        res['op_column'] = self.targetColumn.currentText()
        res['op'] = self.operationCombo.currentText()

        return res

    def deserialize(self, data, hashmap={}, restore_id=True, **kwargs):
        res = super().deserialize(data, hashmap)
        try:
            self.op_column = data['op_column']
            self.op_operation = data['op']

            return True & res
        except Exception as e:
            dumpException(e)
        return res