#
# project build script.
#

.PHONY: default install clean list

default:        
	@echo 'mosaic_utils build script'
	@echo
	@echo 'usage: make <target>'
	@echo
	@echo 'Example: make list'

install:
	@echo
	@echo "\nChecking for updates..\n"
	sudo apt-get update -y && sudo apt-get upgrade -y
	@echo
	@echo "\n\nInstaling GDAL libraries and dependencies..\n"
	sudo apt-get install -y g++ 
	sudo apt-get install -y libgdal-dev gdal-bin python3-gdal
	sudo apt-get install -y build-essential
	pip3 install "numpy<2.0"
	export CPLUS_INCLUDE_PATH=/usr/include/gdal
	export C_INCLUDE_PATH=/usr/include/gdal
	pip3 install GDAL==`gdal-config --version`
	python -c "from osgeo import gdal, gdal_array; print(gdal.__version__)"
        
clean:
	@echo 'Cleaning up temporary files'
	find . -name '*.pyc' -type f -exec rm {} ';'
	find . -name '__pycache__' -type d -print | xargs rm -rf
	@echo 'NOTE: you should clean up the following occasionally (by hand)'
	git clean -fdn

list:
	@cat Makefile | grep "^[a-z]" | grep -v "^cat " | awk '{print $$1}' | sed "s/://g"
