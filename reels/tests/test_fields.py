"""
file: tests/test_fields.py
importable: nothing, pytest loads this file

description: Checks the readers of single edit file fields.
"""

import pytest

from reels.fields import Crop, CutError, centre, crop, number, record


def test_crop_keeps_nine_by_sixteen_with_a_pixel_of_rounding():
    assert crop("405:720:438:0", "here") == Crop(405, 720, 438, 0)
    with pytest.raises(CutError, match="not 9:16"):
        crop("400:400:0:0", "here")
    with pytest.raises(CutError, match="width:height:x:y"):
        crop("iw:ih", "here")


def test_number_names_the_field_and_its_range():
    assert number({"a": 2}, "a", "here", 0, 5) == 2.0
    assert number({}, "a", "here", 0, 5, 1) == 1.0
    with pytest.raises(CutError, match="here: missing a"):
        number({}, "a", "here", 0, 5)
    with pytest.raises(CutError, match="between 0 and 5"):
        number({"a": 9}, "a", "here", 0, 5)
    with pytest.raises(CutError, match="must be a number"):
        number({"a": True}, "a", "here", 0, 5)


def test_record_refuses_an_unknown_field():
    assert record(None, "here", {"a"}) == {}
    with pytest.raises(CutError, match="unknown field b"):
        record({"b": 1}, "here", {"a"})


def test_centre_takes_the_widest_nine_by_sixteen_window():
    assert centre(1920, 1080) == Crop(607, 1080, 656, 0)
    assert centre(1080, 2400) == Crop(1080, 1920, 0, 240)
