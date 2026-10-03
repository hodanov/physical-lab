"""Tests for the tsugu65-build entry point."""

import json
from pathlib import Path

from build123d import import_step

from tsugu65.build import main

HALVES = ("left", "right")


def test_build_writes_exports_and_report(tmp_path: Path) -> None:
    out_dir = tmp_path / "export"

    assert main(["--out", str(out_dir)]) == 0

    for half in HALVES:
        assert import_step(out_dir / f"tsugu65-{half}.step").volume > 0
        for part in ("case", "plate"):
            assert (out_dir / f"tsugu65-{half}-{part}.stl").stat().st_size > 0
        for view in ("top", "front", "side"):
            svg = (out_dir / f"tsugu65-{half}-{view}.svg").read_text(encoding="utf-8")
            assert svg.startswith("<?xml") or svg.startswith("<svg")

    report = json.loads((out_dir / "report.json").read_text(encoding="utf-8"))
    assert report["product"] == "tsugu65"
    parts = {(part["half"], part["part"]): part for part in report["parts"]}
    assert set(parts) == {(half, part) for half in HALVES for part in ("case", "plate")}
    for part in parts.values():
        assert part["is_valid"]
        assert part["volume_mm3"] > 0
        assert len(part["bbox_mm"]["min"]) == len(part["bbox_mm"]["max"]) == 3
    assert report["params"]["tilt_deg"] == 2.0
