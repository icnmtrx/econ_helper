from econ_helper.eh_conf import *
from econ_helper.nodes.base_node_inout import *
from pandas.api.types import is_numeric_dtype


@register_node('lag', NODE_TYPE_PREPROCESSING)
class Node_Lag(BaseInOutNode):
    op_code = 'lag'
    type_code = NODE_TYPE_PREPROCESSING
    op_title = 'Lag'
    content_label_objname = 'node_lag'

    operation_name = 'lag'

    def __init__(self, scene, default_node_text='Lag on'):
        self.lag_column = None
        self.lag_size = None

        #GUI
        self.labelColumn = QLabel('Lag on column')

        self.targetColumn = QComboBox()

        self.lagControl = QSpinBox()
        self.lagControl.setValue(1)
        self.lagControl.setMaximum(99)
        self.lagControl.setMinimum(1)

        self.addOrReplaceButton = QPushButton('Replace with new value')
        self.addOrReplaceButton.setCheckable(True)

        self.onoff_signals(activate=True)

        super().__init__(scene, default_node_text)

        # if hasattr(self, 'value') and self.output_value is not None:
        #     self.targetColumn.addItems(self.output_value.columns)

    def onoff_signals(self, activate=True):
        if activate:
           self.targetColumn.currentIndexChanged.connect(self.targetColumnChanged)
           self.lagControl.valueChanged.connect(self.targetColumnChanged)
           self.addOrReplaceButton.toggled.connect(self.targetColumnChanged)
        else:
           self.targetColumn.currentIndexChanged.disconnect(self.targetColumnChanged)
           self.lagControl.valueChanged.disconnect(self.targetColumnChanged)
           self.addOrReplaceButton.toggled.disconnect(self.targetColumnChanged)

    def main_node_operation(self, df):
        column = self.targetColumn.currentText()
        lag_size = self.lagControl.value()
        replace = self.addOrReplaceButton.isChecked()

        if column == '' or column not in df.columns:
            column = self.lag_column
            lag_size = self.lag_size

        self.lag_column = column if (column != '' and column in df.columns) else None

        if column == '' or column not in df.columns:
            return None

        new_column = column + ' ' + self.operation_name + f' {lag_size}'
        new_value = df[column].shift(lag_size).fillna(0)
        dfc = df.copy()
        dfc.insert(0, new_column, new_value)
        if replace:
            dfc = dfc.drop(columns=[column])
        self.lag_column = column
        self.lag_size = lag_size

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
        if self.lag_column is not None:
            idx = self.targetColumn.findText(self.lag_column, Qt.MatchExactly)
            if idx >= 0:
                self.targetColumn.setCurrentIndex(idx)
                self.lag_column = self.targetColumn.currentText()
        else:
            #self.targetColumn.clear()
            self.markInvalid(error_message='Select lag column')

        if self.lag_size is not None:
            self.lagControl.setValue(self.lag_size)

        if not self.isInvalid():
            new_text = self.content.default_node_text + ' ' + self.targetColumn.currentText()
            self.content.edit.setText(new_text)

        self.onoff_signals(activate=True)

    def targetColumnChanged(self):
        self.markInvalid()
        self.eval()
        #self.node_settings_widget = self.create_settings_widget()
        self.update_ui()


    def create_settings_widget(self):
        w = QWidget()
        lo = QVBoxLayout(w)

        lo.addWidget(self.labelColumn)
        lo.addWidget(self.targetColumn)
        lo.addWidget(self.lagControl)
        lo.addWidget(self.addOrReplaceButton)


        vertSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        lo.addItem(vertSpacer)

        w.setLayout(lo)

        return w

    def serialize(self):
        res = super().serialize()

        res['lag_column'] = self.targetColumn.currentText()
        res['lag_size'] = self.lagControl.value()

        return res

    def deserialize(self, data, hashmap={}, restore_id=True, **kwargs):
        res = super().deserialize(data, hashmap)
        try:
            self.lag_column = data['lag_column']
            self.lag_size = data['lag_size']

            return True & res
        except Exception as e:
            dumpException(e)
        return res