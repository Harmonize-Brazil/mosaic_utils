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


Installation
============

This project relies on Python geospatial libraries such as rasterio and geopandas.
All required dependencies are installed automatically via pip.

Linux Installation
------------------

Using a *Python Virtual Environment*:

1. Clone the repository:

.. code-block:: shell

    git clone https://github.com/Harmonize-Brazil/mosaic_utils.git

2. Enter the project folder:

.. code-block:: shell

    cd mosaic_utils

3. Create a virtual environment:

.. code-block:: shell

    python -m venv venv

4. Activate the environment:

.. code-block:: shell

    source venv/bin/activate

5. Upgrade pip:

.. code-block:: shell

    pip install --upgrade pip

6. Install dependencies and package:

.. code-block:: shell

    pip install -e .
        
**Obs.:** This installs the package in development mode, allowing you to modify the code without having to rebuild the package.


Windows Installation
--------------------

Using PowerShell:

1. Create a virtual environment:

.. code-block:: powershell

    python -m venv mosaic_env

2. Activate the environment:

.. code-block:: powershell

    mosaic_env\Scripts\activate

3. Upgrade pip:

.. code-block:: powershell

    pip install --upgrade pip

4. Install the package:

.. code-block:: powershell

    pip install git+https://github.com/Harmonize-Brazil/mosaic_utils.git

5. Test installation:

.. code-block:: powershell

    crop-mosaic --help


-------------------------------------------------
Troubleshooting
-------------------------------------------------

If you encounter issues:

- Ensure Python version is 3.10 or higher
- Use a clean virtual environment
- Upgrade pip before installation

.. code-block:: shell

    pip install --upgrade pip