
class Font(object):
    BOLD = 1
    ITALIC = 2

    def __init__(self, default, face, size):
        self.default = default
        self.face = face
        self.size = size
        self.faces = ['Times','Georgia','Helvetica']
        self.style = []
        
