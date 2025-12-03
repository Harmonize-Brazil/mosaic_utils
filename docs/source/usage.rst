Usage
=====

Mosaic Cropping Utility (crop_mosaic.py)

During the photogrammetric generation of mosaics from drone imagery, it is common for the outer regions of the reconstructed mosaic to present geometric distortions. These artifacts typically arise due to an insufficient number of homogeneous tie points between overlapping images, especially near the edges of the flight area.

To ensure a cleaner and more accurate final product, it is recommended to remove these border regions.
The utility crop_mosaic.py automates this process by clipping the input mosaic using the polygon that defines the mapped area. This results in a final mosaic that contains only properly reconstructed regions, free of edge distortions and artifacts.


Basic example
-------------

.. code-block:: shell

    python crop_mosaic.py --mosaic_image path/to/mosaic.tif --threshold_area 0.005

Output:
    Cropped mosaic saved to: mosaic_cropped.tif


The Region of Interest (ROI) is defined by a polygon generated from vectorizing the valid pixel values of the input raster.
After this step, the algorithm creates a negative buffer based on the value of ``--threshold_area``, which represents a percentage of the mapped area (in square meters).
Finally, the algorithm produces a cropped raster using the convex hull of this negative buffer, ensuring a clean final mosaic without serrated or distorted edges.

For more details about the available parameters, you can use the ``--help`` option:

.. code-block:: shell

    python crop_mosaic.py --help
