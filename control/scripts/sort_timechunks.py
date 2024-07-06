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
    parser.add_argument('--freq', type=str, required=True, help='Frequency of the data to be processed, Options: day_avg, mon_avg, 6h_avg')
    parser.add_argument('--timebndsvar',type=str, required=True, help='Name of time bounds variable')

    args = parser.parse_args()

    #---???Could add other options here.  If statements depending on daily average, monthly average etc
    if (args.freq == 'day_avg'):
        sorttime_day_avg(args.tempdir,args.basepath,args.runname,args.datestart,args.dateend,args.chunk_size,args.timebndsvar)

    if (args.freq == 'mon_avg'):
        sorttime_mon_avg(args.tempdir,args.basepath,args.runname,args.datestart,args.dateend,args.chunk_size,args.timebndsvar)

    if (args.freq == '6h_avg'):
        sorttime_6h_avg(args.tempdir,args.basepath,args.runname,args.datestart,args.dateend,args.chunk_size,args.timebndsvar)

#------subroutine for managing month offsets in pandas datetime 
def add_months(time, nmonths):
    month = time.month -1 + nmonths
    year = time.year + month // 12
    month = month % 12 + 1
    return time.replace(year=year, month=month) - datetime.timedelta(days=1)



#------------------------DAILY AVERAGED SCRIPTS---------------------------------------

def sortout_time_day_avg(dat, timebndsvar):
    timebnds = dat[timebndsvar]
    diff = np.array(timebnds.isel(nbnd=1)) - np.array(timebnds.isel(nbnd=0))
    diff = diff/2.
    newtime = np.array(timebnds.isel(nbnd=0)) + diff
    dat = dat.assign_coords(time=newtime)

    hours = [ newtime[i].hour for i in np.arange(0,len(newtime),1) ]
    indices = np.argwhere(np.array(hours) == 0)
    if (len(indices) > 0):
        indices = indices[:,0].tolist()
        timeold = dat.time[indices]
        timenew = dat.time.copy()
        timenew.values[indices] = timenew.values[indices] - datetime.timedelta(hours=12)
        for i in np.arange(0,len(indices),1):
            with open("./logs/warnings.txt",'a') as file:
                file.write(f"Warning: changed {str(timeold[i].values)} to {str(timenew[i].values)}"+'\n')
        dat = dat.assign_coords(time=timenew)
    return dat

def sorttime_day_avg(tempdir,basepath,runname,datestart,dateend,chunk_size,timebndsvar):
    #--read in files that contain time variable
    timefiles = sorted(glob(tempdir+"*.nc"))

    #--Set up the real filenames that contain the data
    files = [ basepath+os.path.basename(ifile) for ifile in timefiles ] 

    #--Loop over files and sort out the time
    alltime=[]
    for i in np.arange(0,len(timefiles),1):
        dat = xr.open_dataset(timefiles[i])

        #----Could have an if statement here when incorporating more than daily averages
        dat = sortout_time_day_avg(dat,timebndsvar)
        
        #---Get a list of all the times in al lthe files
        alltime.append(dat)


    #--Convert initial date to an integer to keep track
    idate = int(datestart)
    #--Convert end date to an integer
    dend = int(dateend)

    d1_str = datestart
    dend_str = dateend

    year_d1 = d1_str[0:4]
    mon_d1 = d1_str[4:6]
    year_dend = dend_str[0:4]
    mon_dend = dend_str[4:6]
    day_dend = dend_str[6:8]

