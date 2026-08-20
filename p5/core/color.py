#
# Part of p5: A Python package based on Processing
# Copyright (C) 2017-2019 Abhik Pal
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
from __future__ import annotations
import colorsys
import math
from typing import Optional, Tuple

from ..pmath import lerp
from ..pmath import constrain

from .constants import colour_codes
from . import p5

__all__ = ["color_mode", "Color", "color", "red", "green", "blue", "alpha", "hue", "saturation", "brightness", "lerp_color"]

_color_mults: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
_color_norm: Tuple[float, float, float, float] = (1 / 255, 1 / 255, 1 / 255, 1 / 255)
_rgb_color_mode: bool = True


class PackedColor(int):
    """ARGB color packed into a single int - the fast path returned by
    ``color()`` (RGB or HSB). Subclasses ``int`` so it works anywhere an
    int does, but stays distinguishable from a bare grayscale value (see
    ``parse_color()``). Mirrors ``Color``'s .red/.green/.blue/.alpha/
    .hue/.saturation/.brightness (+ short aliases), scaled by the current
    color_range. HSB values are recomputed from the stored RGB bytes each
    read, so they can drift slightly after an HSB-mode creation - same as
    Processing. Unlike ``Color.b``, .b here is always blue.
    """

    @property
    def red(self):
        return ((self >> 16) & 0xFF) / 255.0 * p5.renderer.style.color_range[0]

    @property
    def green(self):
        return ((self >> 8) & 0xFF) / 255.0 * p5.renderer.style.color_range[1]

    @property
    def blue(self):
        return (self & 0xFF) / 255.0 * p5.renderer.style.color_range[2]

    @property
    def alpha(self):
        return ((self >> 24) & 0xFF) / 255.0 * p5.renderer.style.color_range[3]

    @property
    def hue(self):
        h, _, _ = colorsys.rgb_to_hsv(
            ((self >> 16) & 0xFF) / 255.0, ((self >> 8) & 0xFF) / 255.0, (self & 0xFF) / 255.0
        )
        return h * p5.renderer.style.color_range[0]

    @property
    def saturation(self):
        _, s, _ = colorsys.rgb_to_hsv(
            ((self >> 16) & 0xFF) / 255.0, ((self >> 8) & 0xFF) / 255.0, (self & 0xFF) / 255.0
        )
        return s * p5.renderer.style.color_range[1]

    @property
    def brightness(self):
        _, _, v = colorsys.rgb_to_hsv(
            ((self >> 16) & 0xFF) / 255.0, ((self >> 8) & 0xFF) / 255.0, (self & 0xFF) / 255.0
        )
        return v * p5.renderer.style.color_range[2]

    r = red
    g = green
    b = blue
    a = alpha
    h = hue
    s = saturation
    v = brightness

    def lerp(self, target, amount):
        """Interpolate to `target` by `amount` (0-1). Mirrors
        ``Color.lerp()`` so it works for both ``Color`` and ``PackedColor``.
        """
        lerped = (lerp(s, t, amount) for s, t in zip(
            (self.red, self.green, self.blue, self.alpha),
            (target.red, target.green, target.blue, target.alpha),
        ))
        return Color(*lerped, color_mode="RGB")


def color_mode(
    mode: str,
    max_1: int = 255,
    max_2: Optional[int] = None,
    max_3: Optional[int] = None,
    max_alpha: int = 255,
):
    """Set the color mode of the renderer.

    :param mode: One of {'RGB', 'HSB'} corresponding to Red/Green/Blue
        or Hue/Saturation/Brightness

    :param max_1: Maximum value for the first color channel (default:
        255)

    :param max_2: Maximum value for the second color channel (default:
        max_1)

    :param max_3: Maximum value for the third color channel (default:
        max_1)

    :param max_alpha: Maximum value for the alpha channel (default:
        255)

    """
    global _color_mults, _color_norm, _rgb_color_mode

    if max_2 is None:
        max_2 = max_1

    if max_3 is None:
        max_3 = max_1

    _color_mults = (255.0 / max_1, 255.0 / max_2, 255.0 / max_3, 255.0 / max_alpha)
    _color_norm = (1.0 / max_1, 1.0 / max_2, 1.0 / max_3, 1.0 / max_alpha)
    _rgb_color_mode = mode.startswith("RGB")

    p5.renderer.style.color_range = (max_1, max_2, max_3, max_alpha)
    p5.renderer.style.color_parse_mode = mode


