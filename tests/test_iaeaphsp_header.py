import struct
from pathlib import Path

import pytest

from egsnrc_dosxyz.iaeaphsp_header import (
    IAEAparser,
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


def test_decode_record_normalizes_direction_cosines_above_unit_length():
    parser = IAEAparser()
    parser.setup_record(read_iaeaphsp_header(SAMPLE_HEADER))
    payload = struct.pack(
        parser.record_unpack,
        1,
        -1.0,
        0.0,
        0.0,
        1.0,
        1.0,
        1.0,
        0.0,
        0.0,
        0,
    )

    record = parser.decode_record(payload)

    assert record.u == pytest.approx(2**-0.5)
    assert record.v == pytest.approx(2**-0.5)
    assert record.w == 0.0