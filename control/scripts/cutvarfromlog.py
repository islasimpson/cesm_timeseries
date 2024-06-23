import xarray as xr
import numpy as np
import sys
import os

def cutvarfromlog(logfile,var):
    try:
        with open(logfile,'r') as file:
            lines = file.readlines()
            newlines = [line for line in lines if line.strip() != var]
            with open(logfile,'w') as file:
                file.writelines(newlines)
    except:
        print(f"Error removing variable: {var} from {logfile}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python ???")
        sys.exit(1)

    logfile=sys.argv[1]
    var=sys.argv[2]
    cutvarfromlog(logfile,var)
