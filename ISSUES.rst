=====================================
Related issues and solutions 
=====================================

GDAL import problem
-------------------
ImportError: /home/user/miniconda3/envs/py38/lib/libstdc++.so.6: version `GLIBCXX_3.4.30' not found (required by /lib/libgdal.so.30)

.. tip::

   Find version required and link to current environment:

.. code-block:: shell

     strings /usr/lib/x86_64-linux-gnu/libstdc++.so.6 | grep GLIBCXX_3.4.30
     mv /home/user/miniconda3/envs/py38/lib/libstdc++.so.6 /home/user/miniconda3/envs/py38/lib/libstdc++.so.6_old
     ln -s /usr/lib/x86_64-linux-gnu/libstdc++.so.6 /home/user/miniconda3/envs/py38/lib/libstdc++.so.6

Test GDAL import:

.. code-block:: shell

     python -c "from osgeo import gdal ; print(gdal.__version__)"