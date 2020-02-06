from econ_helper.eh_conf import *
from econ_helper.nodes.base_node_inout import *
import statsmodels.tsa as tsa
from pandas.api.types import is_numeric_dtype


@register_node('adstock', NODE_TYPE_PREPROCESSING)
class Node_Adstock(BaseInOutNode):
    op_code = 'adstock'
    type_code = NODE_TYPE_PREPROCESSING
    op_title = 'Adstock'
    content_label_objname = 'node_adstock'

    operation_name = 'adstock'

    def __init__(self, scene, default_node_text='Adstock on'):
        self.adstock_column = None
        self.adstock_size = None

        #GUI
        self.labelColumn = QLabel('Adstock (in %)')

        self.targetColumn = QComboBox()
        self.labelAdvice = QLabel('Recommended range: 0-100')

        self.adstockControl = QSpinBox()
        self.adstockControl.setValue(30)
        self.adstockControl.setMaximum(100)
        self.adstockControl.setMinimum(0)
        self.adstockControl.setMaximumWidth(self.targetColumn.maximumWidth())


        self.addOrReplaceButton = QPushButton('Replace with new value')
        self.addOrReplaceButton.setCheckable(True)

        self.onoff_signals(activate=True)

        super().__init__(scene, default_node_text)

    def onoff_signals(self, activate=True):
        if activate:
            self.targetColumn.currentIndexChanged.connect(self.targetColumnChanged)
            self.adstockControl.valueChanged.connect(self.targetColumnChanged)
            self.addOrReplaceButton.toggled.connect(self.targetColumnChanged)
        else:
            self.targetColumn.currentIndexChanged.disconnect(self.targetColumnChanged)
            self.adstockControl.valueChanged.disconnect(self.targetColumnChanged)
            self.addOrReplaceButton.toggled.disconnect(self.targetColumnChanged)

    def main_node_operation(self, df):
        dfc = None
        column = self.targetColumn.currentText()
        adstock_size = self.adstockControl.value()
        replace = self.addOrReplaceButton.isChecked()

        if column == '' or column not in df.columns:
            column = self.adstock_column
            adstock_size = self.adstock_size

        self.adstock_column = column if (column != '' and column in df.columns) else None

        if column == '' or column not in df.columns:
            return None

        new_column = column + ' ' + self.operation_name + f' {adstock_size}'
        new_value = tsa.filters.filtertools.recursive_filter(df[column], adstock_size/100)
        dfc = df.copy()
        dfc.insert(0, new_column, new_value)
        if replace:
            dfc = dfc.drop(columns=[column])
        self.adstock_column = column
        self.adstock_size = adstock_size

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
        if self.adstock_column is not None:
            idx = self.targetColumn.findText(self.adstock_column, Qt.MatchExactly)
            if idx >= 0:
                self.targetColumn.setCurrentIndex(idx)
                self.adstock_column = self.targetColumn.currentText()
        else:
            self.markInvalid(error_message='Select adstock column')

        if self.adstock_size is not None:
            self.adstockControl.setValue(self.adstock_size)

        if not self.isInvalid():
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
        lo.addWidget(self.labelAdvice)
        lo.addWidget(self.adstockControl)
        lo.addWidget(self.addOrReplaceButton)

        vertSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        lo.addItem(vertSpacer)

        w.setLayout(lo)

        return w


    def serialize(self):
        res = super().serialize()

        res['adstock_column'] = self.targetColumn.currentText()
        res['adstock_size'] = self.adstockControl.value()

        return res

    def deserialize(self, data, hashmap={}, restore_id=True, **kwargs):
        res = super().deserialize(data, hashmap)
        try:
            self.adstock_column = data['adstock_column']
            self.adstock_size = data['adstock_size']
            return True & res
        except Exception as e:
            dumpException(e)
        return res