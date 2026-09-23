"""Tests for the generated plate and case geometry."""

from functools import cache

import pytest
from build123d import Axis, Face, Part, SortBy, Vector

from tsugu65.assembly import HalfModel, build_half
from tsugu65.layout import Half, extent, keys_in
from tsugu65.params import Params

FLAT = Params(tilt_deg=0)


@cache
def model(half: Half, params: Params) -> HalfModel:
    return build_half(half, params)


def top_face(part: Part) -> Face:
    """Return the upper of the two largest (top and bottom) faces."""
    return part.faces().sort_by(SortBy.AREA)[-2:].sort_by(Axis.Z)[-1]


def top_z(params: Params) -> float:
    """Height of the case rim when the model is not tilted."""
    return params.floor_thickness + params.interior_depth + params.plate_thickness


def opening_z(params: Params) -> float:
    return top_z(params) - params.plate_thickness - params.interior_depth / 2


def in_wall(params: Params) -> float:
    """Offset from the key area edge to the middle of the case wall."""
    return params.plate_clearance + params.wall_thickness / 2


@pytest.mark.parametrize("half", list(Half))
def test_parts_are_valid_solids(half: Half) -> None:
    built = model(half, Params())

    assert built.case.is_valid
    assert built.plate.is_valid
    assert built.case.volume > 0
    assert built.plate.volume > 0


@pytest.mark.parametrize("half", list(Half))
def test_plate_covers_key_area_with_one_opening_per_key(half: Half) -> None:
    built = model(half, FLAT)
    width, depth = extent(half, FLAT)

    size = built.plate.bounding_box().size
    assert pytest.approx((width, depth, FLAT.plate_thickness)) == (size.X, size.Y, size.Z)

    top = top_face(built.plate)
    assert len(top.inner_wires()) == len(keys_in(half))


@pytest.mark.parametrize("half", list(Half))
def test_plate_does_not_interfere_with_case(half: Half) -> None:
    built = model(half, Params())

    assert (built.case & built.plate).volume == pytest.approx(0, abs=1e-6)


@pytest.mark.parametrize("half", list(Half))
def test_plate_top_is_flush_with_case_rim(half: Half) -> None:
    built = model(half, FLAT)

    assert pytest.approx(top_z(FLAT)) == built.case.bounding_box().max.Z
    assert pytest.approx(top_z(FLAT)) == built.plate.bounding_box().max.Z


@pytest.mark.parametrize("half", list(Half))
def test_case_rests_on_z0_with_typing_tilt(half: Half) -> None:
    params = Params(tilt_deg=3.0)
    built = model(half, params)

    assert pytest.approx(0, abs=1e-6) == built.case.bounding_box().min.Z
    top = top_face(built.plate)
    normal = top.normal_at()
    assert normal.get_angle(Vector(0, 0, 1)) == pytest.approx(3.0)
    # The back edge rises: the normal leans toward the front.
    assert normal.Y < 0


def test_usb_c_opening_is_on_left_side_toward_back() -> None:
    case = model(Half.LEFT, FLAT).case
    _, depth = extent(Half.LEFT, FLAT)
    x = -in_wall(FLAT)
    z = opening_z(FLAT)

    assert not case.is_inside((x, depth - FLAT.usb_c_offset_from_back, z))
    assert case.is_inside((x, depth / 3, z))


def test_right_half_has_no_usb_c_opening() -> None:
    case = model(Half.RIGHT, FLAT).case
    width, depth = extent(Half.RIGHT, FLAT)

    assert case.is_inside(
        (width + in_wall(FLAT), depth - FLAT.usb_c_offset_from_back, opening_z(FLAT))
    )


@pytest.mark.parametrize(
    ("half", "number_row_inner_end", "direction"),
    [(Half.LEFT, 7.0, -1), (Half.RIGHT, 0.5, 1)],
)
def test_link_opening_is_on_back_wall_near_inner_side(
    half: Half, number_row_inner_end: float, direction: int
) -> None:
    case = model(half, FLAT).case
    _, depth = extent(half, FLAT)
    x = number_row_inner_end * FLAT.key_pitch + direction * FLAT.link_opening_inset
    y = depth + in_wall(FLAT)
    z = opening_z(FLAT)

    assert not case.is_inside((x, y, z))
    assert case.is_inside((x + direction * 20, y, z))
