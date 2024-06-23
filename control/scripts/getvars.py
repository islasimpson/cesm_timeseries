import xarray as xr
import numpy as np
import sys
import os

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
    if len(sys.argv) < 3:
        print("Usage: python ???")
        sys.exit(1)

    filename = sys.argv[1]
    logname = sys.argv[2]
    getvars(filename,logname)


    
