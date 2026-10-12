"""Drawing specification for the FreeCAD TechDraw renderer.

``drawings/make_drawings.py`` renders one TechDraw page per half from this
specification. Dimension endpoints are vertices of the assembled parts in the world
frame, so the renderer attaches each dimension to real geometry and checks the value
it measures against ``expected_mm``.
"""

import itertools
import math
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from build123d import Axis, Part, Pos, Vector, Wire

from tsugu65.assembly import HalfModel
from tsugu65.layout import Half, Key, keys_in


class View(StrEnum):
    TOP = "top"
    FRONT = "front"
    SIDE = "side"


@dataclass(frozen=True, slots=True)
class ViewOrientation:
    """A view ``direction`` from the part toward the viewer, and the page's ``up``."""

    direction: Vector
    up: Vector

    @property
    def x_direction(self) -> Vector:
        """Return the direction that points right on the page."""
        return self.up.cross(self.direction)


def view_orientations(half: Half) -> dict[View, ViewOrientation]:
    """Return the third-angle views of ``half``; the side view faces its outer side."""
    outer_side = -1.0 if half is Half.LEFT else 1.0
    return {
        View.TOP: ViewOrientation(Vector(0, 0, 1), Vector(0, 1, 0)),
        View.FRONT: ViewOrientation(Vector(0, -1, 0), Vector(0, 0, 1)),
        View.SIDE: ViewOrientation(Vector(outer_side, 0, 0), Vector(0, 0, 1)),
    }


class DimensionKind(StrEnum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    ALIGNED = "aligned"


@dataclass(frozen=True, slots=True)
class Dimension:
    """A distance between two part vertices, drawn in one view."""

    name: str
    view: View
    kind: DimensionKind
    start: Vector
    end: Vector

    def measure(self, orientation: ViewOrientation) -> float:
        """Return the distance a view with ``orientation`` shows for this dimension."""
        delta = self.end - self.start
        horizontal = abs(delta.dot(orientation.x_direction))
        vertical = abs(delta.dot(orientation.up))
        match self.kind:
            case DimensionKind.HORIZONTAL:
                return horizontal
            case DimensionKind.VERTICAL:
                return vertical
            case DimensionKind.ALIGNED:
                return math.hypot(horizontal, vertical)


def _points(shape: Part | Wire) -> list[Vector]:
    return [Vector(vertex.X, vertex.Y, vertex.Z) for vertex in shape.vertices()]


def _to_keyboard(model: HalfModel, point: Vector) -> Vector:
    return (model.keyboard_to_world.inverse() * Pos(point)).position


def _opening_back_left_corner(model: HalfModel, key: Key) -> Vector:
    tolerance = 1e-6
    layout = model.layout
    inside_cell = layout.params.key_pitch / 2 - tolerance
    placed = next(p for p in layout.placed_keys() if p.name == key.name)
    plate = [(point, _to_keyboard(model, point)) for point in _points(model.plate)]
    plate_top_in_cell = [
        (point, local)
        for point, local in plate
        if abs(local.Z) < tolerance
        and abs(local.X - placed.center_x) < inside_cell
        and abs(local.Y - placed.center_y) < inside_cell
    ]
    corner, _ = min(plate_top_in_cell, key=lambda pair: (round(pair[1].X, 6), -pair[1].Y))
    return corner


def _key_pitch_corners(model: HalfModel) -> tuple[Vector, Vector]:
    home_row = 2
    row = sorted(
        (key for key in keys_in(model.layout.half) if key.row == home_row),
        key=lambda key: key.x_u,
    )
    first, second = next(
        (a, b)
        for a, b in itertools.pairwise(row)
        if a.width_u == b.width_u == a.height_u == b.height_u == 1
    )
    return _opening_back_left_corner(model, first), _opening_back_left_corner(model, second)


def _usb_c_dimensions(model: HalfModel, case_back_bottom: Vector) -> list[Dimension]:
    outer_face = model.case.faces().filter_by(Axis.X).sort_by(Axis.X)[0]
    (opening,) = outer_face.inner_wires()
    by_height = sorted(_points(opening), key=lambda p: _to_keyboard(model, p).Z)
    bottom_front, bottom_back = sorted(by_height[:2], key=lambda p: _to_keyboard(model, p).Y)
    top_back = max(by_height[2:], key=lambda p: _to_keyboard(model, p).Y)
    return [
        Dimension("usb_c_width", View.SIDE, DimensionKind.ALIGNED, bottom_front, bottom_back),
        Dimension("usb_c_height", View.SIDE, DimensionKind.ALIGNED, bottom_back, top_back),
        Dimension(
            "usb_c_from_back", View.SIDE, DimensionKind.HORIZONTAL, bottom_back, case_back_bottom
        ),
        Dimension(
            "usb_c_from_bottom", View.SIDE, DimensionKind.VERTICAL, case_back_bottom, bottom_back
        ),
    ]


def _on_ground(points: Sequence[Vector]) -> list[Vector]:
    tolerance = 1e-6
    return [point for point in points if abs(point.Z) < tolerance]


def dimensions(model: HalfModel) -> tuple[Dimension, ...]:
    """Return the dimensions drawn for ``model``, in drawing order."""
    case = _points(model.case)
    ground = _on_ground(case)
    front_top = min(case, key=lambda p: (p.Y, -p.Z))
    front_bottom = min(ground, key=lambda p: p.Y)
    back_top = max(case, key=lambda p: (p.Z, p.Y))
    back_bottom = max(ground, key=lambda p: p.Y)
    pitch_start, pitch_end = _key_pitch_corners(model)

    result = [
        Dimension(
            "overall_width",
            View.TOP,
            DimensionKind.HORIZONTAL,
            min(case, key=lambda p: p.X),
            max(case, key=lambda p: p.X),
        ),
        Dimension(
            "overall_depth",
            View.TOP,
            DimensionKind.VERTICAL,
            min(case, key=lambda p: p.Y),
            max(case, key=lambda p: p.Y),
        ),
        Dimension("key_pitch", View.TOP, DimensionKind.HORIZONTAL, pitch_start, pitch_end),
        Dimension("overall_height", View.SIDE, DimensionKind.VERTICAL, back_bottom, back_top),
        Dimension("front_height", View.SIDE, DimensionKind.VERTICAL, front_bottom, front_top),
    ]
    if model.layout.half is Half.LEFT:
        result += _usb_c_dimensions(model, back_bottom)
    return tuple(result)


def drawing_spec(model: HalfModel, stem: str) -> dict[str, Any]:
    """Return the JSON-ready drawing specification of ``model``.

    ``stem`` names the STEP export (``<stem>.step``) and its top-level label.
    """
    orientations = view_orientations(model.layout.half)
    return {
        "step": f"{stem}.step",
        "source_label": stem,
        "title": f"TSUGU Split 65 {model.layout.half.value} half",
        "views": [
            {
                "name": view.value,
                "direction": list(orientation.direction),
                "x_direction": list(orientation.x_direction),
            }
            for view, orientation in orientations.items()
        ],
        "dimensions": [
            {
                "name": dim.name,
                "view": dim.view.value,
                "kind": dim.kind.value,
                "start": list(dim.start),
                "end": list(dim.end),
                "expected_mm": dim.measure(orientations[dim.view]),
            }
            for dim in dimensions(model)
        ],
    }
