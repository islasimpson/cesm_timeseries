# cesm_timeseries
Tools for generating single variable timeseries from CESM history files.

<em>Note: this currently only works for monthly, daily or 6 hourly averages atmospheric history files.</em>

How to run:

Set up the specifics of your run within the "USER DEFINITIONS" section of control\_jobs.sh.  These include

1. ``user``: Your user name on CISL machines
2. ``PROJECT``: CISL project number
3. ``runname``: The name of the run you want to generate timeseries files for
4. ``datestart``: the start date for time series generation in the form YYYYMMDD
5. ``dateend``: the end date for time series generation in the form YYYYMMDD
6. ``chunk``: the chunk size for time series output: >0 indicates number of years, <0 indicates number of months, and =0 indicates the full record available
7. ``basepath``: The location of your CESM history files
8. ``htype``: the type of histori file.  Will be used to obtain files using ``ls *.$htype.*``
9. ``tempdir``: scratch space for intermediate files (note any files that are in here will get deleted by the scripts)
10. ``outpath``: the location where you want to output the timeseries files
11. ``VARS``: A optional user defined list of variables for which to generate times series.  If left as a blank string it will do all variables in the files
12. ``freq``: the frequency of output.  Options; day\_avg, mon\_avg, 6h\_avg
13. ``timebndsvar``: the name of the time bounds variable
14. ``max_resubmit``: the maximum number of times you want to resubmit the time series generation if it times out (prevents perpetual runaway jobs)

Then execute the script by...

``./control_jobs.sh``

You might want to do this in a screen session.

For troubleshooting, theres information in 
``./pbsfiles/output.log``
``./logs/warnings.txt``
``./logs/progress.txt``


How it works:
- First ``run_sortout_timechunks.pbs`` is called.  This first grabs the time dimension from all files and makes new files with the same name that only contain the time variable in ``tempdir``.  This then calls the python script ``./control/scripts/sort_timechunks.py`` which figures out which files are needed for each chunk and which start and end index from those files are needed for each chunk.  These are then output to files in ``./control/files/`` which are used in the next stage.
- Then ``run_tsgen.pbs`` is called.  On the first call to this it will generate the file ``./logs/vars.txt`` which contains a list of the variables to be processed.  This will either be the user defined list set in ``control_jobs.sh`` or it will use the python script in ``./control/getvars.py`` to generate the variable list from the contents of the file.  It then loops over these variables, concatenating the relevant files and selecting the relevant index for each chunk.
- Once a variable has been processed, it's removed from the variable list using the python script ``./scripts/cutvarfromlog.py``.
- If ``run_tsgen.pbs`` times out before all variables are complete, it will be resubmitted and will start again at the variable where it left off.
- Note: if the time series file already exists, it won't overwrite it.
