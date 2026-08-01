.. image:: _static/mosaic_utils_logo.png
   :width: 220px
   :align: right

Welcome to **mosaic_utils'** documentation
============================================

**mosaic_utils** provides utilities for post-processing orthomosaics
generated from UAV imagery.

Its main application, ``crop-mosaic``, automatically removes invalid
mosaic borders while preserving all raster metadata.

Features
========

* Automatic validity mask detection
* RGB, multispectral and thermal support
* Memory-efficient streaming processing
* Metadata preservation
* Pure Rasterio/OpenCV implementation
* Cross-platform (Linux and Windows)


Contents
========

.. toctree::
   :maxdepth: 2

   installation
   usage
   crop_mosaic
   examples
   api
   authors
   changelog




License
=======

.. admonition::
    Copyright (C) 2026 HARMONIZE/INPE.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.