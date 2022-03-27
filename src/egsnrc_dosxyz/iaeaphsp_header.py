#!/usr/bin/env python3

# simple iaea header reader
def read_iaeaphsp_header(filename_iaeaphsp):
    """simple iaea header reader

    Args:
        filename_iaeaphsp (str): IAEA phase spase full filename with extension

    Returns:
        dict: IAEA phase space as discionary, all values as strings
    """
    PH={}
    key=None
    data=[]
    with open(filename_iaeaphsp, "r") as fi:
        for line in fi:
            line = line.rstrip()
            # print(line)
            if len(line)==0: 
                if key is not None:
                    PH[key] = "\n".join(data)
                    key=None
                    data=[]
                continue
            if line[0] == '$' and line[-1]==':':   # key
                key = line[1:-1]
                # print(key)
            else:
                if key is not None:
                    data.append(line)
    if key is not None:
        PH[key] = "\n".join(data)


    # for k,v in H.items():
    #     print(f"{k}\n{v}")
    return PH

if __name__ == "__main__":
    PH = read_iaeaphsp_header("ex1.IAEAheader")
    print(PH['PARTICLES'])