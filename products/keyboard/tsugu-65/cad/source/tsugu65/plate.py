"""Scissor retention plate.

Geometry is built in the keyboard frame: the half's local layout frame with the plate
top at ``z = 0``.
"""

from build123d import Align, Part, Pos, Rectangle, Sketch, extrude

from tsugu65.layout import Half, place, row_spans
from tsugu65.params import Params

_MIN_CORNER = (Align.MIN, Align.MIN)


def outline(half: Half, params: Params) -> Sketch:
    """Return the stepped key-area outline of the half."""
    sketch = Sketch()
    for x_min, y_min, x_max, y_max in row_spans(half, params):
        sketch += Pos(x_min, y_min) * Rectangle(x_max - x_min, y_max - y_min, align=_MIN_CORNER)
    return sketch.clean()


def openings(half: Half, params: Params) -> Sketch:
    """Return one scissor opening centered under each keycap."""
    sketch = Sketch()
    for key in place(half, params):
        depth = (
            params.half_height_opening_depth if key.half_height else params.scissor_opening_depth
        )
        sketch += Pos(key.center_x, key.center_y) * Rectangle(params.scissor_opening_width, depth)
    return sketch


def plate(half: Half, params: Params) -> Part:
    return extrude(outline(half, params) - openings(half, params), -params.plate_thickness)
