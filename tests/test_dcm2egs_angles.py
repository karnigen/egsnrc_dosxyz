import pytest

from egsnrc_dosxyz.dcm2egs_angles import dcm2egs_angles


def test_zero_plan_angles_match_dosxyz_reference():
    assert dcm2egs_angles(gantry=0.0, couch=0.0, collimator=0.0) == pytest.approx(
        (90.0, 270.0, 270.0)
    )