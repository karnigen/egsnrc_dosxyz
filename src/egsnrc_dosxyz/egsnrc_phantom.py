#!/usr/bin/env python3

from pathlib import Path
import numpy as np

# - Usage:
#     egsphant = EgsPhant().read_egsphant(fn_phant_in)
#     egsphant.write_phantom(fn_phant_out)

# - egsphant format see pirs794 dosxyznrc, chapter 16.6
# - read write .egsphant file
# - memory layout of egsnrc is Fortran so axes of arrays are reversed here,
#   - media[z,y,x], densities[z,y,x]
#   - numpy only knows C memory layout, Fortran layout is always view
class EgsPhant:
    def __init__(self):
        pass

    def read_egsphant(self, fn_phant_in):
        fn_phant_in = Path(fn_phant_in)
        with fn_phant_in.open("r") as fi:
            self.nmat = int(fi.readline().strip())  # number of media in phantom

            self.mats = [0] * self.nmat                  # allocation of array for media
            for i in range(self.nmat):                   # read media
                self.mats[i] = fi.readline().strip()

            self.estepes = [float(x) for x in fi.readline().strip().split()]  # estepe for each media, not used set 0
            self.estepes = np.array(self.estepes, dtype="f4")

            self.nx, self.ny, self.nz = [int(x) for x in fi.readline().strip().split()]     # voxel count in x,y,z

            self.bx = [float(x) for x in fi.readline().strip().split()]   # x bounds (count nvoxx+1)
            self.bx = np.array(self.bx, dtype="f4")

            self.by = [float(x) for x in fi.readline().strip().split()]   # y bounds (count nvoxy+1)
            self.by = np.array(self.by, dtype="f4")

            self.bz = [float(x) for x in fi.readline().strip().split()]   # z bounds (count nvoxz+1)
            self.bz = np.array(self.bz, dtype="f4")

            # media index   1-9 A-Z  !!! whole ascii B - unsigned byte
            self.media=np.zeros((self.nz, self.ny, self.nx), dtype='B') # allocate array for media
            for iz in range(self.nz):
                for iy in range(self.ny):
                    line=fi.readline().strip()
                    row = np.fromiter(map(ord, line), dtype="B")
                    self.media[iz,iy,:]=row
                fi.readline()  # one empty line

            # reading densities
            self.densities=np.zeros((self.nz, self.ny, self.nx), dtype="f4") # allocate array for densities
            for iz in range(self.nz):
                for iy in range(self.ny):
                    row = np.array([float(x) for x in fi.readline().strip().split()], dtype="f4")
                    self.densities[iz,iy,:]=row
                fi.readline()  # one empty line
        return self

    def write_phantom(self, fn_phant_out):
        fn_phant_out = Path(fn_phant_out)
        if fn_phant_out.exists():
            print(f"File {fn_phant_out} already exists")
            exit(1)

        with fn_phant_out.open("w") as fo:
            fo.write(f"{self.nmat}\n")         # count of media

            for i in range(self.nmat):         # media names
                fo.write(f"{self.mats[i]}\n")

            for i in range(self.nmat):         # estepes - dummy
                fo.write("{:13.8f}    ".format(self.estepes[i]))
            fo.write("\n")

            fo.write(f"{self.nx:5d}{self.ny:5d}{self.nz:5d}\n")  # voxel count

            for i in range(self.nx+1):         # x bounds
                fo.write("{:13.8f}    ".format(self.bx[i]))
            fo.write("\n")

            for i in range(self.ny+1):         # y bounds
                fo.write("{:13.8f}    ".format(self.by[i]))
            fo.write("\n")

            for i in range(self.nz+1):         # z bounds
                fo.write("{:13.8f}    ".format(self.bz[i]))
            fo.write("\n")

            # write media indexes
            for iz in range(self.nz):
                for iy in range(self.ny):
                    row=self.media[iz,iy,:]
                    fo.write(row.tobytes().decode('ascii')+"\n")
                fo.write("\n")  # one empty line

            # writing densities
            for iz in range(self.nz):
                for iy in range(self.ny):
                    row=self.densities[iz,iy,:]
                    for ix in range(self.nx):
                        fo.write(" {:10.6f}".format(row[ix]))
                    fo.write("\n")
                fo.write("\n")  # one empty line
        
        return self

