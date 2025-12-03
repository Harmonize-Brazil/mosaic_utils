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

.. image:: docs/source/_static/mosaic_utils_logo.png
   :alt: mosaic_utils logo
   :width: 180px
   :align: right

.. image:: https://img.shields.io/badge/License-GPLv3-green
        :target: https://github.com/Harmonize-Brazil/mosaic_utils/blob/main/LICENSE
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

**mosaic_utils** is a Python package that provides a collection of algorithms and helper functions for processing mosaics generated from drone imagery. It includes tools for handling geospatial metadata, managing sensor-derived information, and performing postprocessing steps commonly required in drone-based mapping workflows.


Documentation
=============

Full documentation is available at:

`https://mosaic_utils.readthedocs.io/en/latest/ <https://mosaic_utils.readthedocs.io/en/latest/>`_

Installation
============

For full installation instructions, please refer to:

`docs/source/installation.rst <docs/source/installation.rst>`_

Obs.: For Windows `click here <https://github.com/Harmonize-Brazil/mosaic_utils/tree/windows>`_.

Usage
=====

Examples, command references and workflows are available in:

`docs/source/usage.rst <docs/source/usage.rst>`_

Quick Start
-----------

Run ``crop_mosaic.py`` to crop a raster using the convex hull of a negative buffer:

.. code-block:: shell

    python crop_mosaic.py \
        --mosaic_image /path/to/mosaic.tif \
        --threshold_area 0.005

Or check all available options:

.. code-block:: shell

    python crop_mosaic.py --help

License
=======

.. admonition::
    Copyright (C) 2025 INPE/HARMONIZE.