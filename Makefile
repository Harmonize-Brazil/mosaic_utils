# Usage:
# make        # check updates and install dependencies

.PHONY = all

all:
	@echo "\nChecking for updates..\n"
	sudo apt-get update && sudo apt-get upgrade
	@echo "\n\nInstaling GDAL libraries and dependencies..\n"
	sudo apt-get install -y g++ 
	sudo apt-get install -y libgdal-dev gdal-bin python3-gdal
	sudo apt-get install -y build-essential
	pip3 install "numpy<2.0"
	export CPLUS_INCLUDE_PATH=/usr/include/gdal
	export C_INCLUDE_PATH=/usr/include/gdal
	pip3 install GDAL==`gdal-config --version`
	python -c "from osgeo import gdal, gdal_array; print(gdal.__version__)"