#    d1 = pd.date_range(start=str(year_d1)+'-'+str(mon_d1)+'-01 12:00:00', periods=1)
    d1 = datetime.datetime(int(year_d1), int(mon_d1), 1)
    dend_dt = datetime.datetime(int(year_dend), int(mon_dend),1)
    dend_dt = add_months(dend_dt,1)
    dend_dt = dend_dt #- datetime.timedelta(days=1)



    #---Loop over date ranges
    segment=0
    flagleap=False
    countfiles=0
    while idate < int(dateend):

        if (chunk_size > 0):
            d2 = d1.replace(year=d1.year + chunk_size) - datetime.timedelta(days=1)
        if (chunk_size < 0):
            d2 = add_months(d1, np.abs(chunk_size))
            if ( (d2.month == 2) & (d2.day == 29) ):
                d2 = d2 - datetime.timedelta(days=1)
                flagleap=True
        if (chunk_size == 0):
            nmonths = (12 - int(mon_d1) + 1) + (int(year_dend) - int(year_d1) - 1)*12 + int(mon_dend)
            d2 = add_months(d1,nmonths) - datetime.timedelta(days=1)

        #---check that d2 is not past the end of the time range for processing
        d2_int = int(str(d2.year).zfill(4)+str(d2.month).zfill(2)+str(d2.day).zfill(2))
        if (d2_int > int(dend)):
            d2 = dend_dt


        d1string = str(d1.year).zfill(4)+str(d1.month).zfill(2)+str(d1.day).zfill(2)
        d2string = str(d2.year).zfill(4)+str(d2.month).zfill(2)+str(d2.day).zfill(2)

        fnamestring=d1string+'-'+d2string
        found_d1=False
        found_d2=False

        #---Now loop over files to fine the files that contribute to the chunk
        #   and the indices for nco
        ifile = countfiles
        while (found_d2 == False):
        #for ifile in np.arange(0,len(alltime),1):

            time_thisfile = alltime[ifile].time
            timestring = [ str(time_thisfile.dt.year.values[i]).zfill(4)+
                           str(time_thisfile.dt.month.values[i]).zfill(2)+
                           str(time_thisfile.dt.day.values[i]).zfill(2) 
                           for i in np.arange(0,time_thisfile.time.size,1) ]


            if (found_d1 == False):
                test = np.isin(d1string, timestring)
                if (test):
                    filelist=[files[ifile]]
                    sumtimes = alltime[ifile].time.size
                    i = np.argwhere(np.char.find(timestring, d1string) >= 0)
                    i = i.flatten()
                    id1 = i[0]
                    found_d1 = True
            elif ((found_d1 == True) & (found_d2 == False)):
                filelist.append(files[ifile])
                sumtimes = sumtimes + alltime[ifile].time.size

            if (found_d2 == False):
                test = np.isin(d2string, timestring)
                if (test):
                    i = np.argwhere(np.char.find(timestring, d2string) >= 0)
                    i = i.flatten()
                    id2 = i[0]
                    sumtimes = sumtimes - alltime[ifile].time.size + id2
                    found_d2 = True
                    countfiles=ifile
            ifile = ifile + 1

        with open('./control/files/segment_files_'+str(segment).zfill(4)+'.txt','w') as file:
            for itime in filelist:
                file.write("%s\n" % itime)

        with open('./control/files/segment_index_'+str(segment).zfill(4)+'.txt','w') as file:
            file.write("%s\n" % str(id1))
            file.write("%s\n" % str(sumtimes))
            file.write("%s\n" % fnamestring)

        # --- setting dates and segment names up for the next iteration
        d1 = d2 + datetime.timedelta(days=1)
        if (flagleap):
            d1 = d1 + datetime.timedelta(days=1)
            flagleap=False

        idate = int(str(d1.year).zfill(4)+str(d1.month).zfill(2)+str(d1.day).zfill(2))
        segment = segment + 1

#-----------------------END DAILY AVERAGED SCRIPTS--------------------------


#-----------------------6 HOURLY AVERAGED SCRIPTS--------------------------

def sortout_time_6h_avg(dat, timebndsvar):
    timebnds = dat[timebndsvar]
    diff = np.array(timebnds.isel(nbnd=1)) - np.array(timebnds.isel(nbnd=0))
    diff = diff/2.
    newtime = np.array(timebnds.isel(nbnd=0)) + diff
    dat = dat.assign_coords(time=newtime)
    
    hours = [ newtime[i].hour for i in np.arange(0,len(newtime),1) ]
    indices = np.argwhere(np.array(hours) == 0)
    if (len(indices) > 0):
        indices = indices[:,0].tolist()
        timeold = dat.time[indices]
        timenew = dat.time.copy()
        timenew.values[indices] = timenew.values[indices] - datetime.timedelta(hours=3)
        for i in np.arange(0,len(indices),1):
            with open("./logs/warnings.txt",'a') as file:
                file.write(f"Warning: changed {str(timeold[i].values)} to {str(timenew[i].values)}"+'\n')
        dat = dat.assign_coords(time=timenew)
    return dat



def sorttime_6h_avg(tempdir,basepath,runname,datestart,dateend,chunk_size,timebndsvar):
    """Sort out 6 hourly averaged fields"""
    #--read in files that contain the time variable
    timefiles = sorted(glob(tempdir+"*.nc"))

    #--Set up the real filenames that contain the data
    files = [ basepath+os.path.basename(ifile) for ifile in timefiles ] 

    alltime=[]
    for i in np.arange(0,len(timefiles),1):
        dat = xr.open_dataset(timefiles[i]) 
        dat = sortout_time_6h_avg(dat,timebndsvar)
        alltime.append(dat)

    #----Convert initial date to an integer to keep track
    idate = int(datestart)
    dend = int(dateend)

    d1_str = datestart
    dend_str = dateend
    
    year_d1 = d1_str[0:4]
    mon_d1 = d1_str[4:6]
    year_dend = dend_str[0:4]
    mon_dend = dend_str[4:6]
    day_dend = dend_str[6:8]   
 
