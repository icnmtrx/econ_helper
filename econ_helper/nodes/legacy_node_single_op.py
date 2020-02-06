from econ_helper.eh_node_base import *
from econ_helper.eh_conf import *
from nodeeditor.node_serializable import Serializable
from nodeeditor.utils import dumpException
from econ_helper.pandas_model import PandasModel

import pandas as pd

# predefined operations:
#     + column index as diff between current and previous, in procents
#     ---- diff between column and mean value of another column
#     + trend calculation by column
#     + adstock by column (recommend values, but the user has to show it)
#     + add lag by column
#     + calculate season factor by column (manually select window size)
#     ---- calculate SOV: competitors trp, our trp.  our/competitors, in procents
#     + calculate deseasoned target column
#     + composition of two manually selected columns (sum, diff, mult, log)

class Operation(Serializable):
    operation_name = 'nothing'

    def getGui(self):
        return None

    def apply(self, df, column, extra_param):
        return df.copy()

    def serialize(self):
        res = super().serialize()
        res['operation_name'] = self.operation_name
        return res

    def deserialize(self, data, hashmap={}):
        res = super().deserialize(data, hashmap)
        try:
            value = data['operation_name']
            self.operation_name = value
            return True & res
        except Exception as e:
            dumpException(e)
        return res


class TrendOperation(Operation):
    operation_name = 'trend'

    def apply(self, df, column, extra_param=None):
        dfc = df.copy()
        x = list(range(dfc[column].shape[0]))
        new_column = column + ' ' + self.operation_name
        x = sm_tools.add_constant(x)  # Add constant
        ols_model = sm.OLS(dfc[column], x)  # Initialize model
        ols_result = ols_model.fit()  # Fit model
        trend_data = ols_result.predict(x)
        dfc[new_column] = trend_data
        return dfc


class LagOperation(Operation):
    operation_name = 'lag'

    def __init__(self):
        super().__init__()
        self.extra_control = None

    def getGui(self, parent=None):
        w = QWidget()
        lo = QVBoxLayout(w)

        if self.extra_control is None:
            self.extra_control = QSlider(parent)
            self.extra_control.setOrientation(Qt.Horizontal)
            self.extra_control.setValue(1)
            self.extra_control.setMaximum(99)
            self.extra_control.setMinimum(1)

        lo.addWidget(self.extra_control)

        w.setLayout(lo)
        return w

    def apply(self, df, column, extra_param=None):
        lag_size = -1
        dfc = df.copy()
        if self.extra_control is not None:
            lag_size = self.extra_control.value()
        else:
            if extra_param is not None:
                lag_size = extra_param

        if lag_size < 0:
            return dfc

        new_column = column + ' ' + self.operation_name + f'{lag_size}'
        dfc[new_column] = dfc[column].shift(lag_size).fillna(0)
        return dfc

    def serialize(self):
        res = super().serialize()
        res['extra_param'] = self.extra_control.value
        return res

    def deserialize(self, data, hashmap={}):
        res = super().deserialize(data, hashmap)
        try:
            value = data['extra_param']
            self.extra_control.setValue(value)
            return True & res
        except Exception as e:
            dumpException(e)
        return res


class OperationContent(QDMNodeContentWidget):

    def initUI(self):
        self.default_node_text = 'Op'
        self.edit = QLineEdit(self.default_node_text, self)
        self.edit.setAlignment(Qt.AlignLeft)
        self.edit.setObjectName(self.node.content_label_objname)
        pass

    def serialize(self):
        res = super().serialize()
        res['value'] = self.edit.text()
        return res

    def deserialize(self, data, hashmap={}):
        res = super().deserialize(data, hashmap)
        try:
            value = data['value']
            self.edit.setText(value)
            return True & res
        except Exception as e:
            dumpException(e)
        return res



#@register_node('operation')
class Node_Operation(EcoNode):
    op_code = 'operation'
    op_title = 'Column operation'
    content_label_objname = 'node_operation'

    def __init__(self, scene):
        super().__init__(scene, inputs=[1], outputs=[1])
        self.eval()

        self.operations = [LagOperation(), TrendOperation()]
        self.extra_widget = None

    def initInnerClasses(self):
        self.content = OperationContent(self)
        self.grNode = EcoGraphicsNode(self)


    def evalImplementation(self):

        input = self.getInput(0)
        if input is not None and hasattr(input, 'value'):
            input = input.value

        self.value = None

        if input is None:
            return input
        self.value = input.copy()
        self.value = self.do_operation()

        if self.value is not None:
            self.dataModel = PandasModel(self.value)
            self.table.setModel(self.dataModel)
            self.table.show()

            self.markDirty(False)
            self.markInvalid(False)

            self.markDescendantsInvalid(False)
            #self.markDescendantsDirty()

            self.grNode.setToolTip("")

            self.evalChildren()

        return self.value

    def onInputChanged(self, new_edge):
        super().onInputChanged(new_edge)
        self.targetColumn.clear()
        self.targetColumn.addItems(self.value.columns)

    def targetColumnChanged(self):
        self.markDirty()
        self.eval()
        new_text = self.content.default_node_text + ' ' + self.targetColumn.currentText()
        self.content.edit.setText(new_text)

    def operationChanged(self):
        op = self.operations[self.dropOperation.currentIndex()]
        gui = op.getGui()
        self.extra_widget = gui

    def create_settings_widget(self):
        w = QWidget()
        lo = QVBoxLayout(w)
        lo.addWidget(QLabel(f'{self.title} settings') )

        self.labelColumn = QLabel('Target column')

        self.targetColumn = QComboBox()
        if self.value is not None:
            self.targetColumn.addItems(self.value.columns)
        self.targetColumn.currentIndexChanged.connect(self.targetColumnChanged)

        lo.addWidget(self.targetColumn)

        self.dropOperation = QComboBox()
        for op in self.operations:
            self.dropOperation.addItem(op.operation_name)
        self.dropOperation.currentIndexChanged.connect(self.operationChaned)

        self.extra_widget = QWidget()
        lo.addWidget(self.extra_widget)


        vertSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        lo.addItem(vertSpacer)

        w.setLayout(lo)

        return w

    def create_output_widget(self):
        w = QWidget()
        lo = QVBoxLayout(w)
        lo.addWidget(QLabel(f'{self.title} output') )

        self.table = QTableView()
        self.dataModel = PandasModel()
        self.table.setModel(self.dataModel)
        #self.table.show()
        lo.addWidget(self.table)

        w.setLayout(lo)
        return w

    def serialize(self):
        res = super().serialize()

        res['target_column'] = self.targetColumn.currentText()
        res['json_value'] = self.value.to_json() if self.value is not None else None

        return res

    def deserialize(self, data, hashmap={}, **kwargs):
        res = super().deserialize(data, hashmap)
        try:
            self.value = pd.read_json(data['json_value'])
            self.targetColumn.addItems(self.value.columns)
            fc = data['target_column']
            #self.dropColumn.setCurrentIndex(self.value.columns.find_index(fc))
            return True & res
        except Exception as e:
            dumpException(e)
        return res