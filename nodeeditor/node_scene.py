import logging
import os
import json
import traceback
from collections import OrderedDict

from nodeeditor.scene_controller import SceneController
from nodeeditor.utils import dumpException
from nodeeditor.node_serializable import Serializable
from nodeeditor.node_graphics_scene import QDMGraphicsScene
from nodeeditor.node_node import Node
from nodeeditor.node_edge import Edge
from nodeeditor.node_scene_history import SceneHistory
from nodeeditor.node_scene_clipboard import SceneClipboard


class InvalidFile(Exception): pass


class Scene(Serializable):
    def __init__(self):
        super().__init__()
        self.nodes = []
        self.edges = []

        self.scene_width = 1024
        self.scene_height = 1024

        self._has_been_modified = False
        self._last_selected_items = []

        # initialiaze all listeners
        self._has_been_modified_listeners = []
        self._item_selected_listeners = []
        self._items_deselected_listeners = []
        self._items_released_listeners = []

        # here we can store callback for retrieving the class for Nodes
        self.node_class_selector = None

        self.initUI()
        self.history = SceneHistory(self)
        self.clipboard = SceneClipboard(self)

        self.grScene.itemSelected.connect(self.onItemSelected)
        self.grScene.itemsDeselected.connect(self.onItemsDeselected)
        self.grScene.itemMouseRelease.connect(self.onMouseRelease)

        self.controller = SceneController(self)

        self.addHasBeenModifiedListener(self.controller.scene_changed)


    def initUI(self):
        self.grScene = QDMGraphicsScene(self)
        self.grScene.setGrScene(self.scene_width, self.scene_height)

    def onItemSelected(self):
        current_selected_items = self.getSelectedItems()
        logging.debug(f'{self.__class__.__name__} selected {current_selected_items}')
        if current_selected_items != self._last_selected_items:
            self._last_selected_items = current_selected_items
            self.history.storeHistory("Selection Changed")
            for callback in self._item_selected_listeners: callback()

    def onMouseRelease(self):
        current_selected_items = self.getSelectedItems()
        logging.debug(f'selected {current_selected_items}')
        for callback in self._items_released_listeners: callback()

    def onItemsDeselected(self):
        self.resetLastSelectedStates()
        if self._last_selected_items != []:
            self._last_selected_items = []
            self.history.storeHistory("Deselected Everything")
            for callback in self._items_deselected_listeners: callback()

    def isModified(self):
        return self.has_been_modified

    def getSelectedItems(self):
        return self.grScene.selectedItems()

    @property
    def has_been_modified(self):
        return self._has_been_modified

    @has_been_modified.setter
    def has_been_modified(self, value):
        if not self._has_been_modified and value:
            # set it now, because we will be reading it soon
            self._has_been_modified = value

            # call all registered listeners
            for callback in self._has_been_modified_listeners: callback()

        self._has_been_modified = value
        self.controller.scene_changed()

    # our helper listener functions
    def addHasBeenModifiedListener(self, callback):
        self._has_been_modified_listeners.append(callback)

    def addItemSelectedListener(self, callback):
        self._item_selected_listeners.append(callback)

    def addItemsDeselectedListener(self, callback):
        self._items_deselected_listeners.append(callback)

    def addItemsMouseReleasedListeners(self, callback):
        self._items_released_listeners.append(callback)

    def addDragEnterListener(self, callback):
        self.getView().addDragEnterListener(callback)

    def addDropListener(self, callback):
        self.getView().addDropListener(callback)

    # custom flag to detect node or edge has been selected....
    def resetLastSelectedStates(self):
        for node in self.nodes:
            node.grNode._last_selected_state = False
        for edge in self.edges:
            edge.grEdge._last_selected_state = False

    def getView(self):
        return self.grScene.views()[0]

    def getItemAt(self, pos):
        return self.getView().itemAt(pos)

    def addNode(self, node):
        self.nodes.append(node)

    def addEdge(self, edge):
        self.edges.append(edge)


    def removeNode(self, node):
        if node in self.nodes:
            self.nodes.remove(node)
        else:
            logging.debug(f"Scene::removeNode wanna remove node {node} from self.nodes but it's not in the list!")

    def removeEdge(self, edge):
        if edge in self.edges:
            self.edges.remove(edge)
        else:
            logging.debug(f"Scene::removeEdge wanna remove edge {edge} from self.edges but it's not in the list!")


    def clear(self):
        while len(self.nodes) > 0:
            self.nodes[0].remove()

        self.has_been_modified = False


    def saveToFile(self, filename):
        with open(filename, "w") as file:
            file.write( json.dumps( self.serialize(), indent=4 ) )
            logging.debug(f"saving to {filename} was successful.")

            self.has_been_modified = False

    def loadFromFile(self, filename):
        with open(filename, "r") as file:
            raw_data = file.read()
            try:
                data = json.loads(raw_data, encoding='utf-8')
                self.deserialize(data)
                self.has_been_modified = False
            except json.JSONDecodeError:
                raise InvalidFile("%s is not a valid JSON file" % os.path.basename(filename))
            except Exception as e:
                dumpException(e)

    def setNodeClassSelector(self, class_selecting_function):
        """ When the function self.node_class_selector is set, we can use different Node Classes """
        self.node_class_selector = class_selecting_function

    def getNodeClassFromData(self, data):
        if self.node_class_selector is None:
            return Node
        else:
            return self.node_class_selector(data)


    def serialize(self):
        nodes, edges = [], []
        for node in self.nodes: nodes.append(node.serialize())
        for edge in self.edges: edges.append(edge.serialize())
        return OrderedDict([
            ('id', self.id),
            ('scene_width', self.scene_width),
            ('scene_height', self.scene_height),
            ('nodes', nodes),
            ('edges', edges),
        ])

    def deserialize(self, data, hashmap={}, restore_id=True):
        self.clear()
        hashmap = {}

        if restore_id: self.id = data['id']

        # create nodes
        for node_data in data['nodes']:
            #classtype = self.getNodeClassFromData(node_data)
            #c = classtype(self)
            #c.deserialize(node_data, hashmap, restore_id)
            #self.addNode(c)

            try:
                self.getNodeClassFromData(node_data)(self).deserialize(node_data, hashmap, restore_id)
            except Exception as e:
                logging.error(e)
                traceback.print_tb(e.__traceback__)

        # create edges
        for edge_data in data['edges']:
            Edge(self).deserialize(edge_data, hashmap, restore_id)

        return True