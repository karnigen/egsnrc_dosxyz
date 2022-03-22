#!/usr/bin/env python3

from pyevtk.hl import *
import numpy as np
from egsnrc_dosxyz import *

# convert .3ddose to rectilinear vtk
# - in paraview first use filter CellData2PointData

def dose3d2vtr(fn_base, overwrite = False):
    fn_3ddose_in = fn_base + ".3ddose"
    dose = Egs3dDose().read_3ddose(fn_3ddose_in)
    cellData = {
        "dose": dose.dose.flatten(),  # data already in F order, must be flatten
    }
    # extension .vtr
    gridToVTK(fn_base, x=dose.bx, y=dose.by, z=dose.bz, cellData=cellData)



if __name__ == "__main__":
    fn_base="ex1"
    dose3d2vtr(fn_base)