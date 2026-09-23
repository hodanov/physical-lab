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

ROW_COUNT = 5

type Level = Literal["full", "top", "bottom"]


class Half(StrEnum):
    LEFT = "left"
    RIGHT = "right"


@dataclass(frozen=True, slots=True)
class _Slot:
    name: str
    width_u: float = 1.0
    # Half-height keys occupy the top or bottom half of the row.
    level: Level = "full"
    # False stacks the next slot in the same column (Mac-style arrow cluster).
    advance: bool = True


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


def _keys(*names: str) -> list[_Slot]:
    return [_Slot(name) for name in names]


# Each row is (left-half slots, right-half slots), listed left to right.
_ROWS: tuple[tuple[list[_Slot], list[_Slot]], ...] = (
    (
        _keys("grave", "1", "2", "3", "4", "5", "6"),
        [*_keys("7", "8", "9", "0", "minus", "equal"), _Slot("delete", 2.0)],
    ),
    (
        [_Slot("tab", 1.5), *_keys("q", "w", "e", "r", "t")],
        [*_keys("y", "u", "i", "o", "p", "lbracket", "rbracket"), _Slot("backslash", 1.5)],
    ),
    (
        [_Slot("caps", 1.75), *_keys("a", "s", "d", "f", "g")],
        [*_keys("h", "j", "k", "l", "semicolon", "quote"), _Slot("return", 2.25)],
    ),
    (
        [_Slot("lshift", 2.25), *_keys("z", "x", "c", "v", "b")],
        [*_keys("n", "m", "comma", "period", "slash"), _Slot("rshift", 2.75)],
    ),
    (
        [*_keys("globe", "lctrl", "loption"), _Slot("lcommand", 1.25), _Slot("space_l", 2.75)],
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


def _build_keys() -> tuple[Key, ...]:
    keys: list[Key] = []
    for row, (left, right) in enumerate(_ROWS):
        row_bottom = ROW_COUNT - 1 - row
        x_u = 0.0
        for half, slots in ((Half.LEFT, left), (Half.RIGHT, right)):
            for slot in slots:
                y_u = row_bottom + (0.5 if slot.level == "top" else 0.0)
                height_u = 1.0 if slot.level == "full" else 0.5
                keys.append(Key(slot.name, half, row, x_u, y_u, slot.width_u, height_u))
                if slot.advance:
                    x_u += slot.width_u
    return tuple(keys)


KEYS: tuple[Key, ...] = _build_keys()


def keys_in(half: Half) -> tuple[Key, ...]:
    return tuple(key for key in KEYS if key.half is half)


def _origin_u(keys: Sequence[Key]) -> float:
    return min(key.x_u for key in keys)


def place(half: Half, params: Params) -> tuple[PlacedKey, ...]:
    """Return keycap positions in the half's local frame.

    The local origin is the front-left corner of the half's key area: the left edge
    of its leftmost key and the front edge of the bottom row.
    """
    keys = keys_in(half)
    origin_u = _origin_u(keys)
    pitch = params.key_pitch
    return tuple(
        PlacedKey(
            name=key.name,
            center_x=(key.x_u - origin_u + key.width_u / 2) * pitch,
            center_y=(key.y_u + key.height_u / 2) * pitch,
            cap_width=params.keycap_size(key.width_u),
            cap_depth=params.keycap_size(key.height_u),
        )
        for key in keys
    )


def extent(half: Half, params: Params) -> tuple[float, float]:
    """Return the (width, depth) of the half's key area, measured on key slots."""
    keys = keys_in(half)
    width_u = max(key.x_u + key.width_u for key in keys) - _origin_u(keys)
    return width_u * params.key_pitch, ROW_COUNT * params.key_pitch
