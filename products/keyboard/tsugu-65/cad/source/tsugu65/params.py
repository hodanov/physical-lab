"""Design parameters for TSUGU Split 65. All lengths are in millimeters.

Values marked ``TODO(donor)`` are placeholders until the donor keyboard's scissor
assemblies and keycaps are measured.
"""

from dataclasses import dataclass

# Conservative placeholder for PA12 minimum wall thickness. Check DMM.make's current
# guideline for the chosen process before ordering.
PA12_MIN_WALL = 1.0

MAX_TILT_DEG = 3.0


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
        if self.key_pitch <= 0:
            raise ValueError(f"key_pitch must be positive: {self.key_pitch}")
        if not 0 <= self.keycap_gap < self.key_pitch / 2:
            raise ValueError(
                f"keycap_gap must leave room for a half-height keycap: {self.keycap_gap}"
            )
        for name in ("scissor_opening_width", "scissor_opening_depth"):
            value = getattr(self, name)
            if not 0 < value < self.key_pitch:
                raise ValueError(f"{name} must be within one key pitch: {value}")
        if not 0 < self.half_height_opening_depth < self.key_pitch / 2:
            raise ValueError(
                "half_height_opening_depth must be within half a key pitch: "
                f"{self.half_height_opening_depth}"
            )
        for name in (
            "plate_thickness",
            "plate_ledge",
            "interior_depth",
            "usb_c_opening_width",
            "link_opening_width",
        ):
            value = getattr(self, name)
            if value <= 0:
                raise ValueError(f"{name} must be positive: {value}")
        if self.plate_clearance < 0:
            raise ValueError(f"plate_clearance must not be negative: {self.plate_clearance}")
        for name in ("wall_thickness", "floor_thickness"):
            value = getattr(self, name)
            if value < PA12_MIN_WALL:
                raise ValueError(f"{name} must be at least {PA12_MIN_WALL} mm: {value}")
        for name in ("usb_c_opening_height", "link_opening_height"):
            value = getattr(self, name)
            if not 0 < value <= self.interior_depth:
                raise ValueError(f"{name} must fit within interior_depth: {value}")
        if not 0 <= self.tilt_deg <= MAX_TILT_DEG:
            raise ValueError(f"tilt_deg must be within 0-{MAX_TILT_DEG}: {self.tilt_deg}")
        if self.split_gap < 0:
            raise ValueError(f"split_gap must not be negative: {self.split_gap}")

    def keycap_size(self, units: float) -> float:
        """Return the keycap length for a key slot spanning ``units`` key pitches."""
        return units * self.key_pitch - self.keycap_gap
