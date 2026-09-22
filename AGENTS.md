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

- FreeCAD is the primary CAD tool.
- `.FCStd` is the source of truth.
- STEP is the primary neutral CAD exchange format.
- STL is a manufacturing/3D-print export format.
- Units are millimeters unless explicitly specified otherwise.

## AI workflow

AI agents may modify CAD source files and
associated scripts, but must preserve the design constraints
documented in each product's `AGENTS.md`.

## Architecture decisions

- Record repository-wide, long-lived decisions in `docs/adr/`.
- Record product-specific, long-lived decisions in each product's `docs/adr/`.
- Follow the ADR conventions in `docs/adr/README.md` when creating or replacing
  a decision.
