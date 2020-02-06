import traceback

import pandas as pd
import pyqtgraph as pg

from econ_helper.eh_conf import *
from econ_helper.eh_node_base import *
from econ_helper.nodes.base_node_inout import BaseNodeContent
from nodeeditor.node_node import SOCKET_TYPE_DF
from nodeeditor.utils import dumpException
from pandas.api.types import is_numeric_dtype


@register_node('plotter', NODE_TYPE_ECO)
class Node_Plotter(EcoNode):
    op_code = 'plotter'
    type_code = NODE_TYPE_ECO
    op_title = 'Plotter'
    content_label_objname = 'node_plotter'

    def __init__(self, scene, default_node_text='Plotter'):
        self.default_node_text = default_node_text
        self.input_value = None

        self.labelColumns = QLabel('Data columns to plot')
        self.plot_columns = []
        self.plotList = QListWidget()

        self.plotArea = pg.PlotWidget() # pg.plot(title='Linear regression')
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
            self.plotList.itemChanged.connect(self.settingsChanged)
        else:
            self.plotList.itemChanged.disconnect(self.settingsChanged)

    def update_ui(self):
        self.onoff_signals(activate=False)

        self.plotList.clear()
        real_input = self.input_value
        if real_input is not None:
            self.plotList.addItems(real_input)
            for i in range(self.plotList.count()):
                w = self.plotList.item(i)
                item_text = w.text()
                if item_text in real_input and is_numeric_dtype(real_input[item_text]):
                    w.setFlags(w.flags() | Qt.ItemIsUserCheckable)
                    w.setCheckState(Qt.Unchecked)
                else:
                    w.setFlags(w.flags() ^ Qt.ItemIsUserCheckable)
                    w.setFlags(w.flags() ^ Qt.ItemIsEnabled)
        else:
            self.markInvalid(error_message='Input is not valid')

        currently_checked = []

        if self.plot_columns is not None:
            for i in range(self.plotList.count()):
                w = self.plotList.item(i)
                if w.text() in self.plot_columns:
                    w.setCheckState(Qt.Checked)
                else:
                    w.setCheckState(Qt.Unchecked)

        for i in range(self.plotList.count()):
            w = self.plotList.item(i)
            if w.checkState() == Qt.Checked:
                currently_checked.append(w.text())

        if not self.isInvalid():
            new_text = self.content.default_node_text + ' ' + str(currently_checked)
            self.content.edit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.content.edit.setText(new_text)

        self.onoff_signals(activate=True)

    def main_node_operation(self, df):
        if df is None or not isinstance(df, pd.DataFrame):
            return None

        real_input = self.input_value
        if real_input is None:
            return None

        currently_checked = []
        for i in range(self.plotList.count()):
            w = self.plotList.item(i)
            if w.checkState() == Qt.Checked:
                currently_checked.append(w.text())

        if len(currently_checked) == 0 or set(currently_checked).isdisjoint(real_input.columns):
            return None, None

        self.plot_columns = currently_checked

        # sanity check
        # here we additionally check if incoming dataframe has expected columns
        # while it can be changed by parent node, keeping plot_columns unchanged yet
        sanity_plot_columns = df.columns[df.columns.isin(self.plot_columns)]

        legend = self.plotArea.getPlotItem().legend
        if legend is not None:
            for item in legend.items:
                legend.removeItem(item)

        self.plotArea.getPlotItem().clearPlots()
        self.plotArea.getPlotItem().clear()
        self.plotArea.clear()
        self.plotArea.getPlotItem().scene().removeItem(self.plotArea.getPlotItem().legend)

        self.plotArea.plotItem.addLegend()

        data = df[sanity_plot_columns].copy()
        for ind, c in enumerate(data.columns):
            item = pg.PlotDataItem(data[c], name=c, pen=pg.mkPen(pg.intColor(index=ind)))
#            self.plotArea.plot(data[c], name=c, pen=pg.mkPen(pg.intColor(index=ind)))
            self.plotArea.addItem(item)

        self.update_ui()
        return data

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
        input_value, socket_type = self.get_guarded_input(0)
        if input_value is None or socket_type is not SOCKET_TYPE_DF \
                or not isinstance(input_value, pd.DataFrame):
            logging.debug(f'Input is not valid to node {self.__class__.__name__}')
            self.grNode.setToolTip("Input is not valid")
            self.markInvalid(error_message='Input is not valid')
            return None
        logging.debug(f'evaluating connection -> {self.__class__.__name__}')

        new_output_value = None

        try:
            self.input_value = input_value
            new_output_value = self.main_node_operation(self.input_value)
            self.output_value = new_output_value
        except Exception as e:
            logging.error(e)
            traceback.print_tb(e.__traceback__)
            self.output_value = None
            self.markInvalid(error_message='Internal node error. See log for details')

        if new_output_value is None:
            self.markInvalid(error_message='Check node configuration')
        else:
            self.markDirty(False)
            self.markInvalid(False)

            self.markDescendantsInvalid(False)
            self.grNode.setToolTip("")

        logging.debug(f'Main node operation done for node {self.__class__.__name__}')
        return self.output_value

    def create_settings_widget(self):
        w = QWidget()
        lo = QVBoxLayout(w)

        lo.addWidget(self.labelColumns)
        lo.addWidget(self.plotList)

        vertSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Minimum)
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

        lo.addWidget(self.plotArea)

        w.setLayout(lo)
        return w

    def serialize(self):
        res = super().serialize()

        currently_checked = []
        for i in range(self.plotList.count()):
            w = self.plotList.item(i)
            if w.checkState() == Qt.Checked:
                currently_checked.append(w.text())
        res['plot_columns'] = currently_checked

        return res

    def deserialize(self, data, hashmap={}, restore_id=True, **kwargs):
        res = super().deserialize(data, hashmap)
        try:
            self.plot_columns = data['plot_columns']

            return True & res
        except Exception as e:
            dumpException(e)
        return res
