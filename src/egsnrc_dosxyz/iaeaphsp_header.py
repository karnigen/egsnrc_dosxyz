#!/usr/bin/env uvr

import argparse
import shutil
import struct
import sys
from dataclasses import dataclass, field
from math import hypot
from pathlib import Path

import numpy as np

# IAEA phase-space format used by EGSnrc.
# =================================
# Header files contain named blocks such as ``$PARTICLES:``. This parser
# recognizes ``//`` comments and preserves each block's lines and comments.
#
# CHECKSUM = RECORD_LENGTH * PARTICLES.
#

# Particle-count fields handled when joining headers.
iaeaphsp_particles = ['PHOTONS','ELECTRONS','POSITRONS','NEUTRONS','PROTONS']



@dataclass
class IAEArecord:
    t:      int         = 0
    E:      float       = 0
    x:      float       = 0
    y:      float       = 0
    z:      float       = 0
    u:      float       = 0
    v:      float       = 0
    w:      float       = 0
    wt:     float       = 0
    xfloat: list[float] = field(default_factory=list)
    xlong:  list[int]   = field(default_factory=list)
    h:      int         = 0                             # history index 0 - new


class IAEAparser:
    def __init__(self):
        self.record_length=0

    def setup_record(self, PH):
        """Configure binary-record decoding from a parsed IAEA header."""
        # The first nine values describe required fields and extra-value counts.
        RECORD_CONTENTS = list( filter(str.strip,  PH['RECORD_CONTENTS'][0]) )  # skip empty lines
        RECORD_CONSTANT = list( filter(str.strip,  PH['RECORD_CONSTANT'][0]) )  # skip empty lines

        self.record_contents = np.array([ int(i) for i in RECORD_CONTENTS[0:9] ], dtype="i2") # take first 9 numbers
        self.nxfloat = self.record_contents[7]
        self.nxlong = self.record_contents[8]
        self.extrafloat_contents = np.array([int(i) for i in RECORD_CONTENTS[9:9+self.nxfloat]], dtype="i2")
        self.extralong_contents = np.array([int(i) for i in RECORD_CONTENTS[9+self.nxfloat:9+self.nxfloat+self.nxlong]], dtype="i2")
        # print(self.record_contents, self.extrafloat_contents, self.extralong_contents )

        # Zero flags in RECORD_CONTENTS mark values supplied by RECORD_CONSTANT.
        self.record_constant=np.ones( 7, dtype="f4")*np.nan
        ix1 = self.record_contents[0:7] == 0  # constant indexes has zero in RECORD_CONTENTS
        self.constant = np.array([ float(i) for i in RECORD_CONSTANT ], dtype="f4") # set specified constants to array or NaN
        self.record_constant[ix1] = self.constant # eg if z is constant then =[ x=nan  y=nan z=z  u=nan  v=nan  w=nan  wt=nan]
        ix2 = np.logical_not(ix1)
        ix1[5]=ix2[5]=False   # 'w' is never stored only as sign in particle type
        print(self.record_constant, self.constant, ix1, ix2)

        # what attributes are constant and what are dynamic
        attributes7 = ['x','y','z','u','v','w','wt']  # 7 selectable attribues but w
        self.rec_attr   = [attributes7[i] for i in range(7) if ix2[i]]
        self.const_attr = [attributes7[i] for i in range(7) if ix1[i]]
        # print(self.rec_attr, self.const_attr)

        # setup record data
        self.r = IAEArecord()
        for i in range(len(self.constant )):   # initialize constant data in record
            self.r.__setattr__(self.const_attr[i], self.constant[i])


        # set record length - store one record from phase space
        self.record_length=5  # type(1Byte) and energy(4B)
        self.record_length += np.sum(self.record_contents)*4
        self.record_length -= 4 # w is not stored, just his sign

        # struct.unpack string
        self.record_unpack = "=bf"  # Standard sizes, no padding: 1 byte for type and 4 for energy.
        self.record_unpack += f"{np.sum(self.record_contents[0:7]) - 1}f"  # xyz uvw whgt
        if self.nxfloat > 0:
            self.record_unpack += f"{self.nxfloat}f"
        if self.nxlong > 0:
            self.record_unpack += f"{self.nxlong}i"

        # particles
        self.particles = PH['PARTICLES'][0][0]
        print(f"record_length:{self.record_length} particles:{self.particles} unpack:{self.record_unpack}")


    def decode_record(self, b):
        """Decode one binary phase-space record into an IAEArecord."""
        q = struct.unpack(self.record_unpack, b)  # Unpack using the configured standard sizes.
        self.r.t = q[0]
        self.r.E = q[1]
        for i in range(len(self.rec_attr)):              # parse dynamic data
            self.r.__setattr__(self.rec_attr[i], q[2+i])
        p=q[2+len(self.rec_attr):]      # data for xfloat and xlong
        if self.nxfloat > 0:
            self.r.xfloat = p[:self.nxfloat]
        if self.nxlong > 0:
            self.r.xlong = p[self.nxfloat:]
        if self.r.t < 0:  # here is stored sign for w
            sw=-1
            self.r.t = -self.r.t
        else:
            sw=1

        if self.r.E < 0:  # new history
            self.r.h=0
            self.r.E = -self.r.E
        else:
            self.r.h += 1  # update history

        # calculate w
        self.r.w = 0.0
        aux = self.r.u**2 + self.r.v**2
        if aux <= 1.0:
            self.r.w = sw * np.sqrt(1.0 - aux)
        else:
            norm = hypot(self.r.u, self.r.v)
            self.r.u /= norm
            self.r.v /= norm

        # print(self.r)
        return self.r


    def read_test(self, fnphsp):
        """Print the first 15 records from a binary phase-space file."""
        if self.record_length <= 0:
            print("Error: record not set up")
            sys.exit()

        with open(fnphsp, "rb") as fi:
            for i in range(15):
                b = fi.read(self.record_length)
                r = self.decode_record(b)
                print(r)


