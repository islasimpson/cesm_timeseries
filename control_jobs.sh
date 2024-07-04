#!/bin/bash

#------------------USER DEFINITIONS----------------------------------
#--User
user=islas

#--account key
account=P93300313

#--Run Name
runname="f.e23.FAMIPfosi.ne0np4.NATL.ne30x8_t13.001"

#--Start and End date for time series generation (of the form YYYYMMDD)
datestart=19580101
dateend=19651231

# Chunk size for time series output
# Chunk size in years if positive i.e., 1 gives a chunk size of 1 year
# Chunk size in months if negative i.e., -1 gives a chunk size of 1 month
chunk=1

#--Location of history files
basepath="/glade/campaign/cesm/development/cvcwg/cvwg/f.e23.FAMIPfosi.ne0np4.NATL.ne30x8_t13.001_FINAL/RAW/atm/h1/"

#--Scratch space for intermediate files (Note, any files that are in here will get deleted by the scripts)
tempdir="/glade/derecho/scratch/islas/temp/RRAtlantic/"

#--Outpath for time series files
#outpath="/glade/campaign/cesm/development/cvcwg/cvwg/f.e23.FAMIPfosi.ne0np4.NATL.ne30x8_t13.001_FINAL/timeseries/atm/day/"
outpath="/glade/derecho/scratch/islas/processed/RRAtlantic/atm/day/"

#--Specify Variables
# If specified as an empty string the it does all the vairables in the file
#VARS=""
VARS=( "PSL" )

#--frequency of field
#--Options: day_avg = daily average
#           mon_avg = monthly average
freq='mon_avg'


#-----------------END USER DEFINITIONS-------------------------------

#----Clean up any previous COMPLETE files from previous executions
if [ -f "./control/COMPLETE" ] ; then
    rm ./control/COMPLETE
fi 

#----Make required directories if they don't exist
if [ ! -d ./pbsfiles ] ; then
    mkdir pbsfiles
fi

if [ ! -d ./logs ] ; then
    mkdir ./logs
fi
if [ ! -d ./control/files ] ; then
    mkdir ./control/files
fi

#----Clean up any previous control files from previous executions
if [ "$(ls -A ./control/files)" ] ; then 
    rm ./control/files/*
fi

if [ -f "./logs/allvars.txt" ] ; then 
    rm ./logs/allvars.txt
fi
if [ -f "./logs/vars.txt" ] ; then
    rm ./logs/vars.txt
fi

if [ "$(ls -A $tempdir)" ] ; then
    rm $tempdir/*
fi

#----Sort out time chunking
qsub -A $account -v runname=$runname,basepath=$basepath,tempdir=$tempdir,datestart=$datestart,dateend=$dateend,chunk=$chunk,freq=$freq run_sortout_timechunks.pbs
while [[ ! -f ./control/COMPLETE ]] ; do
    echo "Sorting of the time chunks is still running..."$(date) >> ./logs/progress.txt
    sleep 60
done
rm ./control/COMPLETE 

exit

#-----First Pass
qsub -A $account -v runname=$runname,basepath=$basepath,outpath=$outpath,vars=$VARS,firstpass=True run_tsgen.pbs 
while [[ ! -f ./control/COMPLETE ]] ; do 
    echo "Job is still running..."$(date) >> ./logs/progress.txt 
    sleep 60
done
rm ./control/COMPLETE

#-----Continuation if first pass if it timed out before reaching the end of the variable list
while [[ -s "./logs/vars.txt" ]] ; do

     #---remove any tmp files that exist from previous call
     if ls $outpath/*.tmp 1> /dev/null 2>&1 ; then
        rm $outpath/*.tmp
     fi

     varcontinue=$(head -n 1 ./logs/vars.txt)
     echo "Continuation at var="$varcontinue >> ./logs/progress.txt
     qsub -A $account -v runname=$runname,basepath=$basepath,outpath=$outpath,vars=$VARS,firstpass=False run_tsgen.pbs
     while [[ ! -f ./control/COMPLETE ]] ; do
         echo "Job is still running..."$(date) >> ./logs/progress.txt
         sleep 60
     done
     rm ./control/COMPLETE 
done
