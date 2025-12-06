Installation
============

This project depends on GDAL, which must be installed at the system level on Linux.
Below are the installation instructions for Ubuntu.


Using a *Python Virtual Environment*:

1. Clone the software repository:

.. code-block:: shell

    git clone https://github.com/Harmonize-Brazil/mosaic_utils.git

2. Go to the source code folder:

.. code-block:: shell

    cd mosaic_utils

3. Create a virtual environment linked to Python:

.. code-block:: shell

    python -m venv venv

4. Activate the new environment:

.. code-block:: shell

    source venv/bin/activate

5. Upgrade the new environment:

.. code-block:: shell
       
    pip3 install --upgrade pip setuptools wheel

6. Using a Makefile to install GDAL bindings based on a custom setup:

.. code-block:: shell

    make install

Problems with GDAL import, please see these `related issues and solutions <../../../ISSUES.rst>`_!

7. Editable install (development):

.. code-block:: bash

    pip3 install -e .
        
**Obs.:** This installs the package in development mode, allowing you to modify the code without having to rebuild the package.