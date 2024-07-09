from p5.core.color import Color

class Pixels(list):
    def __init__(self, l):
        super().__init__(l)
    
    def __setitem__(self, key, value):
        if isinstance(value, Color):
            super().__setitem__(key, tuple(int(v*255) for v in value.rgba))
        elif isinstance(value, (list, tuple)):
            super().__setitem__(key, value)