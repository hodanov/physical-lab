# alice-60

## Product

This is the first keyboard product in `physical-lab`: a 60% Alice-layout
keyboard.

## CAD

- Use FreeCAD for CAD work.
- Use millimeters for all dimensions.
- `cad/source/` contains the editable CAD source of truth (`.FCStd`).
- `cad/export/` contains generated manufacturing exports; do not edit them by
  hand.
- STEP is the neutral CAD master for manufacturing exchange.
- STL is the 3D-print export format.

## Initial design constraints

- 60% Alice layout
- MX-compatible switches
- Hot-swappable switches
- USB-C connectivity
- Tray-mounted case

## Manufacturing

- DMM.make is the initial manufacturing service.
- PA12 is the initial material candidate for prototypes.
- Check the selected material's current design guidelines, including minimum
  wall thickness and clearances, before exporting a manufacturing model.
- Keep manufacturing-service-specific files and notes in `manufacturing/`.

## Change workflow

When changing a physical design, update the source CAD model first, regenerate
the corresponding exports, and record design or manufacturing decisions in the
product documentation.

Record a product ADR in `docs/adr/` for a long-lived decision with meaningful
alternatives or consequences. Keep trial results, dimensions, quotes, and other
short-lived records in their relevant product documentation instead.
