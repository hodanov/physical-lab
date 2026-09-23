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
    plate_thickness: float = 1.5
    wall_thickness: float = 2.0
    # Typing angle, rising toward the back edge.
    tilt_deg: float = 2.0
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
        if self.plate_thickness <= 0:
            raise ValueError(f"plate_thickness must be positive: {self.plate_thickness}")
        if self.wall_thickness < PA12_MIN_WALL:
            raise ValueError(
                f"wall_thickness must be at least {PA12_MIN_WALL} mm: {self.wall_thickness}"
            )
        if not 0 <= self.tilt_deg <= MAX_TILT_DEG:
            raise ValueError(f"tilt_deg must be within 0-{MAX_TILT_DEG}: {self.tilt_deg}")
        if self.split_gap < 0:
            raise ValueError(f"split_gap must not be negative: {self.split_gap}")

    def keycap_size(self, units: float) -> float:
        """Return the keycap length for a key slot spanning ``units`` key pitches."""
        return units * self.key_pitch - self.keycap_gap
