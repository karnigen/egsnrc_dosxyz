#!/usr/bin/env uvr

import argparse
from pathlib import Path

from pyevtk.hl import gridToVTK

from egsnrc_dosxyz.egs3ddose import Egs3dDose

# convert .3ddose to rectilinear vtk
# - in paraview first use filter CellData2PointData

def dose3d2vtr(fn_base, overwrite=False):
    fn_base = Path(fn_base)
    fn_3ddose_in = Path(f"{fn_base}.3ddose")
    fn_vtr_out = Path(f"{fn_base}.vtr")
    if fn_vtr_out.exists() and not overwrite:
        raise FileExistsError(fn_vtr_out)

    dose = Egs3dDose().read_3ddose(fn_3ddose_in)
    cell_data = {
        "dose": dose.dose.flatten(),  # data already in F order, must be flatten
    }
    gridToVTK(str(fn_base), x=dose.bx, y=dose.by, z=dose.bz, cellData=cell_data)



def main():
    parser = argparse.ArgumentParser(description="Convert a 3ddose file to VTK rectilinear format.")
    parser.add_argument("base", type=Path, help="input filename without extension")
    parser.add_argument("--overwrite", action="store_true", help="replace an existing VTR file")
    args = parser.parse_args()

    dose3d2vtr(args.base, overwrite=args.overwrite)


if __name__ == "__main__":
    main()