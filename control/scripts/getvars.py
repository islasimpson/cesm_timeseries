import xarray as xr
import numpy as np
import sys
import os
import argparse

def main():
    parser = argparse.ArgumentParser(description="Argument parser for getting variables")
    parser.add_argument('--filename', type=str, required=True, help='First history file used for getting variables')
    parser.add_argument('--logname', type=str, required=True, help='Location of file that contains the variable list')

    args = parser.parse_args()
    getvars(args.filename, args.logname)

def getvars(filename, logname):
    try:
        ds = xr.open_dataset(filename)
        ds_vars = list(ds.data_vars)
    except:
        print(f"Error opening file: {filename}")
        sys.exit(1)

    dropvars=['w','hyam','hybm','hyai','hybi','date','datesec','time_bnds','date_written',
          'time_written','ndbase','nsbase','nbdate','nbsec','mdt','ndcur','nscur',
          'co2vmr','ch4vmr','n2ovmr','f11vmr','f12vmr','sol_tsi','nsteph','lon','lat','area']

    for ivar in dropvars:
        if ivar in ds_vars:
            ds_vars.remove(ivar)

    try:
        if os.path.exists(logname):
            os.remove(logname)
        with open(logname,'w') as file:
            for ivar in ds_vars:
                file.write(ivar + '\n')
    except:
        print(f"Error writing file: {logname}")
        sys.exit(1)


if __name__ == "__main__":
    main()

    
