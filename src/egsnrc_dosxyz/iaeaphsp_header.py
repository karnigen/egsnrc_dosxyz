#!/usr/bin/env python3

from dataclasses import dataclass,field

from pathlib import Path
import shutil
import numpy as np
import struct

# IAEA phsp file format - in egsnrc
# =================================
# General rules:
#   - c /**/ and c++ // comments are ignored, are allowed anywhere, free format
#   - file contains blockname with block
#   - blockname format
#     - $blockname:   - on separate line
#   - block 
#     - starts immediately after blockname
#     - \n is part of block
#     - block end with next blockname ($) or eof
#  
# - CHECKSUM = RECORD_LENGTH * PARTICLES
#

# - order of particles types is strictly given ???
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

    # set phsp record parameters
    # PH - input from read_iaeaphsp_header(fn)
    # record contents: 9  compulsory + I extra + F extra
    #  type,energy are not in RECORD_CONTENTS
    #    1    2    345 678   9    - given order
    #  type energy xyz uvw   wt
    #
    # - motivation: iaea_header.cpp in egs
    def setup_record(self, PH):
        # parsing RECORD_CONTENTS
        RECORD_CONTENTS = list( filter(str.strip,  PH['RECORD_CONTENTS'][0]) )  # skip empty lines
        RECORD_CONSTANT = list( filter(str.strip,  PH['RECORD_CONSTANT'][0]) )  # skip empty lines

        self.record_contents = np.array([ int(i) for i in RECORD_CONTENTS[0:9] ], dtype="i2") # take first 9 numbers
        self.nxfloat = self.record_contents[7]
        self.nxlong = self.record_contents[8]
        self.extrafloat_contents = np.array([int(i) for i in RECORD_CONTENTS[9:9+self.nxfloat]], dtype="i2")
        self.extralong_contents = np.array([int(i) for i in RECORD_CONTENTS[9+self.nxfloat:9+self.nxfloat+self.nxlong]], dtype="i2")
        # print(self.record_contents, self.extrafloat_contents, self.extralong_contents )

        # read RECORD_CONSTANT - all zeros in record_contents are record_constant, eg only one z for whole phsp file
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
        self.record_unpack = "=bf"  # type and energy 1B+4B,  =B no allignment, otherwise B takes 4bytes, instead of 1B
        self.record_unpack+="{}f".format(np.sum(self.record_contents[0:7])-1) # xyz uvw whgt
        if self.nxfloat > 0: self.record_unpack+="{}f".format(self.nxfloat)
        if self.nxlong  > 0: self.record_unpack+="{}i".format(self.nxlong)

        # particles
        self.particles = PH['PARTICLES'][0][0]
        print(f"record_length:{self.record_length} particles:{self.particles} unpack:{self.record_unpack}")


    # convert binary data to structure
    def decode_record(self, b):
        q = struct.unpack(self.record_unpack, b)  # no allignment !!!
        self.r.t = q[0]
        self.r.E = q[1]
        for i in range(len(self.rec_attr)):              # parse dynamic data
            self.r.__setattr__(self.rec_attr[i], q[2+i])
        p=q[2+len(self.rec_attr):]      # data for xfloat and xlong
        if self.nxfloat > 0: self.r.xfloat = p[:self.nxfloat]
        if self.nxlong > 0: self.r.xlong = p[self.nxfloat:]
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
            aux = sqrt(aux)
            self.r.u /= aux
            self.r.v /= aux

        # print(self.r)
        return self.r


    # fnphsp - phsp with ending IAEAphsp
    # - example how to read phsp file
    def read_test(self, fnphsp):
        if self.record_length <= 0:
            print("Error: record not set up")
            exit()
            return

        with open(fnphsp, "rb") as fi:
            for i in range(15):
                b = fi.read(self.record_length)
                r = self.decode_record(b)
                print(r)


