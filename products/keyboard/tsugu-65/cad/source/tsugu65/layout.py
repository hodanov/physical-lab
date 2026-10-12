"""Physical key layout of TSUGU Split 65.

Keys are defined on a standard 15u US ANSI grid and split between ``6/T/G/B`` and
``7/Y/H/N``, so each half keeps the conventional row stagger. Grid coordinates are in
key units (u): ``x_u`` grows to the right from the left edge of the row and ``y_u``
grows toward the back from the front edge of the bottom row.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

from tsugu65.params import Params

type _Level = Literal["full", "top", "bottom"]


class Half(StrEnum):
    LEFT = "left"
    RIGHT = "right"


@dataclass(frozen=True, slots=True)
class _Slot:
    name: str
    width_u: float = 1.0
    # Half-height keys occupy the top or bottom half of the row.
    level: _Level = "full"
    # False stacks the next slot in the same column (Mac-style arrow cluster).
    advance: bool = True

    @property
    def height_u(self) -> float:
        return 1.0 if self.level == "full" else 0.5

    @property
    def bottom_offset_u(self) -> float:
        return 1.0 - self.height_u if self.level == "top" else 0.0


@dataclass(frozen=True, slots=True)
class Key:
    name: str
    half: Half
    # 0 is the number row (back); 4 is the bottom row (front).
    row: int
    x_u: float
    y_u: float
    width_u: float
    height_u: float


@dataclass(frozen=True, slots=True)
class PlacedKey:
    """A keycap positioned in its half's local frame, in millimeters."""

    name: str
    center_x: float
    center_y: float
    cap_width: float
    cap_depth: float
    half_height: bool


@dataclass(frozen=True, slots=True)
class Rect:
    """An axis-aligned rectangle in a half's local frame."""

    x_min: float
    y_min: float
    x_max: float
    y_max: float

    def __post_init__(self) -> None:
        if self.x_min > self.x_max or self.y_min > self.y_max:
            raise ValueError(f"min must not exceed max: {self}")

    @property
    def width(self) -> float:
        return self.x_max - self.x_min

    @property
    def depth(self) -> float:
        return self.y_max - self.y_min


def _unit_slots(*names: str) -> list[_Slot]:
    return [_Slot(name) for name in names]


# Each row is (left-half slots, right-half slots), listed left to right.
_ROWS: tuple[tuple[list[_Slot], list[_Slot]], ...] = (
    (
        _unit_slots("grave", "1", "2", "3", "4", "5", "6"),
        [*_unit_slots("7", "8", "9", "0", "minus", "equal"), _Slot("delete", 2.0)],
    ),
    (
        [_Slot("tab", 1.5), *_unit_slots("q", "w", "e", "r", "t")],
        [*_unit_slots("y", "u", "i", "o", "p", "lbracket", "rbracket"), _Slot("backslash", 1.5)],
    ),
    (
        [_Slot("caps", 1.75), *_unit_slots("a", "s", "d", "f", "g")],
        [*_unit_slots("h", "j", "k", "l", "semicolon", "quote"), _Slot("return", 2.25)],
    ),
    (
        [_Slot("lshift", 2.25), *_unit_slots("z", "x", "c", "v", "b")],
        [*_unit_slots("n", "m", "comma", "period", "slash"), _Slot("rshift", 2.75)],
    ),
    (
        [
            *_unit_slots("globe", "lctrl", "loption"),
            _Slot("lcommand", 1.25),
            _Slot("space_l", 2.75),
        ],
        [
            _Slot("space_r", 2.75),
            _Slot("rcommand", 1.25),
            _Slot("roption"),
            _Slot("left", level="bottom"),
            _Slot("up", level="top", advance=False),
            _Slot("down", level="bottom"),
            _Slot("fn", level="top", advance=False),
            _Slot("right", level="bottom"),
        ],
    ),
)

_ROW_COUNT = len(_ROWS)


def _build_keys() -> tuple[Key, ...]:
    keys: list[Key] = []
    for row, (left, right) in enumerate(_ROWS):
        row_bottom = _ROW_COUNT - 1 - row
        x_u = 0.0
        for half, slots in ((Half.LEFT, left), (Half.RIGHT, right)):
            for slot in slots:
                y_u = row_bottom + slot.bottom_offset_u
                keys.append(Key(slot.name, half, row, x_u, y_u, slot.width_u, slot.height_u))
                if slot.advance:
                    x_u += slot.width_u
    return tuple(keys)


KEYS: tuple[Key, ...] = _build_keys()


def keys_in(half: Half) -> tuple[Key, ...]:
    return tuple(key for key in KEYS if key.half is half)


def stabilized_keys(half: Half) -> tuple[Key, ...]:
    """Return the keys of ``half`` wide enough to need a wire stabilizer to stay level."""
    stabilizer_min_width_u = 2.0
    return tuple(key for key in keys_in(half) if key.width_u >= stabilizer_min_width_u)


@dataclass(frozen=True, slots=True)
class HalfLayout:
    """The key layout of one half, sized by ``params``.

    Positions are in the half's local frame, in millimeters. The local origin is the
    front-left corner of the half's key area: the left edge of its leftmost key and the
    front edge of the bottom row.
    """

    half: Half
    params: Params

    def _origin_u(self) -> float:
        return min(key.x_u for key in keys_in(self.half))

    def placed_keys(self) -> tuple[PlacedKey, ...]:
        """Return keycap positions in the local frame."""
        origin_u = self._origin_u()
        pitch = self.params.key_pitch
        return tuple(
            PlacedKey(
                name=key.name,
                center_x=(key.x_u - origin_u + key.width_u / 2) * pitch,
                center_y=(key.y_u + key.height_u / 2) * pitch,
                cap_width=self.params.keycap_size(key.width_u),
                cap_depth=self.params.keycap_size(key.height_u),
                half_height=key.height_u < 1,
            )
            for key in keys_in(self.half)
        )

    def _bounds(self, keys: Sequence[Key]) -> Rect:
        origin_u = self._origin_u()
        pitch = self.params.key_pitch
        return Rect(
            x_min=(min(key.x_u for key in keys) - origin_u) * pitch,
            y_min=min(key.y_u for key in keys) * pitch,
            x_max=(max(key.x_u + key.width_u for key in keys) - origin_u) * pitch,
            y_max=max(key.y_u + key.height_u for key in keys) * pitch,
        )

    def row_spans(self) -> tuple[Rect, ...]:
        """Return each row's key area in the local frame, from the number row to the bottom row."""
        keys = keys_in(self.half)
        return tuple(
            self._bounds([key for key in keys if key.row == row]) for row in range(_ROW_COUNT)
        )

    def extent(self) -> tuple[float, float]:
        """Return the (width, depth) of the key area, measured on key slots."""
        bounds = self._bounds(keys_in(self.half))
        return bounds.width, bounds.depth
