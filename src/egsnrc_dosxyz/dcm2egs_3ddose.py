#!/usr/bin/env uvr

import argparse
from pathlib import Path

import numpy as np

from egsnrc_dosxyz.egs3ddose import Egs3dDose
from egsnrc_dosxyz.egsphant import EgsPhant


def dcm2egs_3ddose(fn_3ddose_in, fn_phant_in, fn_3ddose_out, fn_phant_out,  overwrite = False):
    """Rotate matching dose and phantom grids from DICOM to DOSXYZ coordinates.

    Both voxel arrays are rotated 90 degrees around the x-axis, and their y/z
    boundaries are remapped to match the DOSXYZ_show coordinate convention.

    Args:
        fn_3ddose_in: Input .3ddose path.
        fn_phant_in: Input .egsphant path.
        fn_3ddose_out: Output .3ddose path.
        fn_phant_out: Output .egsphant path.
        overwrite: Whether to replace existing output files. Defaults to False.
    """
    dose = Egs3dDose().read_3ddose(fn_3ddose_in)   # .3ddose data
    phant = EgsPhant().read_egsphant(fn_phant_in)  # .egsphant data

    dose.ny, dose.nz = dose.nz, dose.ny
    dose.by, dose.bz = np.flip(-dose.bz), dose.by
    dose.dose = np.rot90(dose.dose, axes=(1,0))
    dose.err = np.rot90(dose.err, axes=(1,0))

    dose.write_3ddose(fn_3ddose_out, overwrite=overwrite)

    phant.ny, phant.nz = phant.nz, phant.ny
    phant.by, phant.bz = np.flip(-phant.bz), phant.by
    phant.media = np.rot90(phant.media, axes=(1,0))
    phant.densities = np.rot90(phant.densities, axes=(1,0))

    phant.write_phantom(fn_phant_out, overwrite=overwrite)


def dcm2egs_3ddose_full(fn3ddose_base, fnphant_base=None, postfix="_1", overwrite=False):
    """Build input/output filenames and convert the dose and phantom files.

    Args:
        fn3ddose_base: Input dose filename without its extension.
        fnphant_base: Input phantom filename without its extension. Defaults to fn3ddose_base.
        postfix: Suffix inserted before each output extension. Defaults to "_1".
        overwrite: Whether to replace existing output files. Defaults to False.
    """

    if fnphant_base is None:
        fnphant_base = fn3ddose_base

    fn_3ddose_in = Path(f"{fn3ddose_base}.3ddose")
    fn_phant_in = Path(f"{fnphant_base}.egsphant")

    fn_3ddose_out = Path(f"{fn3ddose_base}{postfix}.3ddose")
    fn_phant_out = Path(f"{fnphant_base}{postfix}.egsphant")

    dcm2egs_3ddose(
        fn_3ddose_in,
        fn_phant_in,
        fn_3ddose_out,
        fn_phant_out,
        overwrite=overwrite,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Convert a 3ddose file and phantom from DICOM to DOSXYZ coordinates."
    )
    parser.add_argument("dose_base", type=Path, help="dose filename without extension")
    parser.add_argument(
        "--phantom-base",
        type=Path,
        help="phantom filename without extension (defaults to dose_base)",
    )
    parser.add_argument("--postfix", default="_1", help="suffix added to output filenames")
    parser.add_argument("--overwrite", action="store_true", help="replace existing output files")
    args = parser.parse_args()

    dcm2egs_3ddose_full(
        args.dose_base,
        fnphant_base=args.phantom_base,
        postfix=args.postfix,
        overwrite=args.overwrite,
    )


if __name__ == "__main__":
    main()



