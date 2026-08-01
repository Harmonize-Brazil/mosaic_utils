..
    This file is part of Python mosaic_utils tool.
    Copyright (C) 2026 HARMONIZE/INPE.

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

**mosaic_utils** requires **Python 3.10 or later**.

All required dependencies are installed automatically via **pip**.
No manual installation of GDAL is required.


Linux
-----

Installing from the GitHub repository
-------------------------------------

1. Clone the repository:

.. code-block:: shell

    git clone https://github.com/Harmonize-Brazil/mosaic_utils.git

2. Enter the project folder:

.. code-block:: shell

    cd mosaic_utils

3. Create a virtual environment:

.. code-block:: shell

    python -m venv venv

4. Activate it:

.. code-block:: shell

    source venv/bin/activate

5. Upgrade pip:

.. code-block:: shell

    pip install --upgrade pip

6. Install the package:

.. code-block:: shell

    pip install -e .

7. Verify the installation:

.. code-block:: shell

    crop-mosaic --help
        

Windows
-------

Installing from GitHub
~~~~~~~~~~~~~~~~~~~~~~

1. Open **PowerShell** and create a virtual environment:

.. code-block:: powershell

    python -m venv mosaic_utils_env

2. Activate the environment:

.. code-block:: powershell

    mosaic_utils_env\Scripts\activate

3. Upgrade pip:

.. code-block:: powershell

    pip install --upgrade pip

4. Install the package:

.. code-block:: powershell

    pip install git+https://github.com/Harmonize-Brazil/mosaic_utils.git

5. Verify the installation:

.. code-block:: powershell

    crop-mosaic --help


Making ``crop-mosaic`` Available from Any Terminal
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the command is not recognized, the directory containing the
installed executable must be added to the Windows **PATH**.

For a virtual environment, the executable is located at:

.. code-block:: text

    C:\path\to\mosaic_utils_env\Scripts

For a standard Python installation, it is typically located at:

.. code-block:: text

    C:\Users\<username>\AppData\Local\Programs\Python\Python312\Scripts


If this directory is not included in the Windows **PATH**, add it by
running PowerShell as the current user:

.. code-block:: powershell

    $scripts = python -c "import sysconfig; print(sysconfig.get_path('scripts'))"
    [Environment]::SetEnvironmentVariable(
        "Path",
        $env:Path + ";" + $scripts,
        "User"
    )

Close and reopen PowerShell, then verify the installation:

.. code-block:: powershell

    where crop-mosaic

Expected output:

.. code-block:: text

    C:\...\Scripts\crop-mosaic.exe

Finally, confirm that the command is available:

.. code-block:: powershell

    crop-mosaic --help


Updating
--------

To update the package:

.. code-block:: shell

    pip install --upgrade mosaic_utils

or, when installed directly from GitHub:

.. code-block:: shell

    pip install --upgrade git+https://github.com/Harmonize-Brazil/mosaic_utils.git


Troubleshooting
---------------

**Command not found**

Make sure that:

* Python 3.10 or newer is installed.
* The virtual environment is activated.
* The Scripts directory is included in the system PATH.
* ``crop-mosaic --help`` runs successfully.

**Permission denied**

Create a clean virtual environment and reinstall the package.

**Outdated pip**

Upgrade pip before installing:

.. code-block:: shell

    python -m pip install --upgrade pip