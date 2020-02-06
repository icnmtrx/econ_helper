from econ_helper.eh_conf import *
from econ_helper.nodes.base_node_inout import *


@register_node('filter', NODE_TYPE_PREPROCESSING)
class Node_Filter(BaseInOutNode):
    op_code = 'filter'
    type_code = NODE_TYPE_PREPROCESSING
    op_title = 'Filter'
    content_label_objname = 'node_filter'

    def __init__(self, scene, default_node_text='Filter'):
        self.filter_column = None

        self.labelColumn = QLabel('Column to delete')
        self.dropColumn = QComboBox()

        self.onoff_signals(activate=True)

        super().__init__(scene, default_node_text)

    def onoff_signals(self, activate=True):
        if activate:
            self.dropColumn.currentIndexChanged.connect(self.dropFilterChanged)
        else:
            self.dropColumn.currentIndexChanged.disconnect(self.dropFilterChanged)

    def update_ui(self):
        self.onoff_signals(activate=False)

        self.dropColumn.clear()
        if self.input_value is not None:
            self.dropColumn.addItems(self.input_value.columns)
        else:
            self.markInvalid(error_message='Input is not connected')

        self.dropColumn.setCurrentIndex(-1)

        if self.filter_column is not None:
            idx = self.dropColumn.findText(self.filter_column, Qt.MatchExactly)
            if idx >= 0:
                self.dropColumn.setCurrentIndex(idx)
            else:
                self.markInvalid(error_message='Select filter column')

        if not self.isInvalid():
            new_text = self.content.default_node_text + ' ' + self.dropColumn.currentText()
            self.content.edit.setText(new_text)

        self.onoff_signals(activate=True)

    def main_node_operation(self, df):
        dfc = None

        columnToDrop = self.dropColumn.currentText()
        if columnToDrop is None \
                or columnToDrop == '' \
                or columnToDrop not in df.columns:
            columnToDrop = self.filter_column
        if columnToDrop is None \
                or columnToDrop == '' \
                or columnToDrop not in df.columns:
            return None

        if columnToDrop in self.input_value.columns:
            self.filter_column = columnToDrop
            dfc = df.drop(columns=columnToDrop)

        self.filter_column = columnToDrop

        return dfc

    def onMarkedDirty(self):
        super().onMarkedDirty()
        self.eval()
        #self.node_settings_widget = self.create_settings_widget()
        self.update_ui()

    def dropFilterChanged(self):
        self.markInvalid()
        self.eval()
        #self.node_settings_widget = self.create_settings_widget()
        self.update_ui()

    def create_settings_widget(self):
        w = QWidget()
        lo = QVBoxLayout(w)

        lo.addWidget(self.labelColumn)
        lo.addWidget(self.dropColumn)

        vertSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        lo.addItem(vertSpacer)

        w.setLayout(lo)

        return w


    def serialize(self):
        res = super().serialize()

        res['filter_column'] = self.dropColumn.currentText()

        return res

    def deserialize(self, data, hashmap={}, restore_id=True,  **kwargs):
        res = super().deserialize(data, hashmap)
        try:
            self.filter_column = data['filter_column']
            #self.markDirty()

            return True & res
        except Exception as e:
            dumpException(e)
        return res