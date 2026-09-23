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

PRODUCT = "tsugu65"
DEFAULT_OUT_DIR = Path(__file__).resolve().parents[2] / "export"

# Camera distance for SVG projections; far enough to be outside any part.
_VIEW_DISTANCE = 1000.0


def _inspect(half: Half, name: str, part: Part) -> dict[str, Any]:
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


def build_report(models: Sequence[HalfModel], params: Params) -> dict[str, Any]:
    """Return the inspection report for all generated parts."""
    return {
        "product": PRODUCT,
        "params": dataclasses.asdict(params),
        "parts": [
            _inspect(model.half, name, part)
            for model in models
            for name, part in (("case", model.case), ("plate", model.plate))
        ],
    }


def _write_svg(shape: Compound, view: str, outer_side: float, path: Path) -> None:
    center = shape.bounding_box().center()
    origin, up = {
        "top": (center + Vector(0, 0, _VIEW_DISTANCE), (0, 1, 0)),
        "front": (center + Vector(0, -_VIEW_DISTANCE, 0), (0, 0, 1)),
        "side": (center + Vector(outer_side * _VIEW_DISTANCE, 0, 0), (0, 0, 1)),
    }[view]
    visible, hidden = shape.project_to_viewport(origin, up, look_at=center)

    exporter = ExportSVG(margin=5)
    exporter.add_layer("visible")
    exporter.add_layer("hidden", line_color=(160, 160, 160), line_type=LineType.ISO_DOT)
    exporter.add_shape(visible, layer="visible")
    exporter.add_shape(hidden, layer="hidden")
    exporter.write(path)


def export_half(model: HalfModel, params: Params, out_dir: Path) -> None:
    stem = f"{PRODUCT}-{model.half.value}"
    model.case.label = "case"
    model.plate.label = "plate"
    assembly = Compound(label=stem, children=[model.case, model.plate])

    export_step(assembly, out_dir / f"{stem}.step")
    export_stl(model.case, out_dir / f"{stem}-case.stl")
    # Print the plate flat, bottom face down.
    flat_plate = Pos(0, 0, params.plate_thickness) * plate.plate(model.half, params)
    export_stl(flat_plate, out_dir / f"{stem}-plate.stl")

    outer_side = -1.0 if model.half is Half.LEFT else 1.0
    for view in ("top", "front", "side"):
        _write_svg(assembly, view, outer_side, out_dir / f"{stem}-{view}.svg")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help=f"output directory (default: {DEFAULT_OUT_DIR})",
    )
    args = parser.parse_args(argv)

    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    params = Params()
    models = [build_half(half, params) for half in Half]
    for model in models:
        export_half(model, params, out_dir)

    report_path = out_dir / "report.json"
    report_path.write_text(
        json.dumps(build_report(models, params), indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote exports to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
