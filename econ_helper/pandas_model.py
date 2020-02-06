from PyQt5 import QtCore
import numbers

import pandas as pd
from PyQt5.QtGui import *


class PandasModel(QtCore.QAbstractTableModel):

    def __init__(self, data=None):
        QtCore.QAbstractTableModel.__init__(self)
        self._data = data
        self.paint_callback = None

    def set_paint_callback(self, callback):
        self.paint_callback = callback

    def set_data(self, data=None):
        self._data = data


    def default_paint_callback(self, row, column):
        if self._data is None:
            return
        value = self._data.iloc[row, column]

        color = QColor('darkGray')

        if not isinstance(value, numbers.Number):
            brush = QBrush(color)
            return brush

        return


    def rowCount(self, parent=None, **kwargs):
        if self._data is not None:
            return self._data.shape[0]
        else:
            return 0

    def columnCount(self, parent=None, **kwargs):
        if self._data is not None:
            return self._data.shape[1]
        else:
            return 0

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                item = self._data.iloc[index.row(), index.column()]
                if isinstance(item, numbers.Number):
                    return f'{item:.4f}'

                return str(item)
            if role == QtCore.Qt.BackgroundRole:
                if self.paint_callback is not None:
                    return self.paint_callback(index.row(), index.column())
        return None

    def headerData(self, col, orientation, role=None):
        if self._data is None:
            return None

        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self._data.columns[col]

        return None