def parse_color(
    *args, color_mode: str = "RGB", normed: bool = False, **kwargs
) -> Tuple[float, float, float, float]:
    """Parses a color from a range of different input formats.

    This assumes that the args and kwargs are in the following form:

    - gray
    - gray, alpha = ...
    - gray, alpha
    - r, g, b
    - h, s, v
    - r, g, b, a
    - h, s, v, a
    - hex
    - colour name

    - gray = ...
    - gray = ..., alpha = ...
    - r = ..., g = ..., b = ...,
    - red = ..., green = ..., blue = ...,
    - h = ..., s = ..., b = ...,
    - hue = ..., saturation = ..., brightness = ...,
    - r = ..., g = ..., b = ..., a = ...
    - red = ..., green = ..., blue = ..., alpha = ...
    - h = ..., s = ..., b = ..., a = ...
    - hue = ..., saturation = ..., brightness = ..., alpha = ...

    :param args: The positional arguments that define the color.
    :type args: tuple

    :param kwargs: The keyword arguments that define the color.
    :type kwargs: dict

    :returns: The color parsed as red, green, blue, alpha values.

    """

    # Already-packed color (from color()'s fast path) - unpack directly,
    # it's not a grayscale intensity even though it's also just an int.
    if len(args) == 1 and not kwargs and isinstance(args[0], PackedColor):
        packed = args[0]
        r = (packed >> 16) & 0xFF
        g = (packed >> 8) & 0xFF
        b = packed & 0xFF
        a = (packed >> 24) & 0xFF
        return r / 255.0, g / 255.0, b / 255.0, a / 255.0

    if "alpha" in kwargs:
        alpha = kwargs["alpha"]
    elif "a" in kwargs:
        alpha = kwargs["a"]
    elif normed:
        alpha = 1
    else:
        # Color object are sometimes created before we initialise the renderer
        # So we have to check if the renderer is None or not
        alpha = p5.renderer.style.color_range[3] if p5.renderer else 255

    hsb = None
    rgb = None

    if len(args) == 1:
        if isinstance(args[0], (int, float)):
            gray = args[0]
            rgb = gray, gray, gray
        elif isinstance(args[0], str):
            name = args[0].lower()
            if name == "none":
                alpha = 0
                rgb = (0, 0, 0)
            else:
                if name[0] == "#":
                    hexadecimal = args[0]
                elif name in colour_codes.keys():
                    hexadecimal = colour_codes[name]
                else:
                    raise ValueError(f"Invalid colour name {name}")

                alpha = 255
                _r = int(hexadecimal[1:3], 16)
                _g = int(hexadecimal[3:5], 16)
                _b = int(hexadecimal[5:7], 16)
                rgb = (_r, _g, _b)

    elif len(args) == 2:
        gray, alpha = args
        rgb = gray, gray, gray
    elif (len(args) == 3) and color_mode.startswith("RGB"):
        rgb = args
    elif (len(args) == 3) and color_mode.startswith("HSB"):
        hsb = args
    elif (len(args) == 4) and color_mode.startswith("RGB"):
        _r, _g, _b, alpha = args
        rgb = (_r, _g, _b)
    elif (len(args) == 4) and color_mode.startswith("HSB"):
        _h, _s, _b, alpha = args
        hsb = (_h, _s, _b)
    elif "gray" in kwargs:
        gray = kwargs["gray"]
        rgb = gray, gray, gray
    elif all(param in kwargs for param in ["red", "green", "blue"]):
        _r = kwargs["red"]
        _g = kwargs["green"]
        _b = kwargs["blue"]
        rgb = (_r, _g, _b)
    elif all(param in kwargs for param in ["r", "g", "b"]):
        _r = kwargs["r"]
        _g = kwargs["g"]
        _b = kwargs["b"]
        rgb = (_r, _g, _b)
    elif all(param in kwargs for param in ["hue", "saturation", "brightness"]):
        _h = kwargs["hue"]
        _s = kwargs["saturation"]
        _b = kwargs["brightness"]
        hsb = (_h, _s, _b)
    elif all(param in kwargs for param in ["h", "s", "b"]):
        _h = kwargs["h"]
        _s = kwargs["s"]
        _b = kwargs["b"]
        hsb = (_h, _s, _b)
    else:
        raise ValueError("Failed to parse color.")

    if hsb is not None:
        h, s, b = hsb
        if not normed:
            h = constrain(
                h / (p5.renderer.style.color_range[0] if p5.renderer else 255), 0, 1
            )
            s = constrain(
                s / (p5.renderer.style.color_range[1] if p5.renderer else 255), 0, 1
            )
            b = constrain(
                b / (p5.renderer.style.color_range[2] if p5.renderer else 255), 0, 1
            )
        red, green, blue = colorsys.hsv_to_rgb(h, s, b)

    if rgb is not None:
        r, g, b = rgb
        if not normed:
            red = constrain(
                r / (p5.renderer.style.color_range[0] if p5.renderer else 255), 0, 1
            )
            green = constrain(
                g / (p5.renderer.style.color_range[1] if p5.renderer else 255), 0, 1
            )
            blue = constrain(
                b / (p5.renderer.style.color_range[2] if p5.renderer else 255), 0, 1
            )
        else:
            red, green, blue = r, g, b

    if not normed:
        alpha = constrain(
            alpha / p5.renderer.style.color_range[3] if p5.renderer else 255, 0, 1
        )

    return red, green, blue, alpha


