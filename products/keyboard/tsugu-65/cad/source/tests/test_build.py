"""Tests for the tsugu65-build entry point."""

import json
from pathlib import Path

from tsugu65.build import main


def test_build_writes_report(tmp_path: Path) -> None:
    out_dir = tmp_path / "export"

    assert main(["--out", str(out_dir)]) == 0

    report = json.loads((out_dir / "report.json").read_text(encoding="utf-8"))
    assert report["product"] == "tsugu65"
    assert report["parts"] == []
