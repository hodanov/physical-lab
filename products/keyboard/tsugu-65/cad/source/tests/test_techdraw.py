"""Tests for the tsugu65-drawings entry point."""

import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from tsugu65 import techdraw


@pytest.fixture
def no_freecad(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("FREECADCMD", raising=False)
    monkeypatch.setattr(shutil, "which", lambda _name: None)
    monkeypatch.setattr(techdraw, "_MACOS_FREECADCMD", tmp_path / "missing" / "freecadcmd")


@pytest.fixture
def export_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "export"
    directory.mkdir()
    (directory / "tsugu65-left-drawing.json").write_text("{}", encoding="utf-8")
    return directory


@pytest.mark.usefixtures("no_freecad")
def test_find_freecadcmd_prefers_environment_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FREECADCMD", "/custom/freecadcmd")
    monkeypatch.setattr(shutil, "which", lambda _name: "/usr/bin/freecadcmd")

    assert techdraw.find_freecadcmd() == Path("/custom/freecadcmd")


@pytest.mark.usefixtures("no_freecad")
def test_find_freecadcmd_searches_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda _name: "/usr/bin/freecadcmd")

    assert techdraw.find_freecadcmd() == Path("/usr/bin/freecadcmd")


@pytest.mark.usefixtures("no_freecad")
def test_find_freecadcmd_falls_back_to_macos_bundle(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    assert techdraw.find_freecadcmd() is None

    bundled = tmp_path / "freecadcmd"
    bundled.touch()
    monkeypatch.setattr(techdraw, "_MACOS_FREECADCMD", bundled)

    assert techdraw.find_freecadcmd() == bundled


def test_main_requires_drawing_specs(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert techdraw.main(["--export-dir", str(tmp_path)]) == 1
    assert "tsugu65-build" in capsys.readouterr().err


@pytest.mark.usefixtures("no_freecad")
def test_main_reports_missing_freecad(export_dir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert techdraw.main(["--export-dir", str(export_dir)]) == 1
    assert "FREECADCMD" in capsys.readouterr().err


@pytest.mark.parametrize("returncode", [0, 3])
def test_main_runs_renderer_in_freecadcmd(
    monkeypatch: pytest.MonkeyPatch, export_dir: Path, returncode: int
) -> None:
    monkeypatch.setenv("FREECADCMD", "/custom/freecadcmd")
    calls: list[dict[str, Any]] = []

    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append({"command": command, **kwargs})
        return subprocess.CompletedProcess(command, returncode)

    monkeypatch.setattr(subprocess, "run", run)

    assert techdraw.main(["--export-dir", str(export_dir)]) == returncode

    (call,) = calls
    executable, flag, bootstrap = call["command"]
    assert (executable, flag) == ("/custom/freecadcmd", "-c")
    assert "runpy.run_path(" in bootstrap
    script = Path(bootstrap.split("run_path(")[1].split(",")[0].strip("'\""))
    assert script.name == "make_drawings.py"
    assert script.is_file()
    assert call["env"]["TSUGU65_EXPORT_DIR"] == str(export_dir.resolve())
