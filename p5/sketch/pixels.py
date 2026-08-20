import numpy as np

from p5.core.color import Color, PackedColor

def _pack(value):
    """Normalize a color value (a Color object or an already-packed
    PackedColor) into a single packed ARGB int. Anything else (e.g. a
    list of colors from a slice assignment) is rejected immediately
    instead of being silently misinterpreted."""
    if isinstance(value, PackedColor):
        return value
    if isinstance(value, Color):
        r = int(value._red   * 255)
        g = int(value._green * 255)
        b = int(value._blue  * 255)
        a = int(value._alpha * 255)
        return PackedColor((a << 24) | (r << 16) | (g << 8) | b)
    raise TypeError(
        f"Cannot set a pixel to {value!r}; expected a Color or a "
        f"PackedColor (e.g. the result of color())."
    )


def _pack_bulk(tuples):
    """Vectorized equivalent of calling _pack() on every element of a
    list of (r, g, b[, a]) tuples. load_pixels() rebuilds this list from
    the whole canvas on every call, so packing element-by-element in a
    Python loop is the dominant cost of any per-pixel drawing loop -
    this does the same shift/OR packing as a couple of numpy ops over
    the whole array instead of 1 Python call per pixel."""
    if not tuples:
        return []
    arr = np.asarray(tuples, dtype=np.uint32)
    r, g, b = arr[:, 0], arr[:, 1], arr[:, 2]
    a = arr[:, 3] if arr.shape[1] > 3 else np.uint32(255)
    return ((a << 24) | (r << 16) | (g << 8) | b).tolist()


class Pixels(list):
    def __init__(self, l):
        """
        Create a Pixels object from a list of (r, g, b[, a]) tuples (as
        returned by PIL's ``Image.getdata()``). Values are normalized
        and stored as packed ARGB ints, matching what ``__getitem__``
        and ``update_pixels()`` expect.

        Args:
            l (list): List of tuples
        """
        super().__init__(_pack_bulk(l))

    def __setitem__(self, key, value):
        """
        Set the value of the Pixels object at the given index.

        Storage is always a single packed ARGB int (matching the fast
        path in ``color()`` and what ``update_pixels()`` expects).

        Args:
            key (int): Index
            value (Color | PackedColor): A Color object, or a packed
                color as returned by color()

        Raises:
            TypeError: If value is anything else (also catches slice
                assignment, e.g. pixels[1:3] = [...], since the slice's
                list of colors is not itself a Color/PackedColor).
        """
        super().__setitem__(key, _pack(value))

    def __getitem__(self, key):
        """
        Get the value of the Pixels object at the given index.

        Returns the packed ARGB int tagged as PackedColor (cheap - no
        Color object constructed) so it round-trips unambiguously if
        passed straight back into color()/Color(). Use
        red()/green()/blue()/alpha() to read channel values.

        Args:
            key (int): Index

        Returns:
            PackedColor: packed ARGB color
        """
        return PackedColor(super().__getitem__(key))
