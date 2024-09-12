#!/bin/bash

#------------------USER DEFINITIONS----------------------------------
#--User
user=islas

#--account key
account=P04010022

#--Run Name
#runname="b.e23_alpha17f.BLT1850.ne30_t232.098"
#runname="c153_topfix_ne240pg3_FMTHIST_aicn_x01"
#runname="b.e23_alpha17f.BLT1850.ne30_t232.092"
#runname="b.e23_alpha17f.BLTHIST.ne30_t232.092"
runname="b.e30_beta02.BMT1850.ne30_t232.104"
#runname="b.e23_alpha17f.BLT1850.ne30_t232.102"
#runname="b.e30_beta02.BLTHIST.ne30_t232.104"
#runname="b.e30_beta02.BLT1850.ne30_t232.104"
#runname="b.e23_alpha17f.BLTHIST.ne30_t232.092"
#runname="b.e23_alpha17f.BLT1850.ne30_t232.098"

#--Start and End date for time series generation (of the form YYYYMMDD)
#datestart=18500101
#dateend=19911231
#datestart="00010101"
#dateend="02541231"
datestart="00010101"
dateend="01041231"
#datestart="18500101"
#dateend="20131231"
#datestart="00010101"
#dateend="00221231"
#datestart="00010101"
#dateend="02541231"


# Chunk size for time series output
# Chunk size in years if positive i.e., 1 gives a chunk size of 1 year
# Chunk size in months if negative i.e., -1 gives a chunk size of 1 month
chunk=0

#--Location of history files
#basepath="/glade/campaign/cesm/development/cvcwg/cvwg/f.e23.FAMIPfosi.ne0np4.NATL.ne30x8_t13.001_FINAL/RAW/atm/h0/"
#basepath="/glade/derecho/scratch/juliob/archive/c153_ne240pg3_FMTHIST_aicn_x01/atm/regridded/"
#basepath="/glade/derecho/scratch/hannay/archive/b.e23_alpha17f.BLTHIST.ne30_t232.092/atm/hist/"
#basepath="/glade/derecho/scratch/hannay/archive/b.e23_alpha17f.BLT1850.ne30_t232.098/atm/hist/"
basepath="/glade/derecho/scratch/hannay/archive/"$runname"/atm/hist/"
#basepath="/glade/campaign/cgd/amp/juliob/archive/c153_ne30pg3_FMTHIST_x02/atm/regridded/"
#basepath="/glade/derecho/scratch/juliob/archive/c153_topfix_ne240pg3_FMTHIST_aicn_x01/atm/regridded/"
#basepath="/glade/derecho/scratch/hannay/archive/b.e23_alpha17f.BLTHIST.ne30_t232.098b/atm/hist/"

#--String that represents the type of history file.  Will be used to obtain files using ls *.$htype.*
#htype="h0a"
htype="h4a"

#--Scratch space for intermediate files (Note, any files that are in here will get deleted by the scripts)
tempdir="/glade/derecho/scratch/islas/temp/timeseries/"

#--Outpath for time series files
#outpath="/glade/campaign/cesm/development/cvcwg/cvwg/f.e23.FAMIPfosi.ne0np4.NATL.ne30x8_t13.001_FINAL/timeseries/atm/6h_avg/"
#outpath="/glade/campaign/cgd/cas/islas/CESM_DATA/julio_runs/c153_ne240pg3_FMTHIST_aicn_x01/mon/"
outpath="/glade/campaign/cgd/cas/islas/CESM_DATA/CESM3_dev/"$runname"/"
#outpath="/glade/campaign/cgd/cas/islas/CESM_DATA/julio_runs/c153_ne240pg3_FMTHIST_aicn_x01/6hi/"
#outpath="/glade/campaign/cgd/cas/islas/CESM_DATA/CESM3_dev/b.e23_alpha17f.BLTHIST.ne30_t232.098b/"
#outpath="/glade/derecho/scratch/islas/temp/forrich/f.cam6_3_161.FLTHIST_ne30.ke.001/"

#--Specify Variables
# If specified as an empty string the it does all the vairables in the file
#VARS=""
#VARS=( "FSNTC" "TGCLDIWP" "TGCLDLWP" "CLDLOW" "AODVIS" "BURDENBC" "BURDENDUST" "BURDENPOM" "BURDENSEASALT" "BURDENSO4" "BURDENSOA" "CDNUMC" "CLDMED" "FSNT" "SWCF" "TS" "ACTNI" "ACTNL" "ACTREI" "ACTREL" "CLDTOT" "U" "Q" "T" "OMEGA" )
VARS=( "THzm" "UVzm" "UWzm" "Uzm" "VTHzm" "Vzm" "WTHzm" "Wzm" )


#--frequency of field
#--Options: day_avg = daily average
#           mon_avg = monthly average
#           6h_avg = 6 hour averages
freq='mon_avg'

#--The name of the time bounds variable
timebndsvar='time_bounds'

#--The maximum number of resubmits you'd like (preventing runaway jobs that go on forever)
max_resubmit=3

#--Specify as True if looking at zonal mean variables
zmvar=True


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
if [ -f "./pbsfiles/output.log" ] ; then
    rm ./pbsfiles/output.log
fi


if [ "$(ls -A $tempdir)" ] ; then
    rm $tempdir/*
fi

#----Sort out time chunking
qsub -A $account -v runname=$runname,basepath=$basepath,tempdir=$tempdir,datestart=$datestart,dateend=$dateend,chunk=$chunk,freq=$freq,htype=$htype,timebndsvar=$timebndsvar run_sortout_timechunks.pbs
while [[ ! -f ./control/COMPLETE ]] ; do
    echo "Sorting of the time chunks is still running..."$(date) >> ./logs/progress.txt
    sleep 60
done
rm ./control/COMPLETE 

#-----If specifying variables then getting the variable list into a form that works for the pbs script
if [ ! -z $VARS ] ; then
    VARS=$(IFS=_ ; echo "${VARS[*]}")
fi


#-----First Pass
qsub -A $account -v runname=$runname,basepath=$basepath,outpath=$outpath,vars=$VARS,firstpass=True,htype=$htype,zmvar=$zmvar run_tsgen.pbs 
while [[ ! -f ./control/COMPLETE ]] ; do 
    echo "Job is still running..."$(date) >> ./logs/progress.txt 
    sleep 60
done
rm ./control/COMPLETE


#-----Continuation if first pass if it timed out before reaching the end of the variable list
resubmits=0
while [[ -s "./logs/vars.txt" ]] && [ $resubmits -le $max_resubmits ] ; do

     echo $resubmits
     ((resubmits++))
     #---remove any tmp files that exist from previous call
     if ls $outpath/*.tmp 1> /dev/null 2>&1 ; then
        rm $outpath/*.tmp
     fi

     varcontinue=$(head -n 1 ./logs/vars.txt)
     echo "Continuation at var="$varcontinue >> ./logs/progress.txt
     qsub -A $account -v runname=$runname,basepath=$basepath,outpath=$outpath,vars=$VARS,firstpass=False,htype=$htype,zmvar=$zmvar run_tsgen.pbs
     while [[ ! -f ./control/COMPLETE ]] ; do
         echo "Job is still running..."$(date) >> ./logs/progress.txt
         sleep 60
     done
     rm ./control/COMPLETE 
done
