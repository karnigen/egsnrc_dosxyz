import importlib
from pathlib import Path


def test_dcm2egs_3ddose_full_accepts_path_bases(tmp_path, monkeypatch):
    module = importlib.import_module("egsnrc_dosxyz.dcm2egs_3ddose")
    calls = []

    def capture_transform(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(module, "dcm2egs_3ddose", capture_transform)
    dose_base = tmp_path / "dose"
    phantom_base = tmp_path / "phantom"

    module.dcm2egs_3ddose_full(
        dose_base,
        fnphant_base=phantom_base,
        postfix="_rotated",
        overwrite=True,
    )

    args, kwargs = calls[0]
    assert args == (
        Path(f"{dose_base}.3ddose"),
        Path(f"{phantom_base}.egsphant"),
        Path(f"{dose_base}_rotated.3ddose"),
        Path(f"{phantom_base}_rotated.egsphant"),
    )
    assert kwargs == {"overwrite": True}