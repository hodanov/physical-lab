"""Design parameters for TSUGU Split 65. All lengths are in millimeters.

Values marked ``TODO(donor)`` are placeholders until the donor keyboard's scissor
assemblies and keycaps are measured.
"""

from dataclasses import dataclass

# Conservative placeholder for PA12 minimum wall thickness. Check DMM.make's current
# guideline for the chosen process before ordering.
PA12_MIN_WALL = 1.0


@dataclass(frozen=True, slots=True)
class Params:
    # Center-to-center key spacing (1u).
    key_pitch: float = 19.05
    # Space between neighboring keycaps. TODO(donor)
    keycap_gap: float = 2.0
    # Plate opening that retains one 1u scissor assembly. TODO(donor)
    scissor_opening_width: float = 14.0
    scissor_opening_depth: float = 14.0
    # Plate opening depth for the half-height arrow and fn keys. TODO(donor)
    half_height_opening_depth: float = 6.0
    plate_thickness: float = 1.5
    # Gap between the plate edge and the case pocket, per side.
    plate_clearance: float = 0.3
    # Width of the case ledge that supports the plate from below.
    plate_ledge: float = 1.5
    wall_thickness: float = 2.0
    # Minimum floor thickness, found at the front edge.
    floor_thickness: float = 1.5
    # Space under the plate for the membrane, PCB, and battery.
    interior_depth: float = 5.0
    # Typing angle, rising toward the back edge.
    tilt_deg: float = 2.0
    # USB-C opening on the outer (left) side of the left half. Placeholder.
    usb_c_opening_width: float = 9.5
    usb_c_opening_height: float = 3.5
    usb_c_offset_from_back: float = 20.0
    # Inter-half cable opening on the back wall, measured from the inner end of the
    # number row. Placeholder.
    link_opening_width: float = 9.5
    link_opening_height: float = 3.5
    link_opening_inset: float = 16.0
    # Distance between the halves when shown side by side (preview only).
    split_gap: float = 38.1

    def __post_init__(self) -> None:
        for name, valid, requirement in self._constraints():
            if not valid:
                raise ValueError(f"{name} must {requirement}: {getattr(self, name)}")

    def _constraints(self) -> list[tuple[str, bool, str]]:
        """Return (field, satisfied, requirement) for each constraint, in check order."""
        pitch = self.key_pitch
        max_tilt_deg = 3.0
        constraints = [
            ("key_pitch", pitch > 0, "be positive"),
            (
                "keycap_gap",
                0 <= self.keycap_gap < pitch / 2,
                "leave room for a half-height keycap",
            ),
            (
                "half_height_opening_depth",
                0 < self.half_height_opening_depth < pitch / 2,
                "be within half a key pitch",
            ),
            ("plate_clearance", self.plate_clearance >= 0, "not be negative"),
            ("tilt_deg", 0 <= self.tilt_deg <= max_tilt_deg, f"be within 0-{max_tilt_deg}"),
            ("split_gap", self.split_gap >= 0, "not be negative"),
        ]
        constraints += [
            (name, 0 < getattr(self, name) < pitch, "be within one key pitch")
            for name in ("scissor_opening_width", "scissor_opening_depth")
        ]
        constraints += [
            (name, getattr(self, name) > 0, "be positive")
            for name in (
                "plate_thickness",
                "plate_ledge",
                "interior_depth",
                "usb_c_opening_width",
                "link_opening_width",
            )
        ]
        constraints += [
            (name, getattr(self, name) >= PA12_MIN_WALL, f"be at least {PA12_MIN_WALL} mm")
            for name in ("wall_thickness", "floor_thickness")
        ]
        constraints += [
            (name, 0 < getattr(self, name) <= self.interior_depth, "fit within interior_depth")
            for name in ("usb_c_opening_height", "link_opening_height")
        ]
        return constraints

    def keycap_size(self, units: float) -> float:
        """Return the keycap length for a key slot spanning ``units`` key pitches."""
        return units * self.key_pitch - self.keycap_gap

    @property
    def case_outer_offset(self) -> float:
        """Return the distance from the key-area outline to the case's outer surface."""
        return self.plate_clearance + self.wall_thickness