# Header values are stored in input order. Each block maps to a pair of lists:
# content lines and their corresponding ``//`` comments. Blank lines are ignored.
def read_iaeaphsp_header(filename_iaeaphsp):
    """Read an IAEA phase-space header.

    Args:
        filename_iaeaphsp: Path to an ``.IAEAheader`` file.

    Returns:
        A dictionary mapping each block name to its content lines and comments.
    """
    def split_data(data):
        lines,notes=[],[]
        for d in data:
            q = d.split('//',1)  # we only support c++ // comments
            lines.append(q[0])
            if len(q) > 1:
                notes.append(q[1])
            else:
                notes.append('')
        return lines,notes

    PH={}
    key=None
    data=[]
    with open(filename_iaeaphsp, "r") as fi:
        for line in fi:
            line = line.rstrip()
            # print(line)
            if len(line) == 0:
                continue
            if line[0] == '$' and line[-1]==':':   # key - blockname
                if key is not None:                # save previous block if any
                    lines,notes = split_data(data)
                    PH[key] = [lines,notes]
                    key=None
                    data=[]

                key = line[1:-1]
                # print(key)
            else:
                if key is not None:
                    data.append(line)

    if key is not None:
        lines,notes = split_data(data)
        PH[key] = [lines,notes]

    # for k,v in PH.items():
    #     print(f"${k}:")
    #     for d in zip(*v):
    #         # print(d)
    #         line,note = d
    #         print(f"{line}", end='')
    #         if len(note): print(f"//{note}", end='')
    #         print()
    #     print()

    return PH

