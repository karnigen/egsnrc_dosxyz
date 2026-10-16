from pathlib import Path

from egsnrc_dosxyz.iaeaphsp_header import (
    read_iaeaphsp_header,
    write_iaeaphsp_header,
)


SAMPLE_HEADER = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "data"
    / "iaeaphsp"
    / "ex1.IAEAheader"
)


def test_read_iaeaphsp_header_sample():
    header = read_iaeaphsp_header(SAMPLE_HEADER)

    assert header["RECORD_LENGTH"][0][0] == "37"
    assert header["PARTICLES"][0][0] == "4175"


def test_iaeaphsp_header_round_trip(tmp_path):
    original = read_iaeaphsp_header(SAMPLE_HEADER)
    output = tmp_path / "roundtrip.IAEAheader"

    write_iaeaphsp_header(original, output)

    assert read_iaeaphsp_header(output) == original