"""Tests for the physical key layout."""

import itertools

import pytest

from tsugu65.layout import KEYS, Half, Key, extent, keys_in, place, row_spans
from tsugu65.params import Params


def by_name(name: str) -> Key:
    return next(key for key in KEYS if key.name == name)


def row_names(half: Half, row: int) -> list[str]:
    return [key.name for key in sorted(keys_in(half), key=lambda k: k.x_u) if key.row == row]


def test_has_66_uniquely_named_keys() -> None:
    names = [key.name for key in KEYS]

    assert len(names) == 66
    assert len(set(names)) == 66


@pytest.mark.parametrize(
    ("left", "right"), [("6", "7"), ("t", "y"), ("g", "h"), ("b", "n"), ("space_l", "space_r")]
)
def test_splits_between_6tgb_and_7yhn(left: str, right: str) -> None:
    assert by_name(left).half is Half.LEFT
    assert by_name(right).half is Half.RIGHT


def test_each_row_spans_standard_15u_ansi_width() -> None:
    for row in range(5):
        row_keys = [key for key in KEYS if key.row == row]
        assert min(key.x_u for key in row_keys) == 0
        assert max(key.x_u + key.width_u for key in row_keys) == 15


@pytest.mark.parametrize(("name", "x_u"), [("1", 1.0), ("q", 1.5), ("a", 1.75), ("z", 2.25)])
def test_keeps_ansi_row_stagger(name: str, x_u: float) -> None:
    assert by_name(name).x_u == x_u


def test_bottom_row_uses_mac_modifier_order() -> None:
    assert row_names(Half.LEFT, 4) == ["globe", "lctrl", "loption", "lcommand", "space_l"]
    assert row_names(Half.RIGHT, 4)[:3] == ["space_r", "rcommand", "roption"]


def test_fn_is_immediately_right_of_up_arrow() -> None:
    up, fn = by_name("up"), by_name("fn")

    assert fn.x_u == up.x_u + up.width_u
    assert (fn.y_u, fn.height_u) == (up.y_u, up.height_u)


def test_arrow_cluster_is_mac_style_half_height() -> None:
    left, up, down, right = (by_name(n) for n in ("left", "up", "down", "right"))

    assert all(key.height_u == 0.5 for key in (left, up, down, right))
    assert up.x_u == down.x_u
    assert up.y_u == down.y_u + 0.5
    assert left.y_u == down.y_u == right.y_u
    assert left.x_u + 1 == down.x_u
    assert down.x_u + 1 == right.x_u


def test_key_slots_do_not_overlap() -> None:
    for a, b in itertools.combinations(KEYS, 2):
        overlap_x = min(a.x_u + a.width_u, b.x_u + b.width_u) - max(a.x_u, b.x_u)
        overlap_y = min(a.y_u + a.height_u, b.y_u + b.height_u) - max(a.y_u, b.y_u)
        assert overlap_x <= 0 or overlap_y <= 0, (a.name, b.name)


def test_place_uses_local_origin_per_half() -> None:
    params = Params(key_pitch=19.0, keycap_gap=2.0)

    q = next(p for p in place(Half.LEFT, params) if p.name == "q")
    assert (q.center_x, q.center_y) == pytest.approx((2.0 * 19.0, 3.5 * 19.0))
    assert (q.cap_width, q.cap_depth) == pytest.approx((17.0, 17.0))

    # The right half's origin is the left edge of its widest-reaching row (Y at 6.5u).
    y = next(p for p in place(Half.RIGHT, params) if p.name == "y")
    assert (y.center_x, y.center_y) == pytest.approx((0.5 * 19.0, 3.5 * 19.0))


def test_place_half_height_keys() -> None:
    params = Params(key_pitch=19.0, keycap_gap=2.0)

    up = next(p for p in place(Half.RIGHT, params) if p.name == "up")
    assert up.center_y == pytest.approx(0.75 * 19.0)
    assert (up.cap_width, up.cap_depth) == pytest.approx((17.0, 7.5))


def test_placed_keycaps_do_not_overlap() -> None:
    params = Params()
    for half in Half:
        for a, b in itertools.combinations(place(half, params), 2):
            dx = abs(a.center_x - b.center_x) - (a.cap_width + b.cap_width) / 2
            dy = abs(a.center_y - b.center_y) - (a.cap_depth + b.cap_depth) / 2
            assert dx > 0 or dy > 0, (a.name, b.name)


def test_extent_of_each_half() -> None:
    params = Params(key_pitch=19.0)

    assert extent(Half.LEFT, params) == pytest.approx((7.25 * 19.0, 5 * 19.0))
    assert extent(Half.RIGHT, params) == pytest.approx((8.5 * 19.0, 5 * 19.0))


def test_place_marks_half_height_keys() -> None:
    placed = {p.name: p for p in place(Half.RIGHT, Params())}

    assert all(placed[name].half_height for name in ("left", "up", "down", "fn", "right"))
    assert not placed["roption"].half_height


def test_row_spans_follow_row_stagger() -> None:
    pitch = 19.0
    spans = row_spans(Half.LEFT, Params(key_pitch=pitch))

    # Number row (back) spans 7u; the shift row (second from front) spans 7.25u.
    assert spans[0] == pytest.approx((0, 4 * pitch, 7 * pitch, 5 * pitch))
    assert spans[3] == pytest.approx((0, pitch, 7.25 * pitch, 2 * pitch))
    # The right half's rows start at their stagger offset from the local origin.
    assert row_spans(Half.RIGHT, Params(key_pitch=pitch))[0][0] == pytest.approx(0.5 * pitch)
