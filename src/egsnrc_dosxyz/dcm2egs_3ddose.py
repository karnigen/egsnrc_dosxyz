#!/usr/bin/env python3

from pathlib import Path
import numpy as np

from egsnrc_dosxyz import *

def dcm2egs_3ddose(fn_3ddose_in, fn_phant_in, fn_3ddose_out, fn_phant_out,  overwrite = False):
    """ - transform .3ddose and .egsphant from dicom coords to dosxyz coords (only for doswyz_show)
          - implemented as rotation by 90 deg around x axis
          - dosxyz_show requires also .egsphant matrix to be rotated
        - dosxyz and beam coords x:left->right y:from gantry z:up->down
          dicom coord            x:left->right y:up->down    z:to gantry


    Args:
        fn_3ddose_in (Path): input .3ddose
        fn_phant_in (Path): input .egsphant
        fn_3ddose_out (Path): output .3ddose
        fn_phant_out (Path): output .egsphant
        overwrite (bool, optional): overwrite output files. Defaults to False.
    """
    dose = Egs3dDose().read_3ddose(fn_3ddose_in)   # .3ddose data
    phant = EgsPhant().read_egsphant(fn_phant_in)  # .egsphant data

    dose.ny, dose.nz = dose.nz, dose.ny
    dose.by, dose.bz = np.flip(-dose.bz), dose.by
    dose.dose = np.rot90(dose.dose, axes=(1,0))
    dose.err = np.rot90(dose.err, axes=(1,0))

    dose.write_3ddose(fn_3ddose_out, overwrite)

    phant.ny, phant.nz = phant.nz, phant.ny
    phant.by, phant.bz = np.flip(-phant.bz), phant.by
    phant.media = np.rot90(phant.media, axes=(1,0))
    phant.densities = np.rot90(phant.densities, axes=(1,0))

    phant.write_phantom(fn_phant_out, overwrite)


def dcm2egs_3ddose_full(fn3ddose_base, fnphant_base=None, postfix="_1", overwrite=False):
    """prepare file names and call dcm2egs_3ddose(...)

    Args:
        fn3ddose_base (str): input file base of .3ddose (.egsphant)
        fnphant_base (str): input file base of .egsphant
        postfix (str, optional): string added to fbase_in creates output. Defaults to "_1".
        overwrite (bool, optional): overwrite output files. Defaults to False.
    """

    if fnphant_base is None:
        fnphant_base = fn3ddose_base

    fn_3ddose_in = Path(fn3ddose_base + ".3ddose")
    fn_phant_in = Path(fnphant_base + ".egsphant")

    fn_3ddose_out = Path(fn3ddose_base + postfix + ".3ddose")
    fn_phant_out = Path(fnphant_base + postfix + ".egsphant")

    dcm2egs_3ddose(fn_3ddose_in, fn_phant_in, fn_3ddose_out, fn_phant_out,  overwrite)


if __name__ == "__main__":
    dcm2egs_3ddose_full("ex1", overwrite=True)



