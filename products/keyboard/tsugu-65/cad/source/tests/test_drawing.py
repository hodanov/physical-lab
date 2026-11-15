"""Tests for the drawing specification handed to the FreeCAD TechDraw renderer."""

import json
from functools import cache

import pytest
from build123d import Part, Vector

from tsugu65.assembly import HalfModel, build_half
from tsugu65.drawing import Dimension, View, dimensions, drawing_spec, view_orientations
from tsugu65.layout import Half
from tsugu65.params import Params

FLAT = Params(tilt_deg=0)


@cache
def model(half: Half, params: Params) -> HalfModel:
    return build_half(half, params)


def by_name(half: Half, params: Params) -> dict[str, Dimension]:
    return {dim.name: dim for dim in dimensions(model(half, params))}


def measured(half: Half, params: Params, name: str) -> float:
    dim = by_name(half, params)[name]
    return dim.measure(view_orientations(half)[dim.view])


def is_vertex_of(point: Vector, part: Part) -> bool:
    return any((point - Vector(v.X, v.Y, v.Z)).length < 1e-6 for v in part.vertices())


@pytest.mark.parametrize("half", list(Half))
def test_view_x_direction_is_up_cross_direction(half: Half) -> None:
    for orientation in view_orientations(half).values():
        expected = orientation.up.cross(orientation.direction)
        assert (orientation.x_direction - expected).length < 1e-9
        assert orientation.x_direction.length == pytest.approx(1)


@pytest.mark.parametrize(("half", "outward_x"), [(Half.LEFT, -1), (Half.RIGHT, 1)])
def test_side_view_looks_at_outer_side(half: Half, outward_x: float) -> None:
    orientations = view_orientations(half)

    assert outward_x == orientations[View.SIDE].direction.X
    assert tuple(orientations[View.TOP].direction) == (0, 0, 1)
    assert tuple(orientations[View.FRONT].direction) == (0, -1, 0)


@pytest.mark.parametrize("half", list(Half))
def test_dimension_endpoints_are_part_vertices(half: Half) -> None:
    built = model(half, Params())

    for dim in dimensions(built):
        for point in (dim.start, dim.end):
            assert is_vertex_of(point, built.case) or is_vertex_of(point, built.plate), dim.name


@pytest.mark.parametrize("half", list(Half))
def test_overall_dimensions_match_case_bounding_box(half: Half) -> None:
    size = model(half, Params()).case.bounding_box().size

    assert measured(half, Params(), "overall_width") == pytest.approx(size.X)
    assert measured(half, Params(), "overall_depth") == pytest.approx(size.Y)
    assert measured(half, Params(), "overall_height") == pytest.approx(size.Z)


@pytest.mark.parametrize("half", list(Half))
def test_key_pitch_matches_params(half: Half) -> None:
    assert measured(half, Params(), "key_pitch") == pytest.approx(Params().key_pitch)


@pytest.mark.parametrize("half", list(Half))
def test_front_is_lower_than_back_only_when_tilted(half: Half) -> None:
    assert measured(half, Params(), "front_height") < measured(half, Params(), "overall_height")
    assert measured(half, FLAT, "front_height") == pytest.approx(
        measured(half, FLAT, "overall_height")
    )


def test_usb_c_opening_is_dimensioned_on_left_side_view_only() -> None:
    params = Params()
    left = by_name(Half.LEFT, params)

    usb_c = {name: dim for name, dim in left.items() if name.startswith("usb_c_")}
    assert set(usb_c) == {"usb_c_width", "usb_c_height", "usb_c_from_back", "usb_c_from_bottom"}
    assert all(dim.view is View.SIDE for dim in usb_c.values())
    assert measured(Half.LEFT, params, "usb_c_width") == pytest.approx(params.usb_c_opening_width)
    assert measured(Half.LEFT, params, "usb_c_height") == pytest.approx(params.usb_c_opening_height)
    assert not any(name.startswith("usb_c_") for name in by_name(Half.RIGHT, params))


def test_usb_c_position_on_flat_case() -> None:
    params = FLAT
    _, key_depth = model(Half.LEFT, params).layout.extent()
    opening_back_y = key_depth - params.usb_c_offset_from_back + params.usb_c_opening_width / 2
    rim_z = params.floor_thickness + params.interior_depth + params.plate_thickness
    opening_bottom_z = (
        rim_z - params.plate_thickness - params.interior_depth / 2 - params.usb_c_opening_height / 2
    )

    assert measured(Half.LEFT, params, "usb_c_from_back") == pytest.approx(
        key_depth + params.case_outer_offset - opening_back_y
    )
    assert measured(Half.LEFT, params, "usb_c_from_bottom") == pytest.approx(opening_bottom_z)


@pytest.mark.parametrize("half", list(Half))
def test_drawing_spec_is_json_with_expected_values(half: Half) -> None:
    built = model(half, Params())
    stem = f"tsugu65-{half.value}"

    spec = json.loads(json.dumps(drawing_spec(built, stem)))

    assert spec["step"] == f"{stem}.step"
    assert spec["source_label"] == stem
    views = {view["name"]: view for view in spec["views"]}
    assert set(views) == {view.value for view in View}
    orientations = view_orientations(half)
    for dim, entry in zip(dimensions(built), spec["dimensions"], strict=True):
        assert entry["name"] == dim.name
        assert entry["view"] == dim.view.value
        assert entry["kind"] == dim.kind.value
        assert entry["expected_mm"] == pytest.approx(dim.measure(orientations[dim.view]))
        assert entry["expected_mm"] > 0