# NOTE: By default constructor expects color value to be in [0,255] range
# which is then normalized to [0,1] range and then used by the renderer instance
class Color:
    """
    Represents a color.
    """

    def __init__(
        self, *args, color_mode: Optional[str] = None, normed: bool = False, **kwargs
    ):
        if color_mode is None:
            color_mode = p5.renderer.style.color_parse_mode if p5.renderer else "RGB"

        if (len(args) == 1) and isinstance(args[0], Color):
            r = args[0]._red
            g = args[0]._green
            b = args[0]._blue
            a = args[0]._alpha
        elif len(args) == 2 and isinstance(args[0], Color):
            r = args[0]._red
            g = args[0]._green
            b = args[0]._blue
            a = args[1]
        else:
            r, g, b, a = parse_color(
                *args, color_mode=color_mode, normed=normed, **kwargs
            )
        self._red: float = r
        self._green: float = g
        self._blue: float = b
        self._alpha: float = a

        self._recompute_hsb()

    def _recompute_rgb(self):
        """Recompute the RGB values from HSB values."""
        r, g, b = colorsys.hsv_to_rgb(self._hue, self._saturation, self._brightness)
        self._red = r
        self._greeen = g
        self._blue = b

    def _recompute_hsb(self):
        """Recompute the HSB values from the RGB values."""
        h, s, b = colorsys.rgb_to_hsv(self._red, self._green, self._blue)
        self._hue = h
        self._saturation = s
        self._brightness = b

    def lerp(self, target: Color, amount: float) -> Color:
        """Linearly interpolate one color to another by the given amount.

        :param target: The target color to lerp to.

        :param amount: The amount by which the color should be lerped
            (should be a float between 0 and 1).

        :returns: A new color lerped between the current color and the
            other color.

        """
        lerped = (lerp(s, t, amount) for s, t in zip(self.rgba, target.rgba))
        return Color(*lerped, color_mode="RGB")

    def __repr__(self):
        return f"Color( red={self._red}, green={self._green}, blue={self._blue} )"

    __str__ = __repr__

    def __eq__(self, other):
        return all(
            math.isclose(sc, oc) for sc, oc in zip(self.normalized, other.normalized)
        )

    def __neq__(self, other):
        return not all(
            math.isclose(sc, oc) for sc, oc in zip(self.normalized, other.normalized)
        )

    @property
    def normalized(self):
        """Normalized RGBA color values"""
        return (self._red, self._green, self._blue, self._alpha)

    @property
    def normalized_rgb(self):
        """Normalized RGB color values"""
        return (self._red, self._green, self._blue)

    @property
    def gray(self):
        """The gray-scale value of the color.

        Performs a luminance conversion of the current color to
        grayscale.

        """
        # The formula we use to convert to grayscale is approximate
        # and probably not as accurate as a proper coloremetric
        # conversion. However, the number of calculations required is
        # less and GIMP uses something similar so we should be fine.
        #
        # REFERENCES:
        #
        # - "Converting Color Images to B&W"
        #   <https://www.gimp.org/tutorials/Color2BW/>
        #
        # - "Luma Coding in Video Systems" from "Grayscale"
        #   <https://en.wikipedia.org/wiki/Grayscale#Luma_coding_in_video_systems>
        #
        # - Wikipedia : Grayscale
        #   <https://en.wikipedia.org/wiki/Grayscale#Converting_color_to_grayscale>
        #
        # - Conversion to grayscale, sample implementation (StackOverflow)
        # <https://stackoverflow.com/a/15686412>
        norm_gray = 0.299 * self._red + 0.587 * self._green + 0.144 * self._blue
        return norm_gray * 255

    @gray.setter
    def gray(self, value: float):
        value = constrain(value / 255, 0, 1)
        self._red = value
        self._green = value
        self._blue = value
        self._recompute_hsb()

    @property
    def alpha(self):
        """The alpha value for the color."""
        return self._alpha * p5.renderer.style.color_range[3]

    @alpha.setter
    def alpha(self, value: float):
        self._alpha = constrain(value / p5.renderer.style.color_range[3], 0, 1)

    @property
    def rgb(self):
        """
        :returns: Color components in RGB.
        :rtype: tuple
        """
        return (self.red, self.green, self.blue)

    @property
    def rgba(self):
        """
        :returns: Color components in RGBA.
        :rtype: tuple
        """
        return (self.red, self.green, self.blue, self.alpha)

    @property
    def red(self):
        """The red component of the color"""
        return self._red * p5.renderer.style.color_range[0]

    @red.setter
    def red(self, value: float):
        self._red = constrain(value / p5.renderer.style.color_range[0], 0, 1)
        self._recompute_hsb()

    @property
    def green(self):
        """The green component of the color"""
        return self._green * p5.renderer.style.color_range[1]

    @green.setter
    def green(self, value: float):
        self._green = constrain(value / p5.renderer.style.color_range[1], 0, 1)
        self._recompute_hsb()

    @property
    def blue(self):
        """The blue component of the color"""
        return self._blue * p5.renderer.style.color_range[2]

    @blue.setter
    def blue(self, value: float):
        self._blue = constrain(value / p5.renderer.style.color_range[2], 0, 1)
        self._recompute_hsb()

    @property
    def hsb(self):
        """
        :returns: Color components in HSB.
        :rtype: tuple
        """
        return (self._hue, self._saturation, self._brightness)

    @property
    def hsba(self):
        """
        :returns: Color components in HSBA.
        :rtype: tuple
        """
        return (self.hue, self.saturation, self.brightness, self.alpha)

    @property
    def hue(self):
        """The hue component of the color"""
        return self._hue * p5.renderer.style.color_range[0]

    @hue.setter
    def hue(self, value: float):
        self._hue = constrain(value / p5.renderer.style.color_range[0], 0, 1)
        self._recompute_rgb()

    @property
    def saturation(self):
        """The saturation component of the color"""
        return self._saturation * p5.renderer.style.color_range[1]

    @saturation.setter
    def saturation(self, value: float):
        self._saturation = constrain(value / p5.renderer.style.color_range[1], 0, 1)
        self._recompute_rgb()

    @property
    def brightness(self):
        """The brightness component of the color"""
        return self._brightness * p5.renderer.style.color_range[2]

    @brightness.setter
    def brightness(self, value: float):
        self._brightness = constrain(value / p5.renderer.style.color_range[2], 0, 1)
        self._recompute_rgb()

    # ...and some convenient aliases
    r = red
    g = green
    h = hue
    s = saturation
    value = brightness
    v = value

    # `b` is tricky. depending on the current color code, this could
    # either be the brightness value or the blue value.
    @property
    def b(self):
        """The blue or the brightness value (depending on the color mode)."""
        if p5.renderer.style.color_parse_mode == "RGB":
            return self.blue
        elif p5.renderer.style.color_parse_mode == "HSB":
            return self.brightness
        else:
            raise ValueError(f"Unknown color mode {p5.renderer.style.color_parse_mode}")

    @b.setter
    def b(self, value: float):
        if p5.renderer.style.color_parse_mode == "RGB":
            self.blue = value
        elif p5.renderer.style.color_parse_mode == "HSB":
            self.brightness = value
        else:
            raise ValueError(f"Unknown color mode {p5.renderer.style.color_parse_mode}")

    @property
    def hex(self):
        """
        :returns: Color as a hex value
        :rtype: str
        """
        return ("#%02x%02x%02x" % self.rgb).upper()

