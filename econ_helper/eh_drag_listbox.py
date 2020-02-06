from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from econ_helper.eh_conf import *
from nodeeditor.utils import dumpException


class QDMDragListbox(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.top_level_items = {}

        self.initUI()

    def initUI(self):
        # init
        self.setIconSize(QSize(32, 32))
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setDragEnabled(True)
        self.setColumnCount(1)
        self.setHeaderLabel('Available widgets')

        self.addMyItems()

    def addMyItems(self):
        type_codes = list(ECO_NODES.keys())
        type_codes.sort()
        for tc in type_codes:
            self.addMyTopLevelItem(tc)

            op_codes = list(ECO_NODES[tc].keys())
            op_codes.sort()
            for op_code in op_codes:
                node = get_class_from_opcode(op_code, tc)
                self.addMyItem(node.op_title, node.icon, tc, node.op_code)

    def addMyTopLevelItem(self, type_code=TYPE_CODE_COMMON):
        top_level_item = QTreeWidgetItem([type_code])
        self.top_level_items[type_code] = top_level_item
        self.addTopLevelItem(self.top_level_items[type_code])
        self.expandAll()

    def addMyItem(self, name, icon=None, type_code=TYPE_CODE_COMMON, op_code=0):
        # item = QListWidgetItem(name, self) # can be (icon, text, parent, <int>type)
        item = QTreeWidgetItem([name])
        pixmap = QPixmap(icon if icon is not None else ".")
        item.setIcon(0, QIcon(pixmap))
        item.setSizeHint(0, QSize(32, 32))

        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)

        # setup data
        item.setData(0, Qt.UserRole, pixmap)
        item.setData(0, Qt.UserRole + 1, op_code)

        self.top_level_items[type_code].addChild(item)

    def startDrag(self, *args, **kwargs):
        try:
            item = self.currentItem()
            op_code = item.data(0, Qt.UserRole + 1)
            parent_item = item.parent()
            if parent_item is not None:
                type_code = parent_item.text(0)
            else:
                type_code = 'None'

            pixmap = QPixmap(item.data(0, Qt.UserRole))

            itemData = QByteArray()
            dataStream = QDataStream(itemData, QIODevice.WriteOnly)
            dataStream << pixmap
            dataStream.writeQString(op_code)
            dataStream.writeQString(type_code)
            dataStream.writeQString(item.text(0))

            mimeData = QMimeData()
            mimeData.setData(LISTBOX_MIMETYPE, itemData)

            drag = QDrag(self)
            drag.setMimeData(mimeData)
            drag.setHotSpot(QPoint(pixmap.width() / 2, pixmap.height() / 2))
            drag.setPixmap(pixmap)

            drag.exec_(Qt.MoveAction)

        except Exception as e:
            dumpException(e)
