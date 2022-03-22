#!/usr/bin/env python3

from pathlib import Path
import numpy as np

# Usage:
#    dose3d = Egs3dDose().read_3ddose(fn_3ddose_in)
#    dose3d.write_3ddose(fn_3ddose_out)


# - 3ddose format see pirs794 dosxyznrc, chapter 12
# - read and write .3ddose files
# - memory layout of .3ddose is Fortran, using axes order z,y,x for dose[z,y,x], err[z,y,x]
#   - numpy only knows C memory layout and Fortran layout is only view
# 
class Egs3dDose:
    def __init__(self):
        pass

    # reading 3ddose format
    #    - only 6 lines !!!
    def read_3ddose(self, fn_3ddose_in):
        """read .3ddose file

        Args:
            fn_3ddose_in (str): .3ddose file name

        Returns:
            Egs3dDose: self
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
        """write .3ddose format file

        Args:
            fn_3ddose_out (str): .3ddose output file
            overwrite (bool, optional): overwrite output file. Defaults to False.

        Returns:
            Egs3dDose: self
        """
        fn_3ddose_out = Path(fn_3ddose_out)
        if not overwrite and fn_3ddose_out.exists():
            print(f"File {fn_3ddose_out} already exists")
            exit(1)
        with fn_3ddose_out.open('w') as fo:
            fo.write(f"{self.nx}  {self.ny}  {self.nz}\n")
            
            # axes boundaries
            for f in self.bx.flat:  fo.write(f"{f:.6f} ")
            fo.write("\n")
            for f in self.by.flat:  fo.write(f"{f:.6f} ")
            fo.write("\n")
            for f in self.bz.flat:  fo.write(f"{f:.6f} ")
            fo.write("\n")
            
            # values dose and error
            for f in self.dose.flat: fo.write(f"{f:.8g} ")
            fo.write("\n")
            for f in self.err.flat: fo.write(f"{f:.8g} ")
            fo.write("\n")
        return self