def color(*args, **kwargs) -> PackedColor:
    """Create a new color.

    :param args: The positional arguments that define the color.
    :type args: tuple

    :param kwargs: The keyword arguments that define the color.
    :type kwargs: dict

    :returns: A new color, packed as ARGB.
    :rtype: PackedColor

    """
    if not kwargs:
        n = len(args)
        if n == 3 or n == 4:
            if _rgb_color_mode:
                k = _color_mults
                r = int(args[0] * k[0]); r = 255 if r > 255 else (0 if r < 0 else r)
                g = int(args[1] * k[1]); g = 255 if g > 255 else (0 if g < 0 else g)
                b = int(args[2] * k[2]); b = 255 if b > 255 else (0 if b < 0 else b)
                a = int(args[3] * k[3]) if n == 4 else 255
                a = 255 if a > 255 else (0 if a < 0 else a)
            else:
                k = _color_norm
                h = args[0] * k[0]; h = 1.0 if h > 1.0 else (0.0 if h < 0.0 else h)
                s = args[1] * k[1]; s = 1.0 if s > 1.0 else (0.0 if s < 0.0 else s)
                v = args[2] * k[2]; v = 1.0 if v > 1.0 else (0.0 if v < 0.0 else v)
                r, g, b = colorsys.hsv_to_rgb(h, s, v)

                r = int(r * 255); r = 255 if r > 255 else (0 if r < 0 else r)
                g = int(g * 255); g = 255 if g > 255 else (0 if g < 0 else g)
                b = int(b * 255); b = 255 if b > 255 else (0 if b < 0 else b)
                a = int(args[3] * k[3] * 255) if n == 4 else 255
                a = 255 if a > 255 else (0 if a < 0 else a)
            return PackedColor((a << 24) | (r << 16) | (g << 8) | b)

    # Rarer shapes (gray, gray+alpha, existing Color, hex/name, kwargs) -
    # funnel through parse_color(). Color needs its own case since
    # parse_color() doesn't know about it (Color.__init__ handles that).
    if len(args) == 1 and isinstance(args[0], Color):
        r, g, b, a = args[0]._red, args[0]._green, args[0]._blue, args[0]._alpha
    elif len(args) == 2 and isinstance(args[0], Color):
        max_alpha = p5.renderer.style.color_range[3] if p5.renderer else 255
        r, g, b = args[0]._red, args[0]._green, args[0]._blue
        a = args[1] / max_alpha
    else:
        r, g, b, a = parse_color(
            *args, color_mode=("RGB" if _rgb_color_mode else "HSB"), normed=False, **kwargs
        )

    r = int(r * 255); r = 255 if r > 255 else (0 if r < 0 else r)
    g = int(g * 255); g = 255 if g > 255 else (0 if g < 0 else g)
    b = int(b * 255); b = 255 if b > 255 else (0 if b < 0 else b)
    a = int(a * 255); a = 255 if a > 255 else (0 if a < 0 else a)
    return PackedColor((a << 24) | (r << 16) | (g << 8) | b)

