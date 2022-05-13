#!/usr/bin/env python3

from pathlib import Path
import numpy as np


# default ramp
#    medium                  (CTmax-CTmin)/(max density - min density)
#    ------                  --------------------------------------
# 1 AIR700ICRU                       (-974 - -1024)/(0.044-0.001)
# 2 LUNG700ICRU                      (-724 - -974)/(0.302-0.044)
# 3 ICRUTISSUE700ICRU                (101 - -724)/(1.101-0.302)
# 4 ICRPBONE700ICRU                  (1976 - 101)/(2.088-1.101)

# usage: 
# ramp = EgsRamp() or ramp = EgsRamp(mats=[mat1,...], bounds=[b1,...])
# print(ramp.mats)
# print(ramp.ramp([0.001,1, 3]))
class EgsRamp:
    # mats - list of media
    #      - first medium is always vacuum, cannot be changed
    # bound - same size as mats
    def __init__(self, mats=None, bounds=None):
        if mats is None:
            self.mats = ["AIR700ICRU", "LUNG700ICRU", "ICRUTISSUE700ICRU", "ICRPBONE700ICRU"]
        else:
            self.mats = mats
        if bounds is None:
            self.bounds = np.array([0.001, 0.044, 0.302, 1.101], dtype="f8")
        else:
            self.bounds = np.array(bounds, dtype="f8")

    # map density to media index
    # 0 - is vacuum, it is implicit, user media begins 1
    def chunk(self, density):
        return np.searchsorted(self.bounds, density, side="right")


# - Usage:
#     egsphant = EgsPhant().read_egsphant(fn_phant_in)
#     egsphant.write_phantom(fn_phant_out)
# - Variables:
#   - mats
#     nmat
#     estepes = None, not used on write is always replaced by [0] * nmat
#     nz,ny,nx - size z,y,x
#     bz,by,bx - boundaries of size nz+1,ny+1,nx+1
#     media[nz,ny,nx, dtype='B'] - media index, integer from 1 to 94, not ascii !!!
#     densities[nz,ny,nx, dtype='f4'] - mass densities !!! (not electron densities)

# - egsphant format see pirs794 dosxyznrc, chapter 16.6
# - read write .egsphant file
# - memory layout of .egsphant is Fortran, using axes order z,y,x for media[z,y,x], densities[z,y,x]
#   - numpy only knows C memory layout, Fortran layout is only view
class EgsPhant:
    def __init__(self):
        self.estepes = None    # not used anymore and set to [0] * nmat on write
        pass

    # - convert medium index 1-95 to ASCII code
    #     mat_index - 1-95
    #     return    - ASCII code
    # - original fortran code:
    #     (achar(MOD((med_index+16),95) + 32)  # see ctcreate
    def mat2ascii(self, mat_index):
        mat_ascii = chr(  ((mat_index + 16) % 95)   + 32 ) 
        return mat_ascii

    # - original fortran code:
    #     i = mod((iachar(mat_ascii) + 47), 95)   # see dosxyznrc
    def ascii2mat(self, mat_ascii):
        mat_index = ( ord(mat_ascii) + 47 ) % 95
        return mat_index


    # ramp - see EgsRamp
    # origin - (x,y,z) - center of first voxel in row data
    # spacing - (x,y,z)
    # pixel[z,y,x] - el.densities fortran array with reverse xyz!!!
    def create_phantom(self, ramp, origin, spacing, pixels):
        self.mats = ramp.mats
        self.nmat = len(self.mats)

        self.nz,self.ny,self.nx =list(pixels.shape)  # F array zyx
        size = [self.nx,self.ny,self.nz]   # xyz

        # setup boundaries
        b=[0] * 3           # allocate
        for i in range(3):
            b[i]  = np.linspace(origin[i] , origin[i]+size[i]*spacing[i], num=size[i]+1, endpoint=True)
            b[i] -= spacing[i]/2     # move bound by half of size, origin is in center of first voxel
        self.bx, self.by, self.bz = b

        self.media = np.array(ramp.chunk(pixels), dtype='B')
        self.densities = pixels



    def read_egsphant(self, fn_phant_in):
        """read .egsphant file

        Args:
            fn_phant_in (str): .egsphant input file

        Returns:
            EgsPhant: self
        """
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
                    # row = np.fromiter(map(ord, line), dtype="B")           # binary
                    row = np.fromiter(map(self.ascii2mat, line), dtype="B")  # remap ascii to number as egs "0"->0
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

    def write_phantom(self, fn_phant_out, overwrite = False):
        """write .egsphant file

        Args:
            fn_phant_out (str): .egsphant output file
            overwrite (bool, optional): overwrite output file. Defaults to False.

        Returns:
            EgsPhant: self
        """
        # '''
        #     fn_phant_out: [string,path] - output filename
        #     overwrite:    [bool]        - overwrite silently if file exists
        # '''
        self.estepes = [0] * self.nmat

        fn_phant_out = Path(fn_phant_out)
        if not overwrite and fn_phant_out.exists():
            print(f"File {fn_phant_out} already exists")
            exit(1)

        with fn_phant_out.open("w") as fo:
            fo.write(f"{self.nmat}\n")         # count of media

            for i in range(self.nmat):         # media names
                fo.write(f"{self.mats[i]}\n")

            for i in range(self.nmat):         # estepes - dummy
                fo.write("{:.1f} ".format(self.estepes[i]))
            fo.write("\n")

            fo.write(f"{self.nx} {self.ny} {self.nz}\n")  # voxel count

            for i in range(self.nx+1):         # x bounds
                fo.write("{:.4f} ".format(self.bx[i]))
            fo.write("\n")

            for i in range(self.ny+1):         # y bounds
                fo.write("{:.4f} ".format(self.by[i]))
            fo.write("\n")

            for i in range(self.nz+1):         # z bounds
                fo.write("{:.4f} ".format(self.bz[i]))
            fo.write("\n")

            # write media indexes
            for iz in range(self.nz):
                for iy in range(self.ny):
                    row=self.media[iz,iy,:]
                    # fo.write(row.tobytes().decode('ascii')+"\n")     # binary  0->"\0"
                    fo.write(''.join(map(self.mat2ascii, row)) + "\n") # remap int to ascii as egs 0->'0'
                fo.write("\n")  # one empty line

            # writing densities
            for iz in range(self.nz):
                for iy in range(self.ny):
                    row=self.densities[iz,iy,:]
                    for ix in range(self.nx):
                        fo.write(" {:.6f}".format(row[ix]))
                    fo.write("\n")
                fo.write("\n")  # one empty line
        
        return self

