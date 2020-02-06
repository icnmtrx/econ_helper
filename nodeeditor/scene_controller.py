import logging


class SceneController:

    def __init__(self, scene):
        self.scene = scene

    def scene_changed(self):
        nodes = self.scene.nodes
        for n in nodes:
            clname = n.__class__.__name__
            if not n.isDirty():
                logging.debug(f'unchanged {clname} ')
                #continue
            logging.debug(f'changed {clname}')
            n.eval()






