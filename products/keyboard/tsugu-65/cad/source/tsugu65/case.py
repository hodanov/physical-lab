"""Tray-style case that holds the plate flush with its rim.

Geometry is built in the keyboard frame (see ``tsugu65.plate``). The case blank
extends ``depth`` below the rim; ``tsugu65.assembly`` cuts the tilted bottom.
"""

from build123d import Box, Kind, Part, Pos, extrude, offset

from tsugu65 import plate
from tsugu65.layout import Half, extent, row_spans
from tsugu65.params import Params

# How far an opening's cutting box extends past the surfaces it must cut through.
_OVERCUT = 1.0


def cavity(half: Half, params: Params) -> Part:
    """Return the space under the plate, inside the plate-supporting ledge."""
    inner = offset(plate.outline(half, params), -params.plate_ledge, kind=Kind.INTERSECTION)
    return Pos(0, 0, -params.plate_thickness) * extrude(inner, -params.interior_depth)


def _opening_z(params: Params) -> float:
    return -params.plate_thickness - params.interior_depth / 2


def _usb_c_opening(half: Half, params: Params) -> Part:
    """Cut through the outer (left) wall of the left half, toward the back."""
    _, key_depth = extent(half, params)
    x_min = -(params.plate_clearance + params.wall_thickness) - _OVERCUT
    x_max = params.plate_ledge + _OVERCUT
    return Pos(
        (x_min + x_max) / 2, key_depth - params.usb_c_offset_from_back, _opening_z(params)
    ) * Box(x_max - x_min, params.usb_c_opening_width, params.usb_c_opening_height)


def _link_opening(half: Half, params: Params) -> Part:
    """Cut through the back wall near the inner end of the number row."""
    _, key_depth = extent(half, params)
    x_min, _, x_max, _ = row_spans(half, params)[0]
    x = (
        x_max - params.link_opening_inset
        if half is Half.LEFT
        else x_min + params.link_opening_inset
    )
    y_min = key_depth - params.plate_ledge - _OVERCUT
    y_max = key_depth + params.plate_clearance + params.wall_thickness + _OVERCUT
    return Pos(x, (y_min + y_max) / 2, _opening_z(params)) * Box(
        params.link_opening_width, y_max - y_min, params.link_opening_height
    )


def case_blank(half: Half, params: Params, depth: float) -> Part:
    """Return the case with its pocket, cavity, and openings, ``depth`` deep."""
    outline = plate.outline(half, params)
    outer = extrude(
        offset(outline, params.plate_clearance + params.wall_thickness, kind=Kind.ARC), -depth
    )
    pocket = extrude(
        offset(outline, params.plate_clearance, kind=Kind.ARC), -params.plate_thickness
    )
    result = outer - pocket - cavity(half, params) - _link_opening(half, params)
    if half is Half.LEFT:
        result -= _usb_c_opening(half, params)
    return result
