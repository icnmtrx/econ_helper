from nodeeditor.node_content_widget import QDMNodeContentWidget
from nodeeditor.node_graphics_node import QDMGraphicsNode
from nodeeditor.node_socket import *
from nodeeditor.utils import dumpException

DEBUG = True

SOCKET_TYPE_DF = 1
SOCKET_TYPE_MODEL = 2


class Node(Serializable):

    def __init__(self, scene, title="Undefined Node", inputs=[], outputs=[]):
        super().__init__()
        self._title = title
        self.scene = scene

        self.initInnerClasses()
        self.initSettings()

        self.title = title

        self.scene.addNode(self)
        self.scene.grScene.addItem(self.grNode)

        # create socket for inputs and outputs
        self.inputs = []
        self.outputs = []
        self.initSockets(inputs, outputs)

        # dirty and evaluation
        self._is_dirty = False
        self._is_invalid = False

        self.error_message = None

        #print("Initializing node '%s'" % self.__class__.__name__)


    def initInnerClasses(self):
        self.content = QDMNodeContentWidget(self)
        self.grNode = QDMGraphicsNode(self)

    def initSettings(self):
        self.socket_spacing = 22

        self.input_socket_position = LEFT_BOTTOM
        self.output_socket_position = RIGHT_TOP
        self.input_multi_edged = False
        self.output_multi_edged = True

    def initSockets(self, inputs, outputs, reset=True):
        """ Create sockets for inputs and outputs"""
        #logging.debug(f'Node {self.__class__.__name__} init with {len(inputs)} inputs and {len(outputs)} outputs')

        if reset:
            # clear old sockets
            if hasattr(self, 'inputs') and hasattr(self, 'outputs'):
                # remove grSockets from scene
                for socket in (self.inputs+self.outputs):
                    self.scene.grScene.removeItem(socket.grSocket)
                self.inputs = []
                self.outputs = []

        # create new sockets
        counter = 0
        for item in inputs:
            socket = Socket(node=self, index=counter, position=self.input_socket_position,
                            socket_type=item, multi_edges=self.input_multi_edged,
                            count_on_this_node_side=len(inputs), is_input=True
            )
            counter += 1
            self.inputs.append(socket)

        counter = 0
        for item in outputs:
            socket = Socket(node=self, index=counter, position=self.output_socket_position,
                            socket_type=item, multi_edges=self.output_multi_edged,
                            count_on_this_node_side=len(outputs), is_input=False
            )
            counter += 1
            self.outputs.append(socket)

        #logging.debug(f'Node {self.__class__.__name__} has {len(self.inputs)} inputs and {len(self.outputs)} outputs')


    def onEdgeConnectionChanged(self, new_edge):
        pass
