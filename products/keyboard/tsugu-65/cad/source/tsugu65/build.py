"""Generate TSUGU Split 65 manufacturing exports from the code-CAD source.

Exports are written to ``cad/export/`` by default and must not be edited by hand.
"""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

PRODUCT = "tsugu65"
DEFAULT_OUT_DIR = Path(__file__).resolve().parents[2] / "export"


def build_report() -> dict[str, Any]:
    """Return the inspection report for all generated parts."""
    return {"product": PRODUCT, "parts": []}


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
    report_path = out_dir / "report.json"
    report_path.write_text(json.dumps(build_report(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
