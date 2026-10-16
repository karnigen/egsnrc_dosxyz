#!/usr/bin/env uvr

from pathlib import Path

import numpy as np

# default ramp
#    medium                  (CTmax-CTmin)/(max density - min density)
#    ------                  --------------------------------------
# 1 AIR700ICRU                       (-974 - -1024)/(0.044-0.001)
# 2 LUNG700ICRU                      (-724 - -974)/(0.302-0.044)
# 3 ICRUTISSUE700ICRU                (101 - -724)/(1.101-0.302)
# 4 ICRPBONE700ICRU                  (1976 - 101)/(2.088-1.101)

class EgsRamp:
    """Map density values to material indices using density thresholds."""

    def __init__(self, mats=None, bounds=None):
        if mats is None:
            self.mats = ["AIR700ICRU", "LUNG700ICRU", "ICRUTISSUE700ICRU", "ICRPBONE700ICRU"]
        else:
            self.mats = mats
        if bounds is None:
            self.bounds = np.array([0.001, 0.044, 0.302, 1.101], dtype="f8")
        else:
            self.bounds = np.array(bounds, dtype="f8")

    def chunk(self, density):
        """Return material indices; index 0 is the implicit vacuum medium."""
        return np.searchsorted(self.bounds, density, side="right")


class EgsPhant:
    """Read, write, and create EGSnrc phantom grids.

    Voxel arrays use (z, y, x) axis order. Material index 0 represents vacuum;
    the material names in ``mats`` correspond to indices starting at 1.
    """

    def __init__(self):
        self.estepes = None  # Replaced with zeros when writing a phantom file.

    def mat2ascii(self, mat_index):
        """Encode a numeric material index as the character used in .egsphant files."""
        mat_ascii = chr(  ((mat_index + 16) % 95)   + 32 )
        return mat_ascii

    def ascii2mat(self, mat_ascii):
        """Decode a .egsphant material character to its numeric index."""
        mat_index = ( ord(mat_ascii) + 47 ) % 95
        return mat_index

    def create_phantom(self, ramp, origin, spacing, pixels):
        """Create a phantom from density voxels, an origin, and voxel spacing.

        ``origin`` is the center of the first voxel. ``pixels`` is a density
        array with shape (z, y, x); ``ramp`` maps densities to material indices.
        """
        self.mats = ramp.mats
        self.nmat = len(self.mats)

        self.nz,self.ny,self.nx =list(pixels.shape)  # F array zyx
        size = [self.nx,self.ny,self.nz]   # xyz

        # Place each boundary half a voxel before the voxel-center origin.
        b=[0] * 3           # allocate
        for i in range(3):
            b[i]  = np.linspace(origin[i] , origin[i]+size[i]*spacing[i], num=size[i]+1, endpoint=True)
            b[i] -= spacing[i]/2     # move bound by half of size, origin is in center of first voxel
        self.bx, self.by, self.bz = b

        self.media = np.array(ramp.chunk(pixels), dtype='B')
        self.densities = pixels



    def read_egsphant(self, fn_phant_in):
        """Read a .egsphant file into this object.

        Args:
            fn_phant_in: Input .egsphant filename or path.

        Returns:
            This phantom object, for method chaining.
        """
        fn_phant_in = Path(fn_phant_in)
        with fn_phant_in.open("r") as fi:
            self.nmat = int(fi.readline().strip())  # number of media in phantom

            self.mats = [0] * self.nmat                  # allocation of array for media
            for i in range(self.nmat):                   # read media
                self.mats[i] = fi.readline().strip()

            self.estepes = [float(x) for x in fi.readline().strip().split()]  # ESTEPE values, reset to zero on write.
            self.estepes = np.array(self.estepes, dtype="f4")

            self.nx, self.ny, self.nz = [int(x) for x in fi.readline().strip().split()]     # voxel count in x,y,z

            self.bx = [float(x) for x in fi.readline().strip().split()]   # x bounds (count nvoxx+1)
            self.bx = np.array(self.bx, dtype="f4")

            self.by = [float(x) for x in fi.readline().strip().split()]   # y bounds (count nvoxy+1)
            self.by = np.array(self.by, dtype="f4")

            self.bz = [float(x) for x in fi.readline().strip().split()]   # z bounds (count nvoxz+1)
            self.bz = np.array(self.bz, dtype="f4")

            # Material indices are stored as remapped ASCII characters.
            self.media=np.zeros((self.nz, self.ny, self.nx), dtype='B') # allocate array for media
            for iz in range(self.nz):
                for iy in range(self.ny):
                    line=fi.readline().strip()
                    row = np.fromiter(map(self.ascii2mat, line), dtype="B")
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
        """Write this phantom object in .egsphant format.

        Args:
            fn_phant_out: Output .egsphant filename or path.
            overwrite: Whether to replace an existing file. Defaults to False.

        Returns:
            This phantom object, for method chaining.
        """
        self.estepes = [0] * self.nmat

        fn_phant_out = Path(fn_phant_out)
        if not overwrite and fn_phant_out.exists():
            raise FileExistsError(fn_phant_out)

        with fn_phant_out.open("w") as fo:
            fo.write(f"{self.nmat}\n")         # count of media

            for i in range(self.nmat):         # media names
                fo.write(f"{self.mats[i]}\n")

            for i in range(self.nmat):         # estepes - dummy
                fo.write(f"{self.estepes[i]:.1f} ")
            fo.write("\n")

            fo.write(f"{self.nx} {self.ny} {self.nz}\n")  # voxel count

            for i in range(self.nx+1):         # x bounds
                fo.write(f"{self.bx[i]:.4f} ")
            fo.write("\n")

            for i in range(self.ny+1):         # y bounds
                fo.write(f"{self.by[i]:.4f} ")
            fo.write("\n")

            for i in range(self.nz+1):         # z bounds
                fo.write(f"{self.bz[i]:.4f} ")
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
                        fo.write(f" {row[ix]:.6f}")
                    fo.write("\n")
                fo.write("\n")  # one empty line

        return self

