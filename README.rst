###################################
Garpy: Make your garmin data yours!
###################################

|PyPI-Versions| |PyPI-Status| |Codacy-Grade| |Travis| |Coveralls|

``garpy`` is a simple app used to backup your data from Garmin Connect. It can be used to do incremental
backups of your data from Garmin Connect or to download one specific activity.

********************************
Incremental backup of activities
********************************

The first time you use it, all the activities found on your Garmin Connect account will be downloaded to
the directory that you specify. Afterwards, each time you run the command, only the newly available
activities will be downloaded.

The command is used as follows:

.. code:: sh

    garpy download {backup-dir}

Behind the scenes, this is what will happen:

- `garpy` will prompt you for your password and will then authenticate against Garmin Connect.
- It will first fetch the list of all your activities from garmin.
- It will check which activities have already been backed up on the given `backup-dir`
- It will proceed to download all the missing activities.

************************************
Downloading one activity from its ID
************************************

If you wish to download only one activity or simple you want to refresh an already downloaded activity,
use the '-a/--activity' flag as follows:

.. code:: sh

    garpy download --activity 1674567326 {backup-dir}

This will download the activity in all existing formats to the given `backup_dir`

****************
Full CLI options
****************

For more detailed usage, invoke the '--help' command:

.. code:: sh

    $ garpy download --help
    Usage: garpy download [OPTIONS] [BACKUP_DIR]

      Download activities from Garmin Connect

      Entry point for downloading activities from Garmin Connect. By default, it
      downloads all newly created activities since the last time you did a
      backup.

      If you specify an activity ID with the "-a/--activity" flag, only that
      activity will be downloaded, even if it has already been downloaded
      before.

      If no format is specified, the app will download all possible formats.
      Otherwise you can specify the formats you wish to download with the
      "-f/--formats" flag. The flag can be used several  times if you wish to
      specify several formats, e.g., 'garpy download [OPTIONS] -f original -f
      gpx [BACKUP_DIR]' will download .fit and .gpx files

    Options:
      -f, --formats [tcx|gpx|original|summary|fit|details]
                                      Which formats to download. The flag can be
                                      used several times, e.g. '-f original -f
                                      gpx'
      -u, --username {username}       Username of your Garmin account
      -p, --password {password}       Password of your Garmin account
      -a, --activity {ID}             Activity ID. If indicated, download only
                                      that activity, even if it has already been
                                      downloaded. Otherwise, do incremental update
                                      of backup
      --help                          Show this message and exit.


************
Installation
************
``garpy`` requires Python 3.6 or higher on your system. For those who know your way around with Python, install
``garpy`` with pip as follows:

.. code:: sh

    pip install -U garpy


If you are new to Python or have Python 2 installed on your
computer, I recommend you install Miniconda_. To my knowledge, it is the simplest way of installing a robust and
lightweight Python environment.


****************
Acknowledgements
****************

The library is based on garminexport_. I borrowed the GarminClient, refactored it to my taste and
created a package from it.


.. |PyPI-Versions| image:: https://img.shields.io/pypi/pyversions/garpy.svg?logo=python&logoColor=white
   :target: https://pypi.org/project/garpy
.. |PyPI-Status| image:: https://img.shields.io/pypi/v/garpy.svg
   :target: https://pypi.org/project/garpy
.. |Codacy-Grade| image:: https://api.codacy.com/project/badge/Grade/2fbbd268e0a04cd0983291227be53873
   :target: https://app.codacy.com/manual/garpy/garpy/dashboard
.. |Travis| image:: https://api.travis-ci.com/felipeam86/garpy.png?branch=master
    :target: http://travis-ci.com/felipeam86/garpy
.. |Coveralls| image:: https://coveralls.io/repos/github/felipeam86/garpy/badge.svg?branch=develop
    :target: https://coveralls.io/github/felipeam86/garpy?branch=develop


.. _Miniconda: https://docs.conda.io/en/latest/miniconda.html
.. _garminexport: https://github.com/petergardfjall/garminexport