#        print("%s::onEdgeConnectionChanged" % self.__class__.__name__, new_edge)

    def onInputChanged(self, new_edge):
        #print("%s::onInputChanged" % self.__class__.__name__, new_edge)
        self.markDirty()
        self.markDescendantsDirty()

    def __str__(self):
        return "<Node %s..%s>" % (hex(id(self))[2:5], hex(id(self))[-3:])

    @property
    def pos(self):
        return self.grNode.pos()        # QPointF

    def setPos(self, x, y):
        self.grNode.setPos(x, y)

    @property
    def title(self): return self._title

    @title.setter
    def title(self, value):
        self._title = value
        self.grNode.title = self._title

    def getSocketPosition(self, index, position, num_out_of=1):
        x = 0 if (position in (LEFT_TOP, LEFT_CENTER, LEFT_BOTTOM)) else self.grNode.width

        if position in (LEFT_BOTTOM, RIGHT_BOTTOM):
            # start from bottom
            y = self.grNode.height - self.grNode.edge_roundness - self.grNode.title_vertical_padding - index * self.socket_spacing
        elif position in (LEFT_CENTER, RIGHT_CENTER):
            num_sockets = num_out_of
            node_height = self.grNode.height
            top_offset = self.grNode.title_height + 2 * self.grNode.title_vertical_padding + self.grNode.edge_padding
            available_height = node_height - top_offset

            total_height_of_all_sockets = num_sockets * self.socket_spacing
            new_top = available_height - total_height_of_all_sockets

            # y = top_offset + index * self.socket_spacing + new_top / 2
            y = top_offset + available_height/2.0 + (index-0.5)*self.socket_spacing
            if num_sockets > 1:
                y -= self.socket_spacing * (num_sockets-1)/2

        elif position in (LEFT_TOP, RIGHT_TOP):
            # start from top
            y = self.grNode.title_height + self.grNode.title_vertical_padding + self.grNode.edge_roundness + index * self.socket_spacing
        else:
            # this should never happen
            y = 0

        return [x, y]


    def updateConnectedEdges(self):
        logging.debug(f'Node {self.__class__.__name__} has {len(self.inputs)} inputs and {len(self.outputs)} outputs')
        for socket in self.inputs + self.outputs:
            # if socket.hasEdge():
            for edge in socket.edges:
                edge.updatePositions()


    def remove(self):
        # if DEBUG: print("> Removing Node", self)
        # if DEBUG: print(" - remove all edges from sockets")
        for socket in (self.inputs+self.outputs):
            # if socket.hasEdge():
            for edge in socket.edges:
                # if DEBUG: print("    - removing from socket:", socket, "edge:", edge)
                edge.remove()
        # if DEBUG: print(" - remove grNode")
        self.scene.grScene.removeItem(self.grNode)
        self.grNode = None
        # if DEBUG: print(" - remove node from the scene")
        self.scene.removeNode(self)
        # if DEBUG: print(" - everything was done.")


    # node evaluation stuff

    def isDirty(self):
        return self._is_dirty

    def markDirty(self, new_value=True):
        # if new_value == True:
        #     logging.debug("Node '%s' was marked dirty" % self.__class__.__name__)
        # else:
        #     logging.debug("Node '%s' was marked clear" % self.__class__.__name__)

        self._is_dirty = new_value
        if self._is_dirty:
            self.onMarkedDirty()
        else:
            self.onUnmarkedDirty()

    def onUnmarkedDirty(self):
        pass

    def onMarkedDirty(self):
        #logging.debug("Node '%s' onMarkedDirty" % self.__class__.__name__)
        #self.changed.emit(self)
        self.scene.has_been_modified = True
        pass

    def markChildrenDirty(self, new_value=True):
        for other_node in self.getChildrenNodes():
            # logging.debug(f"Node {self.__class__.__name__} marked dirty its child "
            #               f"{other_node.__class__.__name__}, v={new_value}")

            other_node.markDirty(new_value)

    def markDescendantsDirty(self, new_value=True):
        for other_node in self.getChildrenNodes():
            # logging.debug(f"Node {self.__class__.__name__} marked dirty its descendant "
            #               f"{other_node.__class__.__name__}, v={new_value}")
            other_node.markDirty(new_value)
            # logging.debug(f"Node {self.__class__.__name__} marked dirty its descendant child "
            #               f"{other_node.__class__.__name__}, v={new_value}")
            other_node.markChildrenDirty(new_value)

    def isInvalid(self):
        return self._is_invalid

    def markInvalid(self, new_value=True, error_message='Something went wrong'):
        self._is_invalid = new_value
        if self._is_invalid:
            self.onMarkedInvalid()
            self.error_message = error_message
        else:
            self.onUnmarkedInvalid()
            self.error_message = None

    def onMarkedInvalid(self):
        pass

    def onUnmarkedInvalid(self):
        pass

    def markChildrenInvalid(self, new_value=True):
        for other_node in self.getChildrenNodes():
            other_node.markInvalid(new_value)

    def markDescendantsInvalid(self, new_value=True):
        for other_node in self.getChildrenNodes():
            other_node.markInvalid(new_value)
            other_node.markChildrenInvalid(new_value)

    def eval(self):
        self.markDirty(False)
        self.markInvalid(False)
        return 0

    def evalChildren(self):
        for node in self.getChildrenNodes():
            node.eval()


    # traversing nodes functions

    def getChildrenNodes(self):
        if self.outputs == []: return []
        other_nodes = []
        #logging.debug(f"--- Node {self.__class__.__name__} has children:")
        for ix in range(len(self.outputs)):
            for edge in self.outputs[ix].edges:
                other_node = edge.getOtherSocket(self.outputs[ix]).node
                other_nodes.append(other_node)
                #logging.debug(f"---     {self.__class__.__name__} -> {other_node.__class__.__name__}")

        #logging.debug(f'--- total {len(other_nodes)} children')
        return other_nodes

    def getInputSocket(self, index=0):
        try:
            edge = self.inputs[index].edges[0]
            socket = edge.getOtherSocket(self.inputs[index])
            return socket
        except IndexError:
            logging.error(f"EXC: Trying to get input, but none is attached to {self}")
            return None
        except Exception as e:
            dumpException(e)
            return None

    def getInput(self, index=0):
        try:
            edge = self.inputs[index].edges[0]
            socket = edge.getOtherSocket(self.inputs[index])
            return socket.node
        except IndexError:
            logging.error(f"EXC: Trying to get input, but none is attached to {self}")
            return None
        except Exception as e:
            dumpException(e)
            return None


    def getInputs(self, index=0):
        ins = []
        for edge in self.inputs[index].edges:
            other_socket = edge.getOtherSocket(self.inputs[index])
            ins.append(other_socket.node)
        return ins

    def getOutputs(self, index=0):
        outs = []
        for edge in self.outputs[index].edges:
            other_socket = edge.getOtherSocket(self.outputs[index])
            outs.append(other_socket.node)
        return outs


    # serialization functions

    def serialize(self):
        #logging.debug(f'Node {self.__class__.__name__} has {len(self.inputs)} inputs and {len(self.outputs)} outputs')

        inputs, outputs = [], []
        for socket in self.inputs:
            inputs.append(socket.serialize())
        for socket in self.outputs:
            outputs.append(socket.serialize())
        return OrderedDict([
            ('id', self.id),
            ('title', self.title),
            ('pos_x', self.grNode.scenePos().x()),
            ('pos_y', self.grNode.scenePos().y()),
            ('inputs', inputs),
            ('outputs', outputs),
            ('content', self.content.serialize()),
        ])

    def deserialize(self, data, hashmap={}, restore_id=True):
        try:
            if restore_id: self.id = data['id']
            hashmap[data['id']] = self

            self.setPos(data['pos_x'], data['pos_y'])
            self.title = data['title']

            data['inputs'].sort(key=lambda socket: socket['index'] + socket['position'] * 10000 )
            data['outputs'].sort(key=lambda socket: socket['index'] + socket['position'] * 10000 )
            num_inputs = len( data['inputs'] )
            num_outputs = len( data['outputs'] )

            self.inputs = []
            for socket_data in data['inputs']:
                new_socket = Socket(node=self, index=socket_data['index'], position=socket_data['position'],
                                    socket_type=socket_data['socket_type'], count_on_this_node_side=num_inputs,
                                    is_input=True)
                new_socket.deserialize(socket_data, hashmap, restore_id)
                self.inputs.append(new_socket)

            self.outputs = []
            for socket_data in data['outputs']:
                new_socket = Socket(node=self, index=socket_data['index'], position=socket_data['position'],
                                    socket_type=socket_data['socket_type'], count_on_this_node_side=num_outputs,
                                    is_input=False)
                new_socket.deserialize(socket_data, hashmap, restore_id)
                self.outputs.append(new_socket)
        except Exception as e: dumpException(e)

        # also deseralize the content of the node
        res = self.content.deserialize(data['content'], hashmap)

        #logging.debug(f'Node {self.__class__.__name__} has {len(self.inputs)} inputs and {len(self.outputs)} outputs')

        return True & res