"""Tests for design parameters and their constraints."""

import pytest

from tsugu65.params import PA12_MIN_WALL, Params


def test_defaults_are_valid() -> None:
    params = Params()

    assert params.key_pitch == pytest.approx(19.05)
    assert 0 <= params.tilt_deg <= 3
    assert params.wall_thickness >= PA12_MIN_WALL


def test_keycap_size_follows_pitch_and_gap() -> None:
    params = Params(key_pitch=19.0, keycap_gap=2.5)

    assert params.keycap_size(1.0) == pytest.approx(16.5)
    assert params.keycap_size(2.25) == pytest.approx(2.25 * 19.0 - 2.5)
    assert params.keycap_size(0.5) == pytest.approx(9.5 - 2.5)


@pytest.mark.parametrize("tilt_deg", [-0.1, 3.1])
def test_rejects_tilt_outside_low_profile_range(tilt_deg: float) -> None:
    with pytest.raises(ValueError, match="tilt_deg"):
        Params(tilt_deg=tilt_deg)


def test_rejects_wall_thinner_than_pa12_minimum() -> None:
    with pytest.raises(ValueError, match="wall_thickness"):
        Params(wall_thickness=PA12_MIN_WALL - 0.1)


@pytest.mark.parametrize("key_pitch", [0.0, -19.05])
def test_rejects_non_positive_pitch(key_pitch: float) -> None:
    with pytest.raises(ValueError, match="key_pitch"):
        Params(key_pitch=key_pitch)


def test_rejects_gap_that_leaves_no_half_height_keycap() -> None:
    with pytest.raises(ValueError, match="keycap_gap"):
        Params(key_pitch=19.05, keycap_gap=19.05 / 2)


def test_rejects_scissor_opening_larger_than_pitch() -> None:
    with pytest.raises(ValueError, match="scissor_opening"):
        Params(scissor_opening_width=19.1)


def test_rejects_non_positive_plate_thickness() -> None:
    with pytest.raises(ValueError, match="plate_thickness"):
        Params(plate_thickness=0)


def test_rejects_floor_thinner_than_pa12_minimum() -> None:
    with pytest.raises(ValueError, match="floor_thickness"):
        Params(floor_thickness=PA12_MIN_WALL - 0.1)


def test_rejects_half_height_opening_deeper_than_half_pitch() -> None:
    with pytest.raises(ValueError, match="half_height_opening_depth"):
        Params(key_pitch=19.05, half_height_opening_depth=19.05 / 2)


@pytest.mark.parametrize("name", ["usb_c_opening_height", "link_opening_height"])
def test_rejects_side_opening_taller_than_interior(name: str) -> None:
    with pytest.raises(ValueError, match=name):
        Params(interior_depth=5.0, **{name: 5.1})


def test_rejects_negative_plate_clearance() -> None:
    with pytest.raises(ValueError, match="plate_clearance"):
        Params(plate_clearance=-0.1)
