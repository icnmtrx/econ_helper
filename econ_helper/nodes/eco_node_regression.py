import numpy as np
import pandas as pd
import pyqtgraph as pg

from econ_helper.eh_conf import *
from econ_helper.eh_node_base import *
from econ_helper.nodes.base_node_inout import BaseNodeContent
from nodeeditor.node_content_widget import ImprovedPlainTextEdit
from nodeeditor.node_node import SOCKET_TYPE_DF, SOCKET_TYPE_MODEL
from nodeeditor.utils import dumpException

from sklearn.tree import DecisionTreeRegressor


@register_node('regression', NODE_TYPE_ECO)
class Node_Regression(EcoNode):
    op_code = 'regression'
    type_code = NODE_TYPE_ECO
    op_title = 'Regression'
    content_label_objname = 'node_regression'

    def __init__(self, scene, default_node_text='Regression'):
        self.default_node_text = default_node_text
        self.input_value = None

        self.target_column = None
        self.factors = []

        self.labelTarget = QLabel('Target column')
        self.targetColumn = QComboBox()

        self.labelFactors = QLabel('Regressors')
        self.factorList = QListWidget()

        self.outputArea = ImprovedPlainTextEdit()
        self.plotArea = pg.PlotWidget()
        self.plotArea.getPlotItem().setMenuEnabled(False)

        self.onoff_signals(activate=True)

        super().__init__(scene, inputs=[SOCKET_TYPE_DF], outputs=[])

    def initInnerClasses(self):
        self.content = BaseNodeContent(self)
        self.grNode = EcoGraphicsNode(self)
        if self.default_node_text is not None:
            self.content.default_node_text = self.default_node_text

    def onoff_signals(self, activate=True):
        if activate:
            self.factorList.itemChanged.connect(self.settingsChanged)
            self.targetColumn.currentIndexChanged.connect(self.settingsChanged)
        else:
            self.factorList.itemChanged.disconnect(self.settingsChanged)
            self.targetColumn.currentIndexChanged.disconnect(self.settingsChanged)

    def update_ui(self):
        self.onoff_signals(activate=False)

        self.targetColumn.clear()
        if self.input_value is not None:
            self.targetColumn.addItems(self.input_value.columns)
        else:
            self.markInvalid(error_message='Input is not connected')

        self.targetColumn.setCurrentIndex(-1)
        if self.target_column is not None:
            idx = self.targetColumn.findText(self.target_column, Qt.MatchExactly)
            if idx >= 0:
                self.targetColumn.setCurrentIndex(idx)
                self.target_column = self.targetColumn.currentText()
            else:
                self.markInvalid()

        self.factorList.clear()
        column = self.targetColumn.currentText()
        if self.input_value is not None \
                and column is not None \
                and column in self.input_value.columns:
            input_wo_target = self.input_value.drop(columns=[column])
            self.factorList.addItems(input_wo_target)
            for i in range(self.factorList.count()):
                w = self.factorList.item(i)
                w.setFlags(w.flags() | Qt.ItemIsUserCheckable)
                w.setCheckState(Qt.Unchecked)
        else:
            self.markInvalid(error_message='Input is not valid')

        currently_checked = []

        if self.factors is not None:
            for i in range(self.factorList.count()):
                w = self.factorList.item(i)
                if w.text() in self.factors:
                    w.setCheckState(Qt.Checked)
                else:
                    w.setCheckState(Qt.Unchecked)

        for i in range(self.factorList.count()):
            w = self.factorList.item(i)
            if w.checkState() == Qt.Checked:
                currently_checked.append(w.text())

        if not self.isInvalid():
            new_text = self.content.default_node_text + ' ' + str(currently_checked)
            self.content.edit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.content.edit.setText(new_text)

        self.onoff_signals(activate=True)

    def model(self, X, y, constant=True, log_transform=False, verbose=True):
        model = DecisionTreeRegressor().fit(X, y)
        return model

    def main_node_operation(self, df):
        if df is None or not isinstance(df, pd.DataFrame):
            return None

        y_column = self.targetColumn.currentText()
        if y_column is None or y_column == '' \
                or y_column not in df.columns \
                or y_column not in self.input_value.columns:
            return None, None

        self.target_column = y_column

        currently_checked = []
        for i in range(self.factorList.count()):
            w = self.factorList.item(i)
            if w.checkState() == Qt.Checked:
                currently_checked.append(w.text())

        if len(currently_checked) == 0 or set(currently_checked).isdisjoint(self.input_value.columns):
            return None, None

        self.factors = currently_checked

        if self.target_column not in df.columns \
                or self.factors is None:
            return None, None

        # sanity check
        # here we additionally check if incoming dataframe has expected columns
        # while it can be changed by parent node, keeping factors unchanged yet
        sanity_factors = df.columns[df.columns.isin(self.factors)]

        y = df[self.target_column].copy()
        data = df[sanity_factors].copy()

        res_model = self.model(data, y)
        importances = res_model.feature_importances_
        indices = np.argsort(importances)[::-1]
        output_text = "Feature ranking:\n\n"
        for f in range(data.shape[1]):
            output_text += f"{f+1}. feature {indices[f]} [{data.columns[indices[f]]}] ({importances[indices[f]]})\n"

        self.outputArea.setText(f'{output_text}')

        pred = res_model.predict(data)

        self.plotArea.clear()
        self.plotArea.plot(y, name='expected', pen=pg.mkPen('g', width=3))
        self.plotArea.plot(pred, name='predicted', pen=pg.mkPen('y', width=3))

        self.update_ui()
        return res_model, data

    def onUnmarkedInvalid(self):
        super().onUnmarkedInvalid()
        self.update_ui()

    def onMarkedDirty(self):
        super().onMarkedDirty()
        self.eval()
        self.update_ui()

    def settingsChanged(self):
        self.markInvalid()
        self.eval()
        self.update_ui()

    def onMarkedInvalid(self):
        if self.input_value is None:
            logging.debug(f'input is none for {self.__class__.__name__}')
        if self.output_value is None:
            logging.debug(f'output is none for {self.__class__.__name__}')

    def markInvalid(self, new_value=True, error_message='Something went wrong'):
        super().markInvalid(new_value, error_message)
        if new_value:
            logging.debug(f'invalidate node {self.__class__.__name__} with message {error_message}')
            self.onMarkedInvalid()
        else:
            logging.debug(f'node {self.__class__.__name__} marked valid')
            self.onUnmarkedInvalid()

        if new_value and self.error_message is not None:
            self.content.edit.setText(error_message)

    def evalImplementation(self):
        self.input_value = None
        input_node = self.getInput(0)
        if input_node is None or not hasattr(input_node, 'output_value'):
            logging.debug(f'Input is not connected to node {self.__class__.__name__}')
            self.grNode.setToolTip("Input is not connected")
            self.markInvalid(error_message='Input is not connected')
            return None

        logging.debug(f'evaluating connection {input_node.__class__.__name__} -> {self.__class__.__name__}')

        self.input_value = input_node.get_output()
        if self.input_value is None:
            logging.debug(f'Input is not valid to node {self.__class__.__name__}')
            self.grNode.setToolTip("Input is not valid")
            self.markInvalid(error_message='Input is not valid')
            return None

        new_output_model, new_output_value = self.main_node_operation(self.input_value)
        need_update_children = False
        if new_output_model is not None \
                and new_output_value is not None \
                and isinstance(new_output_value, pd.DataFrame):
            need_update_children = True
            self.output_value = []

        if new_output_value is None:
            self.markInvalid(error_message='Check node configuration')
        else:
            # self.dataModel = PandasModel(self.output_value)
            # self.table.setModel(self.dataModel)
            # self.adjust_table_width()
            # self.table.show()
            #
            self.markDirty(False)
            self.markInvalid(False)

            self.markDescendantsInvalid(False)

            if need_update_children:
                logging.debug(f'Node {self.__class__.__name__} makes descendants dirty')
                # self.markDescendantsDirty()
                self.markChildrenDirty()

            self.grNode.setToolTip("")

        logging.debug(f'Main node operation done for node {self.__class__.__name__}')
        return self.output_value

    def create_settings_widget(self):
        w = QWidget()
        lo = QVBoxLayout(w)

        lo.addWidget(self.labelTarget)
        lo.addWidget(self.targetColumn)
        lo.addWidget(self.labelFactors)
        lo.addWidget(self.factorList)

        vertSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        lo.addItem(vertSpacer)

        w.setLayout(lo)

        return w

    def create_output_widget(self, title=None):
        w = QWidget()
        lo = QVBoxLayout(w)
        if title is None:
            lo.addWidget(QLabel(f'{self.title} output'))
        else:
            lo.addWidget(QLabel(title))

        plotPolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        plotPolicy.setVerticalStretch(1)
        self.plotArea.setSizePolicy(plotPolicy)
        lo.addWidget(self.plotArea)

        inputPolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        inputPolicy.setVerticalStretch(3)
        self.outputArea.setSizePolicy(inputPolicy)
        lo.addWidget(self.outputArea)

        w.setLayout(lo)
        return w

    def serialize(self):
        res = super().serialize()

        res['target_column'] = self.target_column
        res['factors'] = self.factors

        return res

    def deserialize(self, data, hashmap={}, restore_id=True, **kwargs):
        res = super().deserialize(data, hashmap)
        try:
            self.target_column = data['target_column']
            self.factors = data['factors']

            return True & res
        except Exception as e:
            dumpException(e)
        return res
