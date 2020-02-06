import traceback
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from pprint import pformat
import logging


def pp(message):
    logging.debug(pformat(message))

def dumpException(e):
    logging.error("%s EXCEPTION:" % e.__class__.__name__, e)
    traceback.print_tb(e.__traceback__)
    raise e


def loadStylesheet(filename):
    logging.debug(f'STYLE loading: {filename}')
    file = QFile(filename)
    file.open(QFile.ReadOnly | QFile.Text)
    stylesheet = file.readAll()
    QApplication.instance().setStyleSheet(str(stylesheet, encoding='utf-8'))

def loadStylesheets(*args):
    res = ''
    for arg in args:
        file = QFile(arg)
        file.open(QFile.ReadOnly | QFile.Text)
        stylesheet = file.readAll()
        res += "\n" + str(stylesheet, encoding='utf-8')
    QApplication.instance().setStyleSheet(res)
