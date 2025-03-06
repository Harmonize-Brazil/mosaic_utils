=====================================
mosaic_utils 
=====================================


.. image:: https://img.shields.io/badge/License-GPLv3-green
        :target: https://github.com/Harmonize-Brazil/scripts_drone/blob/master/LICENSE
        :alt: Software License


.. image:: https://readthedocs.org/projects/scripts_drone/badge/?version=latest
        :target: https://scripts_drone.readthedocs.io/en/latest/
        :alt: Documentation Status


.. image:: https://img.shields.io/badge/lifecycle-experimental-orange.svg
        :target: https://www.tidyverse.org/lifecycle/#experimental
        :alt: Software Life Cycle


About
=====

This repository provides a set of scripts to process GeoTiFF (mosaics) from drones images. 

  
Installation
============

**Dependencies**

    Python 3.12.9, Geopandas and GDAL

Build Steps
-----------

**Using a terminal with Git support at Windows (e.g. Git CMD)** [#]_ **, clone the repository and create the virtual environment with the commands below**:

.. code-block:: shell

        git https://github.com/Harmonize-Brazil/mosaic_utils.git
        cd mosaic_utils
        git switch windows
        python -m venv venv
        venv\Scripts\activate.bat

.. [#] See the guide how to install Git in Windows `here <https://github.com/git-guides/install-git#install-git-on-windows>`_.


Ensure you have GDAL installed on the host (``Windows``):
------------------------------------------------------

Make sure you have created a virtual environment and have activated it before starting the next steps:

1. In order to enable numpy-based raster support, libgdal and its development headers must be installed as well as the Python packages numpy, setuptools, and wheel. 
To install the Python dependencies and build numpy-based raster support:

.. code-block:: shell

        python -m pip install --upgrade pip setuptools whell
        pip3 install numpy
2. Download a ``.whl`` file for the GDAL library from `here <https://github.com/cgohlke/geospatial-wheels/releases>`_ (unofficial binary wheels for some geospatial libraries for Python on Windows). Go to ``Assets`` and 
choose the wheel file by name e.g. (GDAL-3.4.3-cp312-cp312-win_amd64.whl) explanation GDAL-VERSION-PYTHON_VERSION-PYTHON_VERSION-OS-ARCHITECTURE.
Install using the command below:

.. code-block:: shell

        pip3 install GDAL-3.4.3-cp312-cp312-win_amd64.whl



Alternative - Using official package available at Pypi (Due to the **complex** nature of GDAL and its components, different bindings may require additional packages and installation steps):
                                                                                                                
   * https://pypi.org/project/GDAL
   


**Install dependencies and requirements**:

.. code-block:: shell

        pip3 install geopandas
    

Usage
============

Run ``crop_mosaic.py`` to crop a raster file based on the convex hull of the negative buffer from the mapped area:

.. code-block:: shell

    python crop_mosaic.py  --mosaic_image /home/user/Desktop/HARMONIZE-Br_Project/src/FieldWorkCampaigns/Mocajuba2023/EscolaOficina_20231107/Mosaic/EscolaOficina_7nov-orthophoto.tif --threshold_area 0.005
    

The Region of Interest (ROI) is delimited by a polygon resulting from vectorizing the valid pixel values ​​of the raster, after that, the algorithm creates a negative buffer
based on ``threshold_area`` that is a percentage of area mapped in meters. Finally, create a cropped raster using the convex hull of the negative buffer, which aims to 
create the final cropped mosaic without the serrated edges.

Or ``--help`` for further information about script options:

.. code-block:: shell

    python crop_mosaic.py --help


License
=======

.. admonition::
    Copyright (C) 2025 INPE/HARMONIZE.
