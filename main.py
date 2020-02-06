import os
import sys
from PyQt5.QtWidgets import *
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from econ_helper.eh_window import EcoHelperWindow

logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s][%(module)s:%(funcName)s:%(lineno)d] %(message)s')
logger = logging.getLogger()

logger.setLevel(logging.DEBUG)


if __name__ == '__main__':
    logger.info('start')
    app = QApplication(sys.argv)

    # print(QStyleFactory.keys())
    app.setStyle('Fusion')

    wnd = EcoHelperWindow()
    wnd.show()

    sys.exit(app.exec_())
