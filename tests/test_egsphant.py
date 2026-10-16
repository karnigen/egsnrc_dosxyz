import numpy as np
import pytest

from egsnrc_dosxyz.egsphant import EgsPhant, EgsRamp


def test_egsphant_round_trip(tmp_path):
    pixels = np.array([[[0.5, 1.0], [1.5, 2.0]]], dtype="f4")
    phantom = EgsPhant()
    phantom.create_phantom(
        EgsRamp(mats=["TEST"], bounds=[0.1]),
        origin=(0.0, 0.0, 0.0),
        spacing=(1.0, 1.0, 1.0),
        pixels=pixels,
    )
    output = tmp_path / "sample.egsphant"

    phantom.write_phantom(output)
    result = EgsPhant().read_egsphant(output)

    assert (result.nx, result.ny, result.nz) == (2, 2, 1)
    np.testing.assert_array_equal(result.media, phantom.media)
    np.testing.assert_array_equal(result.densities, phantom.densities)
    np.testing.assert_array_equal(result.bx, phantom.bx)
    np.testing.assert_array_equal(result.by, phantom.by)
    np.testing.assert_array_equal(result.bz, phantom.bz)


def test_write_phantom_refuses_to_overwrite_by_default(tmp_path):
    output = tmp_path / "existing.egsphant"
    output.write_text("preserve this file")
    phantom = EgsPhant()
    phantom.nmat = 1

    with pytest.raises(FileExistsError):
        phantom.write_phantom(output)

    assert output.read_text() == "preserve this file"