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


.. image:: https://img.shields.io/github/tag/Harmonize-Brazil/scripts_drone.svg
        :target: https://github.com/Harmonize-Brazil/scripts_drone/releases/latest
        :alt: Release


About
=====

This repository provides a set of scripts to process GeoTiFF (mosaics) from drones images. 

  
Installation (For Windows `click here <https://github.com/Harmonize-Brazil/mosaic_utils/tree/windows>`_)
============

**Dependencies**

    Python 3.12.1, Geopandas and GDAL

Build Steps
-----------

**Clone repository and create Virtual Environment**:

.. code-block:: shell

        git https://github.com/Harmonize-Brazil/mosaic_utils.git
        cd mosaic_utils
        python -m venv venv
        source venv/bin/activate
        pip3 install --upgrade pip setuptools wheel


Ensure you have GDAL installed on the host (``Linux``):
------------------------------------------------------

Using a Makefile, run this command at the terminal:

.. code-block:: shell

        make

Or make step-by-step typing these commands below:

.. code-block:: shell

        sudo apt-get update && sudo apt-get upgrade
        sudo apt-get install -y g++ && sudo apt-get install -y libgdal-dev gdal-bin python3-gdal
        sudo apt-get install build-essential ##This one solves some bugs sometimes
        pip3 install "numpy<2.0"
        export CPLUS_INCLUDE_PATH=/usr/include/gdal
        export C_INCLUDE_PATH=/usr/include/gdal
        pip3 install GDAL==`gdal-config --version`
        python -c "from osgeo import gdal, gdal_array ; print(gdal.__version__)"

Problems with GDAL import, please see these `related issues and solutions <ISSUES.rst>`_!


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
