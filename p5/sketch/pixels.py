from p5.core.color import Color, color_mode
import p5.core.p5 as _p5

class Pixels(list):
    def __init__(self, l):
        old_color_mode = _p5.renderer.style.color_parse_mode
        old_color_range = _p5.renderer.style.color_range
        color_mode("RGBA", 255)
        super().__init__([Color(*v, color_mode="RGBA") for v in l])
        color_mode(old_color_mode, *old_color_range)
    
    def tolist(self):
        return [tuple(int(v*255) for v in value.rgba) for value in self]