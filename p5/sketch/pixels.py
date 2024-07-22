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
        super().__init__(l)
    
    def __setitem__(self, key, value):
        """
        Set the value of the Pixels object at the given index.

        Args:
            key (int): Index
            value (Color): Color
        """
        super().__setitem__(key, tuple(int(v/_p5.renderer.style.color_range[i]*255) for i, v in enumerate(value.rgba)))
    
    def __getitem__(self, key):
        """
        Get the value of the Pixels object at the given index.

        Args:
            key (int): Index

        Returns:
            Color: Color
        """
        # Save the current color mode and range
        old_color_mode = _p5.renderer.style.color_parse_mode
        old_color_range = _p5.renderer.style.color_range

        # Set color mode to RGB 255
        color_mode(RGB, 255)
        ret = Color(*super().__getitem__(key), color_mode="RGBA")

        # Reset color mode
        color_mode(old_color_mode, *old_color_range)
        return ret