def write_iaeaphsp_header(PH, filename_iaeaphsp, overwrite=False):
    """Write parsed IAEA header blocks to an ``.IAEAheader`` file.

    Args:
        PH: Mapping of block names to content lines and ``//`` comments.
        filename_iaeaphsp: Output header filename or path.
        overwrite: Whether to replace an existing file. Defaults to False.
    """
    filename_iaeaphsp = Path(filename_iaeaphsp)
    if not overwrite and filename_iaeaphsp.exists():
        print(f"File {filename_iaeaphsp} already exists")
        sys.exit(1)

    with open(filename_iaeaphsp, "w") as fo:
        for k,v in PH.items():
            fo.write(f"${k}:\n")
            for d in zip(*v):   # v=[lines,notes]
                line,note = d
                fo.write(f"{line}")
                if len(note):
                    fo.write(f"//{note}")
                fo.write("\n")
            fo.write("\n")



def join_iaeaphsp(phsps_in, phsp_out, overwrite=False):
    """Join IAEA headers and their matching binary phase-space files.

    Each input header must have a matching ``.IAEAphsp`` file with the same
    base name. The output header and binary data use the base name of
    ``phsp_out``.
    """
    phsp_out = Path(phsp_out)
    phsps_in = [Path(fn) for fn in phsps_in]

    if phsp_out.suffix != ".IAEAheader":
        print(f"File {phsp_out} suffix is not .IAEAheader")
        sys.exit(1)

    if not overwrite and phsp_out.exists():
        print(f"File {phsp_out} already exists")
        sys.exit(1)

    # Joined headers omit per-file particle and geometry statistics.
    PH=None
    for fn in phsps_in:
        if fn.suffix != ".IAEAheader":
            print(f"File {fn} suffix is not .IAEAheader")
            sys.exit(1)
        ph = read_iaeaphsp_header(fn)
        if PH is None:   # first just simply copy header
            PH=ph
            continue
        else:
            PH['ORIG_HISTORIES'][0][0] = str( int(PH['ORIG_HISTORIES'][0][0]) + int(ph['ORIG_HISTORIES'][0][0]) ) # mandatory
            PH['PARTICLES'][0][0] = str( int(PH['PARTICLES'][0][0]) + int(ph['PARTICLES'][0][0]) ) # mandatory
            for k in iaeaphsp_particles: # mandatory - but not each particle must be present
                if k in PH:
                    PH[k][0][0] = str( int(PH[k][0][0]) + int(ph[k][0][0]) )


    del PH['STATISTICAL_INFORMATION_PARTICLES']
    del PH['STATISTICAL_INFORMATION_GEOMETRY']

    # Record the input header paths in the output notes.
    PH['ADDITIONAL_NOTES'][0].extend(phsps_in)
    PH['ADDITIONAL_NOTES'][1].extend([''] * len(phsps_in))

    # update CHECKSUM = RECORD_LENGTH * PARTICLES
    PH['CHECKSUM'][0][0] = str( int(PH['RECORD_LENGTH'][0][0]) * int(PH['PARTICLES'][0][0]) )

    write_iaeaphsp_header(PH, phsp_out, overwrite)

    # join files
    phsp_out2 = phsp_out.with_suffix('.IAEAphsp')
    phsps_in2 = [ fn.with_suffix('.IAEAphsp') for fn in phsps_in]
    # print(phsp_out2, phsps_in2)

    # Concatenate the binary files in input order.
    with phsp_out2.open('wb') as wfd:
        for fn in phsps_in2:
            with fn.open('rb') as fd:
                shutil.copyfileobj(fd, wfd)


def main():
    parser = argparse.ArgumentParser(
        description="Join IAEA phase-space headers and their matching binary files."
    )
    parser.add_argument("inputs", nargs="+", type=Path, help="input .IAEAheader files")
    parser.add_argument("--output", required=True, type=Path, help="output .IAEAheader path")
    parser.add_argument("--overwrite", action="store_true", help="replace existing output files")
    args = parser.parse_args()

    join_iaeaphsp(args.inputs, args.output, overwrite=args.overwrite)


if __name__ == "__main__":
    main()
