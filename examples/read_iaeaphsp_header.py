import argparse
from pathlib import Path

from egsnrc_dosxyz.iaeaphsp_header import read_iaeaphsp_header


DEFAULT_HEADER = Path(__file__).parent / "data" / "iaeaphsp" / "ex1.IAEAheader"


def main():
    parser = argparse.ArgumentParser(description="Display selected IAEA header fields.")
    parser.add_argument("header", nargs="?", type=Path, default=DEFAULT_HEADER)
    args = parser.parse_args()

    header = read_iaeaphsp_header(args.header)
    for field in ("TITLE", "RECORD_LENGTH", "PARTICLES", "ORIG_HISTORIES"):
        print(f"{field}: {header[field][0][0]}")


if __name__ == "__main__":
    main()