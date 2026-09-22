# alice-60

The first keyboard product in `physical-lab`: a 60% Alice-layout keyboard.

## Status

Specification and project structure are in place. CAD, electronics, firmware,
and manufacturing artifacts have not been created yet.

## Initial specification

- Layout: 60% Alice
- Switches: MX-compatible, hot-swappable
- Connectivity: USB-C
- Mounting: tray mount
- CAD: FreeCAD, in millimeters
- Prototype material candidate: PA12 via DMM.make

## Directory layout

- `cad/source/`: editable FreeCAD source files (`.FCStd`)
- `cad/export/`: generated STEP and STL manufacturing exports
- `drawings/`: dimensioned drawings and related documentation
- `pcb/`: PCB design files
- `firmware/`: keyboard firmware
- `bom/`: bill of materials
- `manufacturing/`: supplier-specific deliverables and production notes

## CAD artifact lifecycle

`cad/source/` is the design source of truth. Regenerate STEP and STL files in
`cad/export/` whenever the CAD model changes. Before ordering, validate the
export against the current design guidelines for the selected material and
manufacturer.
