from p5.core.color import Color

class Pixels(list):
    def __init__(self, l):
        super().__init__([Color(*v) for v in l])
    
    def tolist(self):
        return [tuple(int(v*255) for v in value.rgba) for value in self]