#    d1 = pd.date_range(start=str(year_d1)+'-'+str(mon_d1)+'-01 03:00:00', periods=1)
    d1 = datetime.datetime(int(year_d1), int(mon_d1),1,3)
    dend_dt = datetime.datetime(int(year_dend), int(mon_dend),1,21)
    dend_dt = add_months(dend_dt,1)
    dend_dt = dend_dt #- datetime.timedelta(days=1)
    
    segment=0
    flagleap=False
    countfiles=0
    while idate < int(dateend):
        if (chunk_size > 0):
            d2 = d1.replace(year=d1.year+chunk_size) - datetime.timedelta(hours=6)
        if (chunk_size < 0):
            d2 = add_months(d1, np.abs(chunk_size)) + datetime.timedelta(hours=18)
            if ( (d2.month == 2) & (d2.day == 29) ):
                d2 = d2 - pd.DateOffset(days=1)
                flagleap=True
        if (chunk_size == 0):
            nmonths = (12 - int(mon_d1) + 1) + (int(year_dend) - int(year_d1) - 1)*12 + int(mon_dend)
            d2 = add_months(d1,nmonths) - datetime.timedelta(hours=6)       

        #---check that d2 is not past the end of the time range for processing
        d2_int = int(str(d2.year).zfill(4)+str(d2.month).zfill(2)+str(d2.day).zfill(2))
        if (d2_int > int(dend)):
            d2 = dend_dt

        d1string = str(d1.year).zfill(4)+str(d1.month).zfill(2)+str(d1.day).zfill(2)+str(d1.hour).zfill(2)
        d2string = str(d2.year).zfill(4)+str(d2.month).zfill(2)+str(d2.day).zfill(2)+str(d2.hour).zfill(2)

        d1string4file = str(d1.year).zfill(4)+str(d1.month).zfill(2)+str(d1.day).zfill(2)
        d2string4file = str(d2.year).zfill(4)+str(d2.month).zfill(2)+str(d2.day).zfill(2)

    
        fnamestring=d1string4file+'-'+d2string4file
        found_d1=False
        found_d2=False
    
        #---Now loop over files to find the files that contribute to the chunk 
        #   and the indices for nco
        ifile = countfiles
        while (found_d2 == False):
            time_thisfile = alltime[ifile].time
            timestring = [ str(time_thisfile.dt.year.values[i]).zfill(4)+
                           str(time_thisfile.dt.month.values[i]).zfill(2)+
                           str(time_thisfile.dt.day.values[i]).zfill(2)+
                           str(time_thisfile.dt.hour.values[i]).zfill(2)
                           for i in np.arange(0,time_thisfile.time.size,1) ]

            if (found_d1 == False):
                test = np.isin(d1string, timestring)
                if (test):
                    filelist = [files[ifile]]
                    sumtimes = alltime[ifile].time.size
                    i = np.argwhere(np.char.find(timestring, d1string) >= 0)
                    i = i.flatten()
                    id1 = i[0]
                    found_d1 = True
            elif ((found_d1 == True) & (found_d2 == False) ):
                filelist.append(files[ifile])
                sumtimes = sumtimes + alltime[ifile].time.size
    
            if (found_d2 == False):
                test = np.isin(d2string, timestring)
                if (test):
                    i = np.argwhere(np.char.find(timestring, d2string) >= 0)
                    i = i.flatten()
                    id2 = i[0]
                    sumtimes = sumtimes - alltime[ifile].time.size + id2
                    found_d2 = True
                    countfiles = ifile
            ifile = ifile + 1   
 
        with open('./control/files/segment_files_'+str(segment).zfill(4)+'.txt','w') as file:
            for itime in filelist:
                file.write("%s\n" % itime)
    
        with open('./control/files/segment_index_'+str(segment).zfill(4)+'.txt','w') as file:
            file.write("%s\n" % str(id1))
            file.write("%s\n" % str(sumtimes))
            file.write("%s\n" % fnamestring)
    
        # --- setting dates and segment names up for the next iteration
        d1 = d2 + datetime.timedelta(hours=6)
        if (flagleap):
            d1 = d1 + datetime.timedelta(days=1)
            flagleap=False
        idate = int(str(d1.year).zfill(4)+str(d1.month).zfill(2)+str(d1.day).zfill(2).zfill(2))
        segment = segment + 1
    



#-----------------------END 6 HOURLY AVERAGED SCRIPTS----------------------



