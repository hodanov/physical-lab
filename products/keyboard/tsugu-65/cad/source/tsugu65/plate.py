"""Scissor retention plate.

Geometry is built in the keyboard frame: the half's local layout frame with the plate
top at ``z = 0``.
"""

from build123d import Align, Part, Pos, Rectangle, Sketch, extrude

from tsugu65.layout import HalfLayout

_MIN_CORNER = (Align.MIN, Align.MIN)


def outline(layout: HalfLayout) -> Sketch:
    """Return the stepped key-area outline of the half."""
    sketch = Sketch()
    for x_min, y_min, x_max, y_max in layout.row_spans():
        sketch += Pos(x_min, y_min) * Rectangle(x_max - x_min, y_max - y_min, align=_MIN_CORNER)
    return sketch.clean()


def openings(layout: HalfLayout) -> Sketch:
    """Return one scissor opening centered under each keycap.

    TODO(donor): keys from ``stabilized_keys`` also need wire-stabilizer retention
    features. Add them once the donor's stabilizers are measured; until then these
    keys get only the 1u center opening.
    """
    params = layout.params
    sketch = Sketch()
    for key in layout.place():
        depth = (
            params.half_height_opening_depth if key.half_height else params.scissor_opening_depth
        )
        sketch += Pos(key.center_x, key.center_y) * Rectangle(params.scissor_opening_width, depth)
    return sketch


def plate(layout: HalfLayout) -> Part:
    return extrude(outline(layout) - openings(layout), -layout.params.plate_thickness)
