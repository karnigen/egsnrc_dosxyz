import importlib
from pathlib import Path

import numpy as np
import pytest

from egsnrc_dosxyz.egs3ddose import Egs3dDose


def test_dose3d2vtr_accepts_path_and_honors_overwrite(tmp_path, monkeypatch):
    module = importlib.import_module("egsnrc_dosxyz.dose3d2vtr")
    base = tmp_path / "dose"
    dose = Egs3dDose()
    dose.nx, dose.ny, dose.nz = 2, 1, 1
    dose.bx = np.array([0.0, 1.0, 2.0], dtype="f4")
    dose.by = np.array([0.0, 1.0], dtype="f4")
    dose.bz = np.array([0.0, 1.0], dtype="f4")
    dose.dose = np.array([[[1.0, 2.0]]], dtype="f4")
    dose.err = np.array([[[0.1, 0.2]]], dtype="f4")
    dose.write_3ddose(Path(f"{base}.3ddose"))
    output = Path(f"{base}.vtr")
    output.touch()
    calls = []

    def capture_grid(path, **kwargs):
        calls.append((path, kwargs))

    monkeypatch.setattr(module, "gridToVTK", capture_grid)

    with pytest.raises(FileExistsError):
        module.dose3d2vtr(base)

    module.dose3d2vtr(base, overwrite=True)

    path, kwargs = calls[0]
    assert path == str(base)
    assert kwargs["cellData"]["dose"].tolist() == [1.0, 2.0]