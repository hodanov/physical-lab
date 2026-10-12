"""Generate TSUGU Split 65 manufacturing exports from the code-CAD source.

Exports are written to ``cad/export/`` by default and must not be edited by hand:

- ``tsugu65-<half>.step``: case and plate in assembled position (world frame)
- ``tsugu65-<half>-<part>.stl``: each part for 3D printing
- ``tsugu65-<half>-<view>.svg``: top, front, and outer-side projections for review
- ``report.json``: parameters and inspection results
"""

import argparse
import dataclasses
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from build123d import (
    Compound,
    ExportSVG,
    LineType,
    Part,
    Pos,
    Vector,
    export_step,
    export_stl,
)

from tsugu65 import plate
from tsugu65.assembly import HalfModel, build_half
from tsugu65.layout import Half
from tsugu65.params import Params

_PRODUCT = "tsugu65"


def _inspect_part(half: Half, name: str, part: Part) -> dict[str, Any]:
    bbox = part.bounding_box()
    return {
        "half": half.value,
        "part": name,
        "is_valid": part.is_valid,
        "volume_mm3": round(part.volume, 3),
        "bbox_mm": {
            "min": [round(v, 3) for v in bbox.min],
            "max": [round(v, 3) for v in bbox.max],
        },
    }


def _build_report(models: Sequence[HalfModel], params: Params) -> dict[str, Any]:
    return {
        "product": _PRODUCT,
        "params": dataclasses.asdict(params),
        "parts": [
            _inspect_part(model.layout.half, name, part)
            for model in models
            for name, part in (("case", model.case), ("plate", model.plate))
        ],
    }


def _view_orientations(half: Half) -> dict[str, tuple[Vector, Vector]]:
    outer_side = -1.0 if half is Half.LEFT else 1.0
    return {
        "top": (Vector(0, 0, 1), Vector(0, 1, 0)),
        "front": (Vector(0, -1, 0), Vector(0, 0, 1)),
        "side": (Vector(outer_side, 0, 0), Vector(0, 0, 1)),
    }


def _write_svg(shape: Compound, direction: Vector, up: Vector, path: Path) -> None:
    camera_distance = 1000.0
    center = shape.bounding_box().center()
    visible, hidden = shape.project_to_viewport(
        center + direction * camera_distance, up, look_at=center
    )

    exporter = ExportSVG(margin=5)
    exporter.add_layer("visible")
    exporter.add_layer("hidden", line_color=(160, 160, 160), line_type=LineType.ISO_DOT)
    exporter.add_shape(visible, layer="visible")
    exporter.add_shape(hidden, layer="hidden")
    exporter.write(path)


def _export_half(model: HalfModel, out_dir: Path) -> None:
    layout = model.layout
    stem = f"{_PRODUCT}-{layout.half.value}"
    model.case.label = "case"
    model.plate.label = "plate"
    assembly = Compound(label=stem, children=[model.case, model.plate])

    export_step(assembly, out_dir / f"{stem}.step")
    export_stl(model.case, out_dir / f"{stem}-case.stl")
    # Print the plate flat, bottom face down.
    flat_plate = Pos(0, 0, layout.params.plate_thickness) * plate.plate(layout)
    export_stl(flat_plate, out_dir / f"{stem}-plate.stl")

    for view, (direction, up) in _view_orientations(layout.half).items():
        _write_svg(assembly, direction, up, out_dir / f"{stem}-{view}.svg")


def main(argv: Sequence[str] | None = None) -> int:
    default_out_dir = Path(__file__).resolve().parents[2] / "export"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=default_out_dir,
        help=f"output directory (default: {default_out_dir})",
    )
    args = parser.parse_args(argv)

    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    params = Params()
    models = [build_half(half, params) for half in Half]
    for model in models:
        _export_half(model, out_dir)

    report_path = out_dir / "report.json"
    report_path.write_text(
        json.dumps(_build_report(models, params), indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote exports to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
