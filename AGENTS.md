# AGENTS.md

## Repository

This repository is a monorepo for physical products
designed, prototyped, and manufactured by the owner.

## Structure

- `products/` — individual physical products
- `libraries/` — reusable CAD/electronics assets
- `tools/` — development and manufacturing tools
- `docs/` — general documentation

## Product structure

Each product should keep:

- CAD source files under `cad/source/`
- Manufacturing exports under `cad/export/`
- Technical drawings under `drawings/`
- BOM under `bom/`
- Manufacturing-specific files under `manufacturing/`

## CAD

- Model parts in Python with build123d. The parameters and modeling scripts
  under `cad/source/` are the source of truth (see `docs/adr/0003-*`).
- Use FreeCAD downstream for dimensioned drawings (TechDraw), assembly checks,
  and analysis. It imports the generated STEP files.
- STEP is the primary neutral CAD exchange format.
- STL is a manufacturing/3D-print export format.
- Generated exports under `cad/export/` are not committed; CI publishes them as
  artifacts.
- Units are millimeters unless explicitly specified otherwise.

## Python tooling

- Manage dependencies with uv (`pyproject.toml`, `uv.lock`). Python is pinned
  to 3.11.
- Format and lint with ruff, type-check with mypy (strict), test with pytest.
- Before finishing a change, run:

  ```sh
  uv run ruff format --check .
  uv run ruff check .
  uv run mypy
  uv run pytest
  ```

## AI workflow

AI agents may modify CAD source scripts and
associated tooling, but must preserve the design constraints
documented in each product's `AGENTS.md`.

## Architecture decisions

- Record repository-wide, long-lived decisions in `docs/adr/`.
- Record product-specific, long-lived decisions in each product's `docs/adr/`.
- Follow the ADR conventions in `docs/adr/README.md` when creating or replacing
  a decision.
