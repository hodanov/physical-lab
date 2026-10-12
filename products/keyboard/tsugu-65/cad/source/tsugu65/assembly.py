"""Place the case and plate of one half in the world frame.

The keyboard frame is rotated about the X axis by the typing tilt so the back edge
rises, then the case bottom is cut flat at ``z = 0``.
"""

import math
from dataclasses import dataclass

from build123d import Keep, Part, Plane, Pos, Rot, split

from tsugu65 import case, plate
from tsugu65.layout import Half, HalfLayout
from tsugu65.params import Params


@dataclass(frozen=True)
class HalfModel:
    half: Half
    case: Part
    plate: Part


def build_half(half: Half, params: Params) -> HalfModel:
    layout = HalfLayout(half, params)
    tilt = math.radians(params.tilt_deg)
    _, key_depth = layout.extent()
    # Deep enough to reach below the tilted floor everywhere.
    blank_depth = (
        params.plate_thickness
        + params.interior_depth
        + params.floor_thickness
        + (key_depth + 2 * params.case_outer_offset) * math.sin(tilt)
        + 10
    )

    rotate = Rot(X=params.tilt_deg)
    case_blank = rotate * case.case_blank(layout, blank_depth)
    cavity = rotate * case.cavity(layout)
    # The floor is thinnest under the lowest point of the cavity.
    bottom_z = cavity.bounding_box().min.Z - params.floor_thickness / math.cos(tilt)

    to_ground = Pos(0, 0, -bottom_z)
    tilted_case = split(case_blank, Plane.XY.offset(bottom_z), keep=Keep.TOP)
    return HalfModel(
        half=half,
        case=to_ground * tilted_case,
        plate=to_ground * (rotate * plate.plate(layout)),
    )
