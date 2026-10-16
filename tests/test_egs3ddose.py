import numpy as np
import pytest

from egsnrc_dosxyz.egs3ddose import Egs3dDose


def test_3ddose_round_trip(tmp_path):
    original = Egs3dDose()
    original.nx, original.ny, original.nz = 2, 2, 1
    original.bx = np.array([0.0, 1.0, 2.0], dtype="f4")
    original.by = np.array([-1.0, 0.0, 1.0], dtype="f4")
    original.bz = np.array([4.0, 5.0], dtype="f4")
    original.dose = np.array([[[1.0, 2.0], [3.0, 4.0]]], dtype="f4")
    original.err = np.array([[[0.1, 0.2], [0.3, 0.4]]], dtype="f4")
    output = tmp_path / "roundtrip.3ddose"

    original.write_3ddose(output)
    result = Egs3dDose().read_3ddose(output)

    assert (result.nx, result.ny, result.nz) == (2, 2, 1)
    np.testing.assert_array_equal(result.bx, original.bx)
    np.testing.assert_array_equal(result.by, original.by)
    np.testing.assert_array_equal(result.bz, original.bz)
    np.testing.assert_allclose(result.dose, original.dose)
    np.testing.assert_allclose(result.err, original.err)


def test_write_3ddose_refuses_to_overwrite_by_default(tmp_path):
    output = tmp_path / "existing.3ddose"
    output.write_text("preserve this file")

    with pytest.raises(FileExistsError):
        Egs3dDose().write_3ddose(output)

    assert output.read_text() == "preserve this file"