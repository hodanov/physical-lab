"""Render TechDraw drawings from the drawing specifications in an export directory.

Runs inside FreeCAD's bundled Python 3.11; start it with ``uv run tsugu65-drawings``,
which sets ``TSUGU65_EXPORT_DIR``. For each ``*-drawing.json`` written by
``tsugu65-build``, this imports the STEP export, lays out third-angle views on an A3
page, attaches each dimension to the vertices named in the specification, checks every
measured value against ``expected_mm``, and saves ``<spec stem>.FCStd`` next to the
specification. Any failed check raises, so nothing is saved for that half.
"""

import datetime
import json
import os
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self

import FreeCAD as App
import Import

_TOLERANCE = 1e-3
_DIMENSION_TYPES = {"horizontal": "DistanceX", "vertical": "DistanceY", "aligned": "Distance"}


@dataclass(frozen=True, slots=True)
class _Bounds:
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    @classmethod
    def around(cls, points: Sequence[tuple[float, float]]) -> Self:
        xs = [x for x, _ in points]
        ys = [y for _, y in points]
        return cls(min(xs), min(ys), max(xs), max(ys))

    @property
    def center(self) -> tuple[float, float]:
        return (self.x_min + self.x_max) / 2, (self.y_min + self.y_max) / 2


@dataclass(frozen=True, slots=True)
class _PlacedView:
    item: Any
    vertices: tuple[tuple[float, float], ...]
    projection_center: tuple[float, float]

    @classmethod
    def of(cls, item: Any, source: Any) -> Self:
        vertices = []
        index = 0
        while True:
            try:
                point = item.getVertexByIndex(index).Point
            except (IndexError, ValueError, RuntimeError):
                break
            vertices.append((point.x, point.y))
            index += 1
        projected = [item.projectPoint(vertex.Point) for vertex in source.Shape.Vertexes]
        center = _Bounds.around([(p.x, p.y) for p in projected]).center
        return cls(item, tuple(vertices), center)

    @property
    def bounds(self) -> _Bounds:
        return _Bounds.around(self.vertices)

    def vertex_at(self, point: Sequence[float]) -> int:
        projected = self.item.projectPoint(App.Vector(*point))
        x = projected.x - self.projection_center[0]
        y = projected.y - self.projection_center[1]
        index, distance = min(
            (
                (i, ((vx - x) ** 2 + (vy - y) ** 2) ** 0.5)
                for i, (vx, vy) in enumerate(self.vertices)
            ),
            key=lambda pair: pair[1],
        )
        if distance > _TOLERANCE:
            raise RuntimeError(
                f"{self.item.Type} view has no visible vertex at {tuple(point)} "
                f"(nearest is {distance:.4f} mm away)"
            )
        return index


def _projection_name(direction: Sequence[float]) -> str:
    names = {(0, -1, 0): "Front", (0, 0, 1): "Top", (-1, 0, 0): "Left", (1, 0, 0): "Right"}
    key = tuple(round(component) for component in direction)
    if key not in names:
        raise RuntimeError(f"no third-angle projection looks along {tuple(direction)}")
    return names[key]


def _is_close(actual: Any, expected: Sequence[float]) -> bool:
    distance: float = (actual - App.Vector(*expected)).Length
    return distance < _TOLERANCE


def _add_page(doc: Any, spec: dict[str, Any]) -> Any:
    template = doc.addObject("TechDraw::DrawSVGTemplate", "Template")
    template.Template = str(
        Path(App.getResourceDir()) / "Mod/TechDraw/Templates/ISO/A3_Landscape_ISO5457_minimal.svg"
    )
    texts = dict.fromkeys(template.EditableTexts, "")
    texts.update(
        title=spec["title"],
        drawing_number=spec["source_label"],
        scale="1 : 1",
        date_of_issue=datetime.date.today().isoformat(),
        sheet_number="1 / 1",
    )
    template.EditableTexts = texts
    page = doc.addObject("TechDraw::DrawPage", "Page")
    page.Template = template
    return page


def _add_views(doc: Any, page: Any, source: Any, spec: dict[str, Any]) -> dict[str, _PlacedView]:
    views = {view["name"]: view for view in spec["views"]}
    group = doc.addObject("TechDraw::DrawProjGroup", "Views")
    page.addView(group)
    group.Source = [source]
    group.ProjectionType = "Third angle"
    group.ScaleType = "Custom"
    group.Scale = 1.0
    group.AutoDistribute = True
    group.spacingX = 30
    group.spacingY = 30
    group.addProjection("Front")
    group.Anchor.Direction = App.Vector(*views["front"]["direction"])
    group.Anchor.XDirection = App.Vector(*views["front"]["x_direction"])
    items = {"front": group.Anchor}
    for name, view in views.items():
        if name != "front":
            items[name] = group.addProjection(_projection_name(view["direction"]))
    doc.recompute()

    for name, item in items.items():
        view = views[name]
        if not (
            _is_close(item.Direction, view["direction"])
            and _is_close(item.XDirection, view["x_direction"])
        ):
            raise RuntimeError(
                f"{name} view is oriented {item.Direction}, {item.XDirection}; "
                f"expected {view['direction']}, {view['x_direction']}"
            )
    placed = {name: _PlacedView.of(item, source) for name, item in items.items()}
    _center_on_page(group, page, placed)
    return placed