#-----------------------MONTHLY AVERAGED SCRIPTS----------------------------

def sorttime_mon_avg(tempdir,basepath,runname,datestart,dateend,chunk_size,timebndsvar):
    """Sort out monthly averaged fields"""
    #--read in files that contain the time variable
    timefiles = sorted(glob(tempdir+"*.nc"))

    #--Set up the real filenames that contain the data
    files = [ basepath+os.path.basename(ifile) for ifile in timefiles ] 

    alltime=[]
    for i in np.arange(0,len(timefiles),1):
        dat = xr.open_dataset(timefiles[i], decode_times='False')
        timebnds = dat[timebndsvar]
        diff = np.array(timebnds.isel(nbnd=1)) - np.array(timebnds.isel(nbnd=0))
        diff = diff/2.
        newtime = np.array(timebnds.isel(nbnd=0)) + diff
        dat['time'] = newtime 
        alltime.append(dat)


    d1_str = datestart
    dend_str = dateend

    year_d1 = d1_str[0:4]
    mon_d1 = d1_str[4:6]
    year_dend = dend_str[0:4]
    mon_dend = dend_str[4:6]

    # start date in datetime format
    d1 = datetime.datetime(int(year_d1), int(mon_d1), 1)

    # end date in datetime format
    dend_dt = datetime.datetime(int(year_dend), int(mon_dend),1)
    dend_dt = add_months(dend_dt,1)
    dend_dt = dend_dt - datetime.timedelta(days=1)

    dend = int(year_dend+mon_dend)
    idate = int(year_d1+mon_d1)

    segment = 0
    countfiles = 0
    while idate < int(dend):
        if (chunk_size > 0): # chunks in years
            d2 = d1.replace(year=d1.year + chunk_size) - datetime.timedelta(days=1)
        if (chunk_size < 0): # chunks in months
            d2 = add_months(d1, np.abs(chunk_size))
        if (chunk_size == 0): # one chunk for the full record
            nmonths = (12 - int(mon_d1) + 1) + (int(year_dend) - int(year_d1) - 1)*12 + int(mon_dend)
            d2 = add_months(d1, nmonths) - datetime.timedelta(days=1)

        d2_int = int(str(d2.year).zfill(4) + str(d2.month).zfill(2))
        if (d2_int > int(dend)):
            d2 = dend_dt

        d1string = str(d1.year).zfill(4)+str(d1.month).zfill(2)
        d2string = str(d2.year).zfill(4)+str(d2.month).zfill(2)

        fnamestring=d1string+'-'+d2string
        found_d1=False
        found_d2=False


        #---Now loop over files to find the files that contribute to the chunk and the indices for nco
        ifile = countfiles
        #for ifile in np.arange(0,len(alltime),1):
        while (found_d2 == False):
            time_thisfile = alltime[ifile].time
            timestring=[ str(time_thisfile.dt.year.values[i]).zfill(4)+
                         str(time_thisfile.dt.month.values[i]).zfill(2) 
                         for i in np.arange(0,time_thisfile.time.size,1) ]
    
            if (found_d1 == False):
                test = np.isin(d1string, timestring)
                if test:
                    filelist = [ files[ifile] ]
                    sumtimes = alltime[ifile].time.size
                    i = np.argwhere(np.char.find(timestring, d1string) >= 0)
                    i = i.flatten()
                    id1 = i[0]
                    found_d1 = True
            elif ((found_d1 == True) & (found_d2 == False)):
                filelist.append(files[ifile])
                sumtimes = sumtimes + alltime[ifile].time.size
    
            if (found_d2 == False):
                test = np.isin(d2string, timestring)
                if test:
                    i = np.argwhere(np.char.find(timestring, d2string) >= 0)
                    i = i.flatten()
                    id2 = i[0]
                    sumtimes = sumtimes - alltime[ifile].time.size + id2
                    found_d2 = True
                    countfiles = ifile
            ifile = ifile + 1

        with open('./control/files/segment_files_'+str(segment).zfill(4)+'.txt','w') as file:
            for itime in filelist:
                file.write("%s\n" % itime)
    
        with open('./control/files/segment_index_'+str(segment).zfill(4)+'.txt','w') as file:
            file.write("%s\n" % str(id1))
            file.write("%s\n" % str(sumtimes))
            file.write("%s\n" % fnamestring)
        
        d1 = d2 + datetime.timedelta(days=1)
        idate = int(str(d1.year).zfill(4) + str(d1.month).zfill(2))
        segment = segment + 1


#---------------------------------END MONTHLY AVERAGED SCRIPTS--------------------



if __name__ == "__main__":
    main()
