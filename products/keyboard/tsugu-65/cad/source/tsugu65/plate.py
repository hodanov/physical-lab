"""Scissor retention plate.

Geometry is built in the keyboard frame: the half's local layout frame with the plate
top at ``z = 0``.
"""

from build123d import Align, Part, Pos, Rectangle, Sketch, extrude

from tsugu65.layout import HalfLayout


def outline(layout: HalfLayout) -> Sketch:
    """Return the stepped key-area outline of the half."""
    min_corner = (Align.MIN, Align.MIN)
    sketch = Sketch()
    for span in layout.row_spans():
        sketch += Pos(span.x_min, span.y_min) * Rectangle(span.width, span.depth, align=min_corner)
    return sketch.clean()


def _scissor_openings(layout: HalfLayout) -> Sketch:
    params = layout.params
    sketch = Sketch()
    for key in layout.placed_keys():
        depth = (
            params.half_height_opening_depth if key.half_height else params.scissor_opening_depth
        )
        sketch += Pos(key.center_x, key.center_y) * Rectangle(params.scissor_opening_width, depth)
    return sketch


def plate(layout: HalfLayout) -> Part:
    """Return the plate with one scissor opening centered under each keycap.

    TODO(donor): keys from ``stabilized_keys`` also need wire-stabilizer retention
    features. Add them once the donor's stabilizers are measured; until then these
    keys get only the 1u center opening.
    """
    return extrude(outline(layout) - _scissor_openings(layout), -layout.params.plate_thickness)