# simple iaea header reader
# PH - order of blocks as in input file
#    - for each blockname: is array of array
#      - [0] are lines [] - without \n
#      - [1] are notes [] - same size as lines contains c++ notes //
#      - empty lines are ignored, but lines with only c++ comment // are stored as empty line + notes
def read_iaeaphsp_header(filename_iaeaphsp):
    """simple iaea header reader

    Args:
        filename_iaeaphsp (str): IAEA phase spase full filename with extension .IAEAheader

    Returns:
        dict: IAEA phase space as discionary, all values as strings
              key : [0] - lines
                    [1] - notes
    """
    def split_data(data):
        lines,notes=[],[]
        for d in data:
            q = d.split('//',1)  # we only support c++ // comments
            lines.append(q[0])
            if len(q) > 1: notes.append(q[1])
            else:          notes.append('')
        return lines,notes

    PH={}
    key=None
    data=[]
    with open(filename_iaeaphsp, "r") as fi:
        for line in fi:
            line = line.rstrip()
            # print(line)
            if len(line)==0: continue
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

# PH - dictionary phase spase header
def write_iaeaphsp_header(PH, filename_iaeaphsp, overwrite=False):
    filename_iaeaphsp = Path(filename_iaeaphsp)
    if not overwrite and filename_iaeaphsp.exists():
        print(f"File {filename_iaeaphsp} already exists")
        exit(1)

    with open(filename_iaeaphsp, "w") as fo:
        for k,v in PH.items():
            fo.write(f"${k}:\n")
            for d in zip(*v):   # v=[lines,notes]
                line,note = d
                fo.write(f"{line}")
                if len(note): fo.write(f"//{note}")
                fo.write("\n")
            fo.write("\n")

 

# phsps_in - list of phsp spaces
# phsp_out - output phsp with .IAEAheader suffix
def join_iaeaphsp(phsps_in, phsp_out, overwrite=False):
    phsp_out = Path(phsp_out)
    phsps_in = [Path(fn) for fn in phsps_in]

    if phsp_out.suffix != ".IAEAheader":
        print(f"File {phsp_out} suffix is not .IAEAheader")
        exit(1)

    if not overwrite and phsp_out.exists():
        print(f"File {phsp_out} already exists")
        exit(1)

    # simple join headers - without STATISTICAL_INFORMATION_PARTICLES and STATISTICAL_INFORMATION_GEOMETRY
    # PH       key : [0] - lines
    #                [1] - notes
    PH=None
    for fn in phsps_in:
        if fn.suffix != ".IAEAheader":
            print(f"File {fn} suffix is not .IAEAheader")
            exit(1)
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

    # add list of input files into notes
    PH['ADDITIONAL_NOTES'][0].extend(phsps_in)
    PH['ADDITIONAL_NOTES'][1].extend([''] * len(phsps_in))

    # update CHECKSUM = RECORD_LENGTH * PARTICLES
    PH['CHECKSUM'][0][0] = str( int(PH['RECORD_LENGTH'][0][0]) * int(PH['PARTICLES'][0][0]) )

    write_iaeaphsp_header(PH, phsp_out, overwrite)

    # join files
    phsp_out2 = phsp_out.with_suffix('.IAEAphsp')
    phsps_in2 = [ fn.with_suffix('.IAEAphsp') for fn in phsps_in]
    # print(phsp_out2, phsps_in2)

    # - cat files in order of phsps_in
    # - must be binary 'wb' 'rb'
    with phsp_out2.open('wb') as wfd:
        for fn in phsps_in2:
            with fn.open('rb') as fd:
                shutil.copyfileobj(fd, wfd)


if __name__ == "__main__":
    # PH = read_iaeaphsp_header("ex1.IAEAheader")
    # print(PH['PARTICLES'])
    # print(PH['MONTE_CARLO_CODE_VERSION'])
    # print(PH['GLOBAL_PHOTON_ENERGY_CUTOFF'])
    # write_iaeaphsp_header(PH, "ex2.IAEAheader", overwrite=True)

    ph_in = ["ex1.IAEAheader", "ex2.IAEAheader"]
    ph_ou = "ex_all.IAEAheader"
    join_iaeaphsp(ph_in, ph_ou, overwrite=True)
