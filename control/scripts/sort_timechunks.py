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
    parser.add_argument('--datestart', type=str, required=True, help='Start year of time series generation')
    parser.add_argument('--dateend', type=str, required=True, help='End year of time series generation')
    parser.add_argument('--chunk_size', type=int, required=True, help='Chunk size for time series chunking')

    args = parser.parse_args()

    #---???Could add other options here.  If statements depending on daily average, monthly average etc
    sorttime_day_avg(args.tempdir,args.basepath,args.runname,args.datestart,args.dateend,args.chunk_size)


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

def sorttime_day_avg(tempdir,basepath,runname,datestart,dateend,chunk_size):
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


    #--Convert initial date to an integer to keep track
    idate = int(datestart)
    d1_str = datestart

    year_d1 = d1_str[0:4]
    mon_d1 = d1_str[4:6]
    d1 = pd.date_range(start=str(year_d1)+'-'+str(mon_d1)+'-01 12:00:00', periods=1)

    #---Loop over date ranges
    segment=0
    while idate < int(dateend):

        if (chunk_size > 0):
            d2 = d1 + pd.DateOffset(years=chunk_size) - pd.DateOffset(days=1)
        if (chunk_size < 0):
            d2 = d1 + pd.DateOffset(months=np.abs(chunk_size)) - pd.DateOffset(days=1)

        d1string = str(d1.year.values[0])+str(d1.month.values[0]).zfill(2)+str(d1.day.values[0]).zfill(2)
        d2string = str(d2.year.values[0])+str(d2.month.values[0]).zfill(2)+str(d2.day.values[0]).zfill(2)

        fnamestring=d1string+'-'+d2string
        found_d1=False
        found_d2=False

        #---Now loop over files to fine the files that contribute to the chunk
        #   and the indices for nco
        for ifile in np.arange(0,len(alltime),1):
            if (found_d1 == False):
                test = np.argwhere(np.array(alltime[ifile].time) == d1[0])
                if (len(test) > 0):
                    filelist=[files[ifile]]
                    sumtimes = alltime[ifile].time.size
                    id1 = test[0][0]
                    found_d1 = True
            elif ((found_d1 == True) & (found_d2 == False)):
                filelist.append(files[ifile])
                sumtimes = sumtimes + alltime[ifile].time.size

            if (found_d2 == False):
                test = np.argwhere(np.array(alltime[ifile].time) == d2[0])
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

        # --- setting dates and segment names up for the next iteration
        d1 = d2 + pd.DateOffset(days=1)
        idate = int(str(d1.year.values[0])+str(d1.month.values[0]).zfill(2)+str(d1.day.values[0]).zfill(2)) 
        segment = segment + 1

if __name__ == "__main__":
    main()
