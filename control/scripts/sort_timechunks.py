import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from glob import glob
import os
import datetime
import sys
import argparse

import warnings
warnings.filterwarnings('ignore')

def main():
    parser = argparse.ArgumentParser(description="Argument parser for sorting out time")
    parser.add_argument('--tempdir', type=str, required=True, help='Location of temporary dir')
    parser.add_argument('--basepath', type=str, required=True, help='Directory containing history flies')
    parser.add_argument('--runname', type=str, required=True, help='Simulation name')
    parser.add_argument('--ystart', type=int, required=True, help='Start year of time series generation')
    parser.add_argument('--yend', type=int, required=True, help='End year of time series generation')
    parser.add_argument('--chunk_size', type=int, required=True, help='Chunk size for time series chunking')

    args = parser.parse_args()

    #---???Could add other options here.  If statements depending on daily average, monthly average etc
    sorttime_day_avg(args.tempdir,args.basepath,args.runname,args.ystart,args.yend,args.chunk_size)


def sortout_time_day_avg(dat):
    timebndavg = np.array(dat['time_bnds'],
                          dtype='datetime64[s]').view('i8').mean(axis=1).astype('datetime64[s]')
    dates = pd.DatetimeIndex(timebndavg)
    lyindices=np.argwhere( (dates.month == 2) & ( dates.day == 29))
    if (len(lyindices) > 0):
        for i in lyindices:
            timebndavg[i] = str(dates.year[i].item())+'-02-28T12:00:00'
    dat['time'] = timebndavg

    # ----sort out any dates that have a time of 00h by subtracting 12h
    # Print a warning when doing this
    hours = dat.time.dt.hour
    indices = hours == 0
    if (len(indices) > 0):
        indices = np.where(indices)[0]
        timeold = dat.time[indices]
        timenew = dat.time.copy()
        timenew.values[indices] = timenew.values[indices] - np.timedelta64(12,'h')
        for i in np.arange(0,len(indices),1):
            with open("./logs/warnings.txt",'a') as file:
                file.write(f"Warning: changed {str(timeold[i].values)} to {str(timenew[i].values)}"+'\n')
        dat = dat.assign_coords(time=timenew)
    return dat

def sorttime_day_avg(tempdir,basepath,runname,ystart,yend,chunk_size):
    #--read in files that contain time variable
    timefiles = sorted(glob(tempdir+"*.nc"))

    #--Set up the real filenames that contain the data
    files = [ basepath+os.path.basename(ifile) for ifile in timefiles ] 

    #--Loop over files and sort out the time
    alltime=[]
    for i in np.arange(0,len(timefiles),1):
        dat = xr.open_dataset(timefiles[i])

        #----Could have an if statement here when incorporating more than daily averages
        dat = sortout_time_day_avg(dat)
        
        #---Get a list of all the times in al lthe files
        alltime.append(dat)

    segment=0
    for iyear in np.arange(ystart,yend+1,chunk_size):

        #---Would need to change this if we want more flexibility beyond chunks of integer years
        d1 = np.array(pd.date_range(start=str(iyear)+'-01-01 12:00:00', periods=1))
        d1string = str(iyear)+'0101'
        d2 = np.array(pd.date_range(start=str(iyear + chunk_size-1)+'-12-31 12:00:00', periods=1))
        d2string = str(iyear+chunk_size-1)+'1231'
        fnamestring=d1string+'-'+d2string
        found_d1=False
        found_d2=False

        #---Now loop over files to fine the files that contribute to the chunk
        #   and the indices for nco
        for ifile in np.arange(0,len(alltime),1):
            if (found_d1 == False):
                test = np.argwhere(np.array(alltime[ifile].time) == d1)
                if (len(test) > 0):
                    filelist=[files[ifile]]
                    sumtimes = alltime[ifile].time.size
                    id1 = test[0][0]
                    found_d1 = True
            elif ((found_d1 == True) & (found_d2 == False)):
                filelist.append(files[ifile])
                sumtimes = sumtimes + alltime[ifile].time.size

            if (found_d2 == False):
                test = np.argwhere(np.array(alltime[ifile].time) == d2)
                if (len(test) > 0):
                    id2 = test[0][0]
                    sumtimes = sumtimes - alltime[ifile].time.size + id2
                    found_d2 = True

        with open('./control/files/segment_files_'+str(segment).zfill(4)+'.txt','w') as file:
            for itime in filelist:
                file.write("%s\n" % itime)

        with open('./control/files/segment_index_'+str(segment).zfill(4)+'.txt','w') as file:
            file.write("%s\n" % str(id1))
            file.write("%s\n" % str(sumtimes))
            file.write("%s\n" % fnamestring)

        segment = segment + 1

if __name__ == "__main__":
    main()