def red(c):
    """Get the red component of a color.

    :param c: The color to get the red component of.
    :type c: Color

    :returns: The red component of the color.

    """
    return c.red

def green(c):
    """Get the green component of a color.

    :param c: The color to get the green component of.
    :type c: Color

    :returns: The green component of the color.

    """
    return c.green

def blue(c):
    """Get the blue component of a color.

    :param c: The color to get the blue component of.
    :type c: Color

    :returns: The blue component of the color.

    """
    return c.blue

def alpha(c):
    """Get the alpha component of a color.

    :param c: The color to get the alpha component of.
    :type c: Color

    :returns: The alpha component of the color.

    """
    return c.alpha

def hue(c):
    """Get the HSB hue component of a color.

    :param c: The color to get the hue component of.
    :type c: Color

    :returns: The hue component of the color.

    """
    return c.hue

def saturation(c):
    """Get the HSB saturation component of a color.

    :param c: The color to get the saturation component of.
    :type c: Color

    :returns: The saturation component of the color.

    """
    return c.saturation

def brightness(c):
    """Get the HSB brightness component of a color.

    :param c: The color to get the brightness component of.
    :type c: Color

    :returns: The brightness component of the color.

    """
    return c.brightness

def lerp_color(c1, c2, amt):
    """Linear interpolation between 2 colors.

    :param c1: The color at the start of the interpolation
    :param c2: The color at the end of the interpolation
    :param amt: The fractional distance [0.0...1.0] from c1 to c2
    :type c1, c2: Color
    :type amt: float

    :returns: The interpolated color.

    """
    return c1.lerp(c2, amt)
