..
    This file is part of Python mosaic_utils tool.
    Copyright (C) 2025 HARMONIZE/INPE.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <https://www.gnu.org/licenses/gpl-3.0.html>.

=====================================
mosaic_utils tool
=====================================

.. image:: https://img.shields.io/badge/License-GPLv3-green
        :target: https://github.com/Harmonize-Brazil/mosaic_utils/blob/windows/LICENSE
        :alt: Software License


.. image:: https://readthedocs.org/projects/mosaic_utils/badge/?version=latest
        :target: https://mosaic_utils.readthedocs.io/en/latest/
        :alt: Documentation Status


.. image:: https://img.shields.io/badge/lifecycle-experimental-orange.svg
        :target: https://www.tidyverse.org/lifecycle/#experimental
        :alt: Software Life Cycle


.. image:: https://img.shields.io/github/tag/Harmonize-Brazil/mosaic_utils.svg
        :target: https://github.com/Harmonize-Brazil/mosaic_utils/releases/latest
        :alt: Release


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

        git clone https://github.com/Harmonize-Brazil/mosaic_utils.git
        cd mosaic_utils
        git switch windows
        python -m venv venv
        venv\Scripts\activate.bat

.. [#] See the guide how to install Git in Windows using an installer `here <https://github.com/git-guides/install-git#install-git-on-windows>`_.


**Ensure you have GDAL installed on the host** (``Windows``):

Make sure you have created a virtual environment and have activated it before starting the next steps:

1. In order to enable numpy-based raster support, libgdal and its development headers must be installed as well as the Python packages numpy, setuptools, and wheel. 
To install the Python dependencies and build numpy-based raster support:

.. code-block:: shell

        python -m pip install --upgrade pip 
        pip3 install --upgrade setuptools wheel
        pip3 install "numpy<2.0"

2. Download a ``.whl`` file for the GDAL library from `here <https://github.com/cgohlke/geospatial-wheels/releases>`_ (unofficial binary wheels for some geospatial libraries for Python on Windows) or use alternative way based on official package available at Pypi [#]_ (complex process to create bindings using compilation in C++).
    * 2.1 At Github page of geospatial-wheels, go to ``Assets`` and choose the wheel file by name e.g. (GDAL-3.4.3-cp312-cp312-win_amd64.whl). The name of file refers on GDAL-VERSION-PYTHON_VERSION-PYTHON_VERSION-OS-ARCHITECTURE.    
    * 2.2 After download, install GDAL using the command below:

.. code-block:: shell

        pip3 install GDAL-3.4.3-cp312-cp312-win_amd64.whl

3. Verify that numpy-based raster support for GDAL has been installed with:

.. code-block:: shell

        python -c "from osgeo import gdal, gdal_array ; print(gdal.__version__)"



.. [#] Alternative - Using official package available at Pypi (Due to the **complex** nature of GDAL and its components, different bindings may require additional packages and installation steps):
                                                                                                                
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

