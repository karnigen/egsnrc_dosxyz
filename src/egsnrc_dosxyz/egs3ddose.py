#!/usr/bin/env uvr

from pathlib import Path

import numpy as np


# The .3ddose format is described in PIRS-794, DOSXYZnrc manual, chapter 12.
# Values are stored with x varying fastest; NumPy arrays use (z, y, x) axis order.
#
class Egs3dDose:
    """Read and write DOSXYZnrc .3ddose dose and uncertainty grids."""

    def __init__(self):
        pass

    def read_3ddose(self, fn_3ddose_in):
        """Read a .3ddose file into this object.

        Args:
            fn_3ddose_in: Input .3ddose filename or path.

        Returns:
            This dose object, for method chaining.
        """
        fn_3ddose_in = Path(fn_3ddose_in)
        with fn_3ddose_in.open("r") as fi:
            self.nx, self.ny, self.nz = [int(x) for x in fi.readline().strip().split()]         # voxel count
            self.bx = np.array([float(x) for x in fi.readline().strip().split()], dtype="f4")   # x bounds (count nx+1)
            self.by = np.array([float(x) for x in fi.readline().strip().split()], dtype="f4")   # y bounds (count ny+1)
            self.bz = np.array([float(x) for x in fi.readline().strip().split()], dtype="f4")   # z bounds (count nz+1)
            self.dose = np.array([float(x) for x in fi.readline().strip().split()], dtype='f4').reshape(self.nz, self.ny, self.nx) # nx*ny*nz
            self.err  = np.array([float(x) for x in fi.readline().strip().split()], dtype='f4').reshape(self.nz, self.ny, self.nx) # nx*ny*nz
        return self

    def write_3ddose(self, fn_3ddose_out, overwrite = False):
        """Write this dose object in .3ddose format.

        Args:
            fn_3ddose_out: Output .3ddose filename or path.
            overwrite: Whether to replace an existing file. Defaults to False.

        Returns:
            This dose object, for method chaining.
        """
        fn_3ddose_out = Path(fn_3ddose_out)
        if not overwrite and fn_3ddose_out.exists():
            raise FileExistsError(fn_3ddose_out)
        with fn_3ddose_out.open('w') as fo:
            fo.write(f"{self.nx}  {self.ny}  {self.nz}\n")

            # axes boundaries
            for boundary in self.bx.flat:
                fo.write(f"{boundary:.6f} ")
            fo.write("\n")
            for boundary in self.by.flat:
                fo.write(f"{boundary:.6f} ")
            fo.write("\n")
            for boundary in self.bz.flat:
                fo.write(f"{boundary:.6f} ")
            fo.write("\n")

            # values dose and error
            for value in self.dose.flat:
                fo.write(f"{value:.8g} ")
            fo.write("\n")
            for value in self.err.flat:
                fo.write(f"{value:.8g} ")
            fo.write("\n")
        return self