def _center_on_page(group: Any, page: Any, placed: dict[str, _PlacedView]) -> None:
    title_block_height = 60.0
    margin = 15.0
    corners = []
    for view in placed.values():
        bounds = view.bounds
        corners += [
            (view.item.X.Value + bounds.x_min, view.item.Y.Value + bounds.y_min),
            (view.item.X.Value + bounds.x_max, view.item.Y.Value + bounds.y_max),
        ]
    block = _Bounds.around(corners)
    width = page.Template.Width.Value
    height = page.Template.Height.Value
    block_x, block_y = block.center
    group.X = width / 2 - block_x
    group.Y = (title_block_height + height - margin) / 2 - block_y
    if (
        group.X.Value + block.x_min < margin
        or group.X.Value + block.x_max > width - margin
        or group.Y.Value + block.y_min < title_block_height
        or group.Y.Value + block.y_max > height - margin
    ):
        raise RuntimeError("views do not fit on the A3 page at 1:1")


def _add_dimensions(
    doc: Any, page: Any, spec: dict[str, Any], views: dict[str, _PlacedView]
) -> list[tuple[Any, dict[str, Any]]]:
    first_offset = 8.0
    step = 7.0
    stacked: dict[tuple[str, str], int] = {}
    added = []
    for entry in spec["dimensions"]:
        view = views[entry["view"]]
        start = view.vertex_at(entry["start"])
        end = view.vertex_at(entry["end"])
        dimension = doc.addObject("TechDraw::DrawViewDimension", entry["name"])
        dimension.Type = _DIMENSION_TYPES[entry["kind"]]
        dimension.References2D = [(view.item, (f"Vertex{start}", f"Vertex{end}"))]
        page.addView(dimension)

        bounds = view.bounds
        (sx, sy), (ex, ey) = view.vertices[start], view.vertices[end]
        mid_x, mid_y = (sx + ex) / 2, (sy + ey) / 2
        runs_horizontally = {"horizontal": True, "vertical": False}.get(
            entry["kind"], abs(ex - sx) >= abs(ey - sy)
        )
        if runs_horizontally:
            side = "above" if mid_y >= bounds.center[1] else "below"
        else:
            side = "right" if mid_x >= bounds.center[0] else "left"
        level = stacked.get((entry["view"], side), 0)
        stacked[(entry["view"], side)] = level + 1
        offset = first_offset + step * level
        dimension.X = {"right": bounds.x_max + offset, "left": bounds.x_min - offset}.get(
            side, mid_x
        )
        dimension.Y = {"above": bounds.y_max + offset, "below": bounds.y_min - offset}.get(
            side, mid_y
        )
        added.append((dimension, entry))
    return added


def _check_dimensions(added: list[tuple[Any, dict[str, Any]]]) -> None:
    mismatches = []
    for dimension, entry in added:
        measured = dimension.getRawValue()
        print(f"  {entry['name']}: {measured:.3f} mm (expected {entry['expected_mm']:.3f})")
        if abs(measured - entry["expected_mm"]) > _TOLERANCE:
            mismatches.append(entry["name"])
    if mismatches:
        raise RuntimeError(f"dimensions differ from the specification: {', '.join(mismatches)}")


def render_drawing(spec_path: Path) -> Path:
    """Render the drawing of one specification and return the saved ``.FCStd`` path."""
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    stem = spec_path.stem
    out_path = spec_path.with_suffix(".FCStd")
    out_path.unlink(missing_ok=True)
    doc = App.newDocument(stem.replace("-", "_"))
    try:
        Import.insert(str(spec_path.parent / spec["step"]), doc.Name)
        (source,) = doc.getObjectsByLabel(spec["source_label"])
        page = _add_page(doc, spec)
        views = _add_views(doc, page, source, spec)
        added = _add_dimensions(doc, page, spec, views)
        doc.recompute()
        print(f"{stem}:")
        _check_dimensions(added)
        doc.saveAs(str(out_path))
    finally:
        App.closeDocument(doc.Name)
    return out_path


def main() -> None:
    export_dir = Path(os.environ["TSUGU65_EXPORT_DIR"])
    spec_paths = sorted(export_dir.glob("*-drawing.json"))
    if not spec_paths:
        raise RuntimeError(f"no *-drawing.json in {export_dir}")
    for spec_path in spec_paths:
        print(f"wrote {render_drawing(spec_path)}")


if __name__ == "__main__":
    main()
