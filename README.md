# cesm_timeseries
Tools for generating single variable timeseries from CESM history files.

<em>Note: this currently only works for daily averages.  I've also only tested it for a chunk size of 1 year so far - need to test for more</em>

How to run:

Set up the specifics of your run within the "USER DEFINITIONS" section of control\_jobs.sh.  These include

<ol>
<li>`user`: Your user name on CISL machines</li>
<li>``PROJECT``: CISL project number</li>
<li>``runname``: The name of the run you want to generate timeseries files for</li>
<li>``ystart``: the start year for time series generation</li>
<li>``yend``: the end year for time series generation</li>
<li>``chunk``: the chunk size for time series output (only works for integer number of years right now)</li>
<li>``basepath``: The location of your CESM history files</li>
<li>``tempdir``: scratch space for intermediate files (note any files that are in here will get deleted by the scripts)</li>
<li>``outpath``: the location where you want to output the timeseries files</li>
<li>``VARS``: A optional user defined list of variables for which to generate times series.  If left as a blank string it will do all variables in the files</li>
<ol>

Then execute the script by...

``./control_jobs.sh``

You might want to do this in a screen session.

For troubleshooting, theres information in 
``./pbsfiles/output.log``
``./pbsfiles/warnings.txt``
``./pbsfiles/progress.txt``


How it works:
<ol>
<li>First ``run_sortout_timechunks.pbs`` is called.  This first grabs the time dimension from all files and makes new files with the same name that only contain the time variable in ``tempdir``.  This then calls the python script ``./control/scripts/sort_timechunks.py`` which figures out which files are needed for each chunk and which start and end index from those files are needed for each chunk.  These are then output to files in ``./control/files/`` which are used in the next stage.</li>
<li>Then ``run_tsgen.pbs`` is called.  On the first call to this it will generate the file ``./logs/vars.txt`` which contains a list of the variables to be processed.  This will either by the user defined list set in ``control_jobs.sh`` or it will use the python script in ``./control/getvars.py`` to generate the variable list from the contents of the file.  It then loops over these variables, concatenating the relevant files and selecting the relevant index for each chunk.</li>
<li>Once a variable has been processed, it's removed from the variable list using the python script ``./scripts/cutvarfromlog.py``.</li>
<li>If ``run_tsgen.pbs`` times out before all variables are complete, it will be resubmitted and will start again at the variable where it left off.</li>
<li>Note: if the time series file already exists, it won't overwrite it<li>
