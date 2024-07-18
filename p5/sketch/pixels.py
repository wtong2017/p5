from p5.core.color import Color, color_mode
from p5.core.constants import RGB
import p5.core.p5 as _p5

class Pixels(list):
    def __init__(self, l):
        """
        Create a Pixels object from a list of tuples.

        Args:
            l (list): List of tuples
        """
        # Save the current color mode and range
        old_color_mode = _p5.renderer.style.color_parse_mode
        old_color_range = _p5.renderer.style.color_range

        # Set color mode to RGB 255
        color_mode(RGB, 255)
        super().__init__([Color(*v, color_mode="RGBA") for v in l])

        # Reset color mode
        color_mode(old_color_mode, *old_color_range)
    
    def tolist(self):
        """
        Convert the Pixels object to a list of tuples.

        Returns:
            list: List of tuples
        """
        return [tuple(int(v/_p5.renderer.style.color_range[i]*255) for i, v in enumerate(value.rgba)) for value in self]