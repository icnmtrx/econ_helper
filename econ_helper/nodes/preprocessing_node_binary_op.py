from econ_helper.eh_conf import register_node, NODE_TYPE_PREPROCESSING
from econ_helper.nodes.base_node_inout import *
from pandas.api.types import is_numeric_dtype


@register_node('binary', NODE_TYPE_PREPROCESSING)
class Node_BinaryOp(BaseInOutNode):
    op_code = 'binary'
    type_code = NODE_TYPE_PREPROCESSING
    op_title = 'Binary'
    content_label_objname = 'node_binary'

    operation_name = 'binary'

    def __init__(self, scene, default_node_text='Binary op on'):

        self.available_ops = ['sum', 'diff', 'mult', 'div']
        self.op_column_1st = None
        self.op_column_2nd = None
        self.op_operation = None

        # GUI
        self.labelColumn = QLabel('Binary op on columns')

        self.targetColumnFirst = QComboBox()

        self.targetColumnSecond = QComboBox()

        self.operationLabel = QLabel('Available operations')

        self.operationCombo = QComboBox()
        self.operationCombo.addItems(self.available_ops)

        self.onoff_signals(activate=True)

        super().__init__(scene, default_node_text)

    def onoff_signals(self, activate=True):
        if activate:
            self.targetColumnFirst.currentIndexChanged.connect(self.targetColumnChanged)
            self.targetColumnSecond.currentIndexChanged.connect(self.targetColumnChanged)
            self.operationCombo.currentIndexChanged.connect(self.targetColumnChanged)
        else:
            self.targetColumnFirst.currentIndexChanged.disconnect(self.targetColumnChanged)
            self.targetColumnSecond.currentIndexChanged.disconnect(self.targetColumnChanged)
            self.operationCombo.currentIndexChanged.disconnect(self.targetColumnChanged)


    def main_node_operation(self, df):
        dfc = None
        column_first = self.targetColumnFirst.currentText()
        column_second = self.targetColumnSecond.currentText()
        op = self.operationCombo.currentText()

        if column_first == '' or column_first not in df.columns:
            column_first = self.op_column_1st
        if column_second == '' or column_second not in df.columns:
            column_second = self.op_column_2nd
        if op == '':
            op = self.op_operation

        self.op_column_1st = column_first if (column_first != '' and column_first in df.columns) else None
        self.op_column_2nd = column_second if (column_second != '' and column_second in df.columns) else None
        self.op_operation = op if op != '' else None

        if column_first == '' or column_second == '' \
                or column_first not in df.columns \
                or column_second not in df.columns:
            return None

        new_column = None
        new_value = None
        self.operation_name = op
        if op == 'sum':
            new_column = f'({column_first}) + ({column_second})'
            new_value = df[column_first] + df[column_second]
        elif op == 'diff':
            new_column = f'({column_first}) - ({column_second})'
            new_value = df[column_first] - df[column_second]
        elif op == 'mult':
            new_column = f'({column_first}) * ({column_second})'
            new_value = df[column_first] * df[column_second]
        elif op == 'div':
            new_column = f'({column_first}) / ({column_second})'
            new_value = df[column_first] / df[column_second]
        else:
            pass

        if new_column is not None and new_value is not None:
            dfc = df.copy()
            dfc.insert(0, new_column, new_value)

        self.op_column_1st = column_first
        self.op_column_2nd = column_second
        self.op_operation = op

        return dfc

    def update_ui(self):
        self.onoff_signals(activate=False)

        self.targetColumnFirst.clear()
        self.targetColumnSecond.clear()

        if self.input_value is not None:
            self.targetColumnFirst.addItems(self.input_value.columns)
            for i in range(self.targetColumnFirst.count()):
                item = self.targetColumnFirst.itemText(i)
                if item in self.input_value.columns and is_numeric_dtype(self.input_value[item]):
                    self.targetColumnFirst.model().item(i).setEnabled(True)
                else:
                    self.targetColumnFirst.model().item(i).setEnabled(False)

            self.targetColumnSecond.addItems(self.input_value.columns)
            for i in range(self.targetColumnSecond.count()):
                item = self.targetColumnSecond.itemText(i)
                if item in self.input_value.columns and is_numeric_dtype(self.input_value[item]):
                    self.targetColumnSecond.model().item(i).setEnabled(True)
                else:
                    self.targetColumnSecond.model().item(i).setEnabled(False)
        else:
            self.markInvalid(error_message='Input is not connected')

        self.targetColumnFirst.setCurrentIndex(-1)
        self.targetColumnSecond.setCurrentIndex(-1)

        if self.op_column_1st is not None:
            idx = self.targetColumnFirst.findText(self.op_column_1st, Qt.MatchExactly)
            if idx >= 0:
                self.targetColumnFirst.setCurrentIndex(idx)
                self.op_column_1st = self.targetColumnFirst.currentText()
        else:
            self.markInvalid(error_message='Select first column')

        if self.op_column_2nd is not None:
            idx = self.targetColumnSecond.findText(self.op_column_2nd, Qt.MatchExactly)
            if idx >= 0:
                self.targetColumnSecond.setCurrentIndex(idx)
                self.op_column_2nd = self.targetColumnSecond.currentText()
        else:
            self.markInvalid(error_message='Select second column')

        self.operationCombo.setCurrentIndex(-1)
        if self.op_operation is not None:
            idx = self.operationCombo.findText(self.op_operation, Qt.MatchExactly)
            if idx >= 0:
                self.operationCombo.setCurrentIndex(idx)
                self.op_operation = self.operationCombo.currentText()
        else:
            self.markInvalid(error_message='Select operation')

        if not self.isInvalid():
            op = self.operationCombo.currentText().capitalize()
            self.content.default_node_text = op
            new_text = (self.content.default_node_text
                        + f' ({self.targetColumnFirst.currentText()}, {self.targetColumnSecond.currentText()})')
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
        lo.addWidget(self.targetColumnFirst)
        lo.addWidget(self.targetColumnSecond)
        lo.addWidget(self.operationLabel)
        lo.addWidget(self.operationCombo)

        vertSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        lo.addItem(vertSpacer)

        w.setLayout(lo)

        return w

    def serialize(self):
        res = super().serialize()

        res['op_column_1st'] = self.targetColumnFirst.currentText()
        res['op_column_2nd'] = self.targetColumnSecond.currentText()
        res['op'] = self.operationCombo.currentText()

        return res

    def deserialize(self, data, hashmap={}, restore_id=True, **kwargs):
        res = super().deserialize(data, hashmap)
        try:
            self.op_column_1st = data['op_column_1st']
            self.op_column_2nd = data['op_column_2nd']
            self.op_operation = data['op']

            return True & res
        except Exception as e:
            dumpException(e)
        return res
