"""Smoke tests that the code-CAD toolchain can build and export geometry."""

from pathlib import Path

from build123d import Box, export_step, export_stl, import_step


def test_box_round_trips_through_step(tmp_path: Path) -> None:
    box = Box(10, 20, 30)
    step_path = tmp_path / "box.step"

    assert export_step(box, step_path)

    imported = import_step(step_path)
    assert abs(imported.volume - 6000) < 1e-6


def test_box_exports_stl(tmp_path: Path) -> None:
    stl_path = tmp_path / "box.stl"

    assert export_stl(Box(10, 20, 30), stl_path)
    assert stl_path.stat().st_size > 0
