"""Render dimensioned TechDraw drawings of the exports in FreeCAD.

Runs ``drawings/make_drawings.py`` with FreeCAD's ``freecadcmd`` on the drawing
specifications written by ``tsugu65-build``, and saves ``tsugu65-<half>-drawing.FCStd``
next to the exports. The exit status is non-zero if any dimension does not match its
specification.
"""

import argparse
import os
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from tsugu65.build import default_export_dir

_MACOS_FREECADCMD = Path("/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd")


def find_freecadcmd() -> Path | None:
    """Return ``$FREECADCMD``, else ``freecadcmd`` on ``PATH``, else the macOS app's copy."""
    if configured := os.environ.get("FREECADCMD"):
        return Path(configured)
    if on_path := shutil.which("freecadcmd"):
        return Path(on_path)
    return _MACOS_FREECADCMD if _MACOS_FREECADCMD.is_file() else None


def main(argv: Sequence[str] | None = None) -> int:
    default_dir = default_export_dir()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--export-dir",
        type=Path,
        default=default_dir,
        help=f"directory with the tsugu65-build exports (default: {default_dir})",
    )
    args = parser.parse_args(argv)

    export_dir: Path = args.export_dir.resolve()
    if not any(export_dir.glob("*-drawing.json")):
        print(
            f"no drawing specifications in {export_dir}; run tsugu65-build first", file=sys.stderr
        )
        return 1
    freecadcmd = find_freecadcmd()
    if freecadcmd is None:
        print(
            "freecadcmd not found: install FreeCAD 1.1 or later, or set FREECADCMD", file=sys.stderr
        )
        return 1

    script = Path(__file__).resolve().parents[3] / "drawings" / "make_drawings.py"
    # freecadcmd exits 0 even when a script passed as a file argument raises; run it
    # through -c so failures reach the exit status.
    bootstrap = f"import runpy; runpy.run_path({str(script)!r}, run_name='__main__')"
    completed = subprocess.run(  # noqa: S603 -- runs the FreeCAD executable the user configured
        [str(freecadcmd), "-c", bootstrap],
        env={**os.environ, "TSUGU65_EXPORT_DIR": str(export_dir)},
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
