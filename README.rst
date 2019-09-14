###################################
Garpy: Make your garmin data yours!
###################################

|PyPI-Versions| |PyPI-Status| |Codacy-Grade| |Travis|

``garpy`` is a simple app used to backup your data from Garmin Connect.


.. code:: sh

    pip install -U garpy

.. warning:: Under development. Stay tuned!

***************
Getting started
***************


``garpy`` requires Python 3.6 or higher on your system. If you are new to Python or have Python 2 installed on your
computer, I recommend you install Miniconda_. To my knowledge, it is
the simplest way of installing a robust and lightweight Python environment.


****************
Acknowledgements
****************

The library is based  on garminexport_. I borrowed the GarminClient and refactored it to my taste.


.. |PyPI-Versions| image:: https://img.shields.io/pypi/pyversions/garpy.svg?logo=python&logoColor=white
   :target: https://pypi.org/project/garpy
.. |PyPI-Status| image:: https://img.shields.io/pypi/v/garpy.svg
   :target: https://pypi.org/project/garpy
.. |Codacy-Grade| image:: https://api.codacy.com/project/badge/Grade/2fbbd268e0a04cd0983291227be53873
   :target: https://app.codacy.com/manual/garpy/garpy/dashboard
.. |Travis| image:: https://api.travis-ci.com/felipeam86/garpy.png?branch=master
    :target: http://travis-ci.com/felipeam86/garpy


.. _Miniconda: https://docs.conda.io/en/latest/miniconda.html
.. _garminexport: https://github.com/petergardfjall/garminexport
