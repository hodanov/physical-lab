# TSUGU Split 65

## Product

This is the first keyboard product in `physical-lab`: a Mac-oriented,
low-profile split keyboard.

## CAD

- Use FreeCAD for CAD work.
- Use millimeters for all dimensions.
- `cad/source/` contains the editable CAD source of truth (`.FCStd`).
- `cad/export/` contains generated manufacturing exports; do not edit them by
  hand.
- STEP is the neutral CAD master for manufacturing exchange.
- STL is the 3D-print export format.

## Design constraints

- US ANSI 65%-class layout with no function-key row
- Split between `6/T/G/B` (left) and `7/Y/H/N` (right); retain conventional
  row stagger rather than an Alice or column-staggered layout
- 66 physical keys, including two independent space keys and an arrow cluster
- Place the layer `fn` key immediately to the right of the up-arrow key;
  map `fn` + `1` through `=` to F1 through F12
- Retain a Globe key for macOS input-source switching and use Mac modifier
  order and legends
- Use a membrane-and-scissor mechanism as the primary key technology to target
  a thin, quiet, MacBook Air-like typing experience
- USB-C host connection and Bluetooth multi-pairing for three hosts
- Wire the two halves together for inter-half data and power; the left half is
  the main unit and owns USB-C, Bluetooth, battery, antenna, and host switching
- Place the USB-C host port on the outer (left) side face of the left half,
  toward the back edge
- Keep the default typing angle between 0 and 3 degrees; do not make tenting a
  first-prototype requirement
- Use a non-metal enclosure by default to preserve Bluetooth performance

## Manufacturing

- DMM.make is the initial manufacturing service.
- PA12 is the initial material candidate for prototypes.
- A first prototype may reuse scissor assemblies, silicone domes, and keycaps
  from compatible donor keyboards. Production must use a stable, legitimate
  component supply before it is considered manufacturable.
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
