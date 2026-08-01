Changelog
=========

(unreleased)
------------
*


0.3.0 (2026-07-31)
------------------

* Enable support for BigTIFFs and Windows color terminal
* Replaced convex hull approach with OpenCV contour extraction.
* Improved outer polygon preservation.
* Added validity mask auto-detection.
* Added RGB, multispectral and thermal workflows.
* Improved documentation with processing pipeline illustrations.
* Simplified installation. 

0.2.0 (2026-04-06)
------------------

* Removed dependency on system-level GDAL (osgeo.gdal).
* Replaced GDAL Warp with rasterio-based processing.
* Implemented memory-efficient streaming crop using windowed processing.
* Eliminated full raster loading into memory during crop operations.
* Enabled multi-threaded processing via rasterio environment settings.
* Simplified installation (no GDAL manual installation required).
* Full compatibility with Windows using pip-only installation.
* Updated installation guide to reflect pip-based workflow.
* Updated project dependencies (added pyproj, version constraints).
* Improved classifiers and metadata for PyPI readiness.

0.1.0 (2025-12-05)
------------------

* Convert repository to a Python package.
* Documentation generation based on Sphinx.
* Automatic project versioning using setuptools-git-versioning.
* Creating the mask using multiprocessing based on threads. 
* Using GDAL Warp Options, thereby avoiding handling long strings.
* Implementing output with ANSI colors and time measuring.

0.0.1 (2025-02-01)
------------------

* Initial version.
