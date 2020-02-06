from econ_helper.eh_conf import *
from econ_helper.nodes.base_node_inout import *

import statsmodels.tools.tools as sm_tools
import statsmodels.api as sm
from pandas.api.types import is_numeric_dtype


@register_node('trend', NODE_TYPE_PREPROCESSING)
class Node_Filter(BaseInOutNode):
    op_code = 'trend'
    type_code = NODE_TYPE_PREPROCESSING
    op_title = 'Trend'
    content_label_objname = 'node_trend'

    operation_name = 'trend'

    def __init__(self, scene, default_node_text='Trend on'):
        self.trend_column = None

        #GUI
        self.labelColumn = QLabel('Trend on column')

        self.targetColumn = QComboBox()

        self.addOrReplaceButton = QPushButton('Replace with new value')
        self.addOrReplaceButton.setCheckable(True)

        self.onoff_signals(activate=True)

        super().__init__(scene, default_node_text)


    def onoff_signals(self, activate=True):
        if activate:
            self.targetColumn.currentIndexChanged.connect(self.targetColumnChanged)
            self.addOrReplaceButton.toggled.connect(self.targetColumnChanged)
        else:
            self.targetColumn.currentIndexChanged.disconnect(self.targetColumnChanged)
            self.addOrReplaceButton.toggled.disconnect(self.targetColumnChanged)

    def main_node_operation(self, df):
        column = self.targetColumn.currentText()
        replace = self.addOrReplaceButton.isChecked()
        if column == '' or column not in df.columns:
            column = self.trend_column

        self.trend_column = column if (column != '' and column in df.columns) else None

        if column == '' or column not in df.columns:
            return None

        x = list(range(df[column].shape[0]))
        new_column = column + ' ' + self.operation_name
        x = sm_tools.add_constant(x)  # Add constant
        ols_model = sm.OLS(df[column], x)  # Initialize model
        ols_result = ols_model.fit()  # Fit model
        trend_data = ols_result.predict(x)

        dfc = df.copy()
        dfc.insert(0, new_column, trend_data)
        if replace:
            dfc = dfc.drop(columns=[column])

        self.trend_column = column

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
        if self.trend_column is not None:
            idx = self.targetColumn.findText(self.trend_column, Qt.MatchExactly)
            if idx >= 0:
                self.targetColumn.setCurrentIndex(idx)
                self.trend_column = self.targetColumn.currentText()
        else:
            self.markInvalid(error_message='Select column')

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
        lo.addWidget(self.addOrReplaceButton)

        vertSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        lo.addItem(vertSpacer)

        w.setLayout(lo)

        return w


    def serialize(self):
        res = super().serialize()

        res['trend_column'] = self.targetColumn.currentText()

        return res

    def deserialize(self, data, hashmap={}, restore_id=True, **kwargs):
        res = super().deserialize(data, hashmap)
        try:
            self.trend_column = data['trend_column']

            return True & res
        except Exception as e:
            dumpException(e)
        return res