import argparse
from pathlib import Path

from egsnrc_dosxyz.egs3ddose import Egs3dDose


def main():
    parser = argparse.ArgumentParser(description="Read and rewrite a 3ddose file.")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    dose = Egs3dDose().read_3ddose(args.input)
    dose.write_3ddose(args.output)
    print(f"Wrote {args.output} ({dose.nx} x {dose.ny} x {dose.nz} voxels)")


if __name__ == "__main__":
    main()