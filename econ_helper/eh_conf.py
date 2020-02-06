LISTBOX_MIMETYPE = "application/x-item"


TYPE_CODE_COMMON='Common'

NODE_TYPE_DATA_SOURCE = 'Data Source'
NODE_TYPE_DATA_DEST = 'Data Dest'
NODE_TYPE_PREPROCESSING = 'Preprocessing'
NODE_TYPE_ECO = 'Econometrics'

ECO_NODES = {
}


class ConfException(Exception): pass
class InvalidNodeRegistration(ConfException): pass
class OpCodeNotRegistered(ConfException): pass


def register_node_now(op_code, type_code, class_reference):
    if type_code not in ECO_NODES:
        ECO_NODES[type_code] = {}

    if op_code in ECO_NODES[type_code]:
        raise InvalidNodeRegistration("Duplicate node registration of '%s'. There is already %s" %(
            op_code, ECO_NODES[type_code][op_code]
        ))
    ECO_NODES[type_code][op_code] = class_reference


def register_node(op_code, type_code=TYPE_CODE_COMMON):
    def decorator(original_class):
        register_node_now(op_code, type_code, original_class)
        return original_class
    return decorator

def get_class_from_opcode(op_code, type_code=TYPE_CODE_COMMON):
    if op_code not in ECO_NODES[type_code]:
        raise OpCodeNotRegistered("OpCode '%d' is not registered for type" % (op_code, type_code))
    return ECO_NODES[type_code][op_code]



# import all nodes and register them
from econ_helper.nodes import *