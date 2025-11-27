#
# This file is part of mosaic_utils.
# Copyright (C) 2025 HARMONIZE/INPE.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/gpl-3.0.html>.
#
"""Utility for post-processing of mosaics built using drone images, to remove areas affected by deformations (edge areas)

   This approach is based on Region of interest (ROI) delimitation using pixels with valid values (avoiding NoData) to create a polygon (vectorizing the raster) used to crop mosaic 
   using a threshold (%) of the mapped area"""


# --------------------------
#        Imports
# --------------------------
from osgeo import osr, gdal, ogr
import numpy as np
import geopandas as gpd
from shapely.geometry import MultiPolygon, Polygon
from multiprocessing import cpu_count
import subprocess
import os
import sys
import tempfile

""" Settings """
result = subprocess.run(['gdal-config','--datadir'], capture_output=True, text=True)
os.environ['GDAL_DATA'] = result.stdout.replace('\n','') #set gdal data path
os.environ['PROJ_LIB'] = result.stdout.replace('\n','').replace('gdal','proj') #set proj path
gdal.UseExceptions()  # this allows GDAL to throw Python Exceptions
num_workers = int(cpu_count() - (cpu_count() * 0.20)) # using about 80% of cores

# Check version of GDAL with driver that supports the creation of Cloud Optimized GeoTIFF (COG) (Added in version 3.1):
if not tuple([int(i) for i in gdal.__version__.split('.')]) >= (3,1):
    raise RuntimeError('GDAL version requirement for support COG creation is >= 3.1 version installed:{}'.format(gdal.__version__))


# --------------------------
#        Functions
# --------------------------
def get_valid_namefile(src_filename):
    """
    Create a valid filename to save raster cropped by source filename of raster.

    Arguments
    ---------
    src_filename: str
        Input filename of mosaic to crop

    Returns
    ---------
    String with name for output cropped raster of mosaic
    """
    dirname = os.path.dirname(src_filename)
    prefix,suffix = os.path.splitext(os.path.basename(src_filename))
    return os.path.join(dirname,prefix+'_cropped'+suffix)


# Remove inner lines - https://stackoverflow.com/a/70387141
def remove_interiors(poly):
    """
    Close polygon holes by limitation to the exterior ring.

    Arguments
    ---------
    poly: shapely.geometry.Polygon
        Input shapely Polygon

    Returns
    ---------
    Polygon without any interior holes
    """
    if poly.interiors:
        return Polygon(list(poly.exterior.coords))
    else:
        return poly


def pop_largest(gs):
    """
    Pop the largest polygon off of a GeoSeries

    Arguments
    ---------
    gs: geopandas.GeoSeries
        Geoseries of Polygon or MultiPolygon objects

    Returns
    ---------
    Largest Polygon in a Geoseries
    """
    geoms = [g.area for g in gs]
    return gs.pop(geoms.index(max(geoms)))


def close_holes(geom):
    """
    Remove holes in a polygon geometry

    Arguments
    ---------
    gseries: geopandas.GeoSeries
        Geoseries of Polygon or MultiPolygon objects

    Returns
    ---------
    Largest Polygon in a Geoseries
    """
    if isinstance(geom, MultiPolygon):
        ser = gpd.GeoSeries([remove_interiors(g) for g in geom.geoms])
        big = pop_largest(ser)
        outers = ser.loc[~ser.within(big)].tolist()
        if outers:
            return MultiPolygon([big] + outers)
        return Polygon(big)
    if isinstance(geom, Polygon):
        return remove_interiors(geom)

def define_roi(file_in):
    """
    Create the Region Of Interest (ROI), delimited by pixel valid values.

    Arguments
    ---------
    file_in: str
        Input filename of mosaic to delimit the ROI 

    Returns
    ---------
    roi_area_dissolved: geopandas.DataFrame
        Object with a polygon delimiting the ROI 
    """
    src_ds = gdal.Open(str(file_in), gdal.GA_ReadOnly)

    driver = gdal.GetDriverByName('MEM') #To avoid error of overview creation
    dst_ds = driver.Create('', xsize=src_ds.RasterXSize, ysize=src_ds.RasterYSize,
                        bands=1, eType=gdal.GDT_Byte)
    

    # Set projection using source file
    dst_ds.SetGeoTransform(src_ds.GetGeoTransform())
    dst_ds.SetProjection(src_ds.GetProjection())
       
    print('Reading RGB mosaic...')
    arr = src_ds.ReadAsArray()
    arr = arr[0:3,...] #keep only RGB
    nodata = src_ds.GetRasterBand(1).GetNoDataValue()    
    if nodata == None:
        nodata = int(arr[0,0,0])

    arr_out = np.ones([arr.shape[1],arr.shape[2]], dtype=np.int8)
    print('Delimiting the area with valid pixels...')
    arr_out[(arr[0,...] == nodata) & (arr[1,...] == nodata) & (arr[2,...] == nodata)] = 0
    del arr

    # Create a band with mask of valid pixels    
    band = dst_ds.GetRasterBand(1)
    band.WriteArray(arr_out)
    band.SetNoDataValue(nodata)
    band.FlushCache()
    del arr_out
   
    #  Create shapefile with polygon delimiting the ROI
    prefix = os.path.splitext(os.path.basename(file_in))[0]
    with tempfile.TemporaryDirectory() as tmp:
        path_shp = os.path.join(tmp, prefix+'.shp')
        dst_layername = "PolyFtr"
        drv = ogr.GetDriverByName("ESRI Shapefile")
        dst_shp_ds = drv.CreateDataSource(path_shp)
        srs = osr.SpatialReference()
        srs.ImportFromWkt(src_ds.GetProjection()) 
        dst_layer = dst_shp_ds.CreateLayer(dst_layername, srs = srs)
        print('Creating polygon for delimited area...')
        gdal.Polygonize(srcBand=band, maskBand=band, outLayer=dst_layer, iPixValField=-1, options=[], callback=None)
        dst_shp_ds.Destroy()         
        
        # Read the polygon of ROI
        roi_area = gpd.read_file(path_shp)
        roi_area['id'] = 'valid'
        roi_area_dissolved =  roi_area.dissolve(by='id')
        del roi_area

        # Once we're done, close properly the dataset
        src_ds.FlushCache()
        del src_ds
        dst_ds.FlushCache()
        del dst_ds

    # Remove inner lines    
    roi_area_dissolved.geometry = roi_area_dissolved.geometry.apply(lambda p: close_holes(p))

    return roi_area_dissolved
   

def crop_mosaic_by_polygon(file_in,file_out,threshold_area):
    """
    Crop a raster file based on the convex hull of a negative buffer created using the percentage of Region Of Interest (ROI), delimited by pixel valid values.

    Arguments
    ---------
    file_in: str
        Input filename of mosaic to crop
    file_out: str
        Output filename of cropped mosaic
    threshold_area: float
        Input value to create a negative buffer by ROI    

    Returns
    ---------
    None
    """
    prefix = os.path.splitext(os.path.basename(file_in))[0]
    roi_area = define_roi(file_in)
    
    # Create negative buffer to remove deformed borders of image using a threshold based on percentage of ROI in meters:
    # Details about buffer method http://shapely.readthedocs.io/en/latest/manual.html#object.buffer
    roi_area = roi_area.to_crs('EPSG:3395') #to CRS in meters
    roi_area_buffered_negative = roi_area.buffer(-1. *  ((max(roi_area['geometry'].area) * threshold_area) / 100.), resolution=5,single_sided=True)

    with tempfile.TemporaryDirectory() as tmp:
        # Save negative buffer to avoid a final crop with recesses areas:
        path_shp = os.path.join(tmp, prefix+'_negative_buffer.shp') 
        roi_area_buffered_negative.to_file(path_shp)

        print('Cropping the mosaic with a negative buffer from the delimited area...') 
        file_out_tmp = os.path.join(os.path.dirname(file_in), prefix+'_tmp.tif')
        
        dst_output = gdal.Warp(file_out_tmp,file_in, 
                            options="-overwrite -multi -wm 80%  -of COG -cutline {} -crop_to_cutline -co BIGTIFF=YES" \
                                " -wo OPTIMIZE_SIZE=TRUE -co NUM_THREADS={}".format(path_shp,str(num_workers)))    

    roi_area = define_roi(file_out_tmp)
    # Create negative buffer to remove recesses areas of image based on threshold_area of 0.001 of ROI in meters:
    # Details about buffer method http://shapely.readthedocs.io/en/latest/manual.html#object.buffer
    roi_area = roi_area.to_crs('EPSG:3395') #to CRS in meters
    roi_area_buffered_negative = roi_area.buffer(-1. *  ((max(roi_area['geometry'].area) *  0.001) / 100.), resolution=5,single_sided=True)


    with tempfile.TemporaryDirectory() as tmp:
        # Save a convex hull from the negative buffer to avoid a final crop with serrated edges:        
        path_shp = os.path.join(tmp, prefix+'_convex_hull.shp') 
        roi_area_buffered_negative.convex_hull.to_file(path_shp)

        print('Cropping the mosaic with a convex hull from the buffer that delimited the area...')  
        block_size_output = 256 #Sets the tile width and height in pixels. Must be divisible by 16. https://gdal.org/drivers/raster/cog.html#general-creation-options
        dst_output = gdal.Warp(file_out,file_out_tmp, 
                            options="-overwrite -multi -wm 80%  -of COG -cutline {} -crop_to_cutline -co BIGTIFF=YES -co BLOCKSIZE={}" \
                                " -co COMPRESS=DEFLATE -wo OPTIMIZE_SIZE=TRUE -co NUM_THREADS={}".format(path_shp,str(block_size_output),str(num_workers)))
        if os.path.exists(file_out):
            print('\nCrop file created at:\n',file_out)
    os.remove(file_out_tmp) #remove temporary file       


def main(argv):
    if argv.raster_output == None:
        raster_output = get_valid_namefile(argv.mosaic_image)
    else:
        raster_output = argv.raster_output

    crop_mosaic_by_polygon(argv.mosaic_image,raster_output,argv.threshold_area)
 

if __name__ == "__main__":

    # Prompt user for (optional) command line arguments, when run from IDLE:
    if 'idlelib' in sys.modules: sys.argv.extend(input("Args: ").split())

    # Process the arguments
    from argparse import ArgumentParser, SUPPRESS
    import arghelper

    # Disable default help
    parser = ArgumentParser(description='Crop raster file (mosaic) to avoid deformed areas near to edges of image.', add_help=False)
    required = parser.add_argument_group('required arguments')
    optional = parser.add_argument_group('optional arguments')

    # Add back help
    try:          
        required.add_argument('--mosaic_image', type=lambda x: arghelper.is_valid_file(parser, x),
                        help='Path to the mosaic file. Example /home/user/FieldWorkCampaigns/Mocajuba2023/EscolaOficina_20231107/Mosaic/EscolaOficina_7nov-orthophoto.tif',
                            metavar='path_to_file', required=True)
        required.add_argument('--threshold_area',
                        help='Percentage value from area to create a negative buffer of ROI to crop deformed regions. For example 0.005 (value defined in our tests)',
                            metavar='0.005', type=float, required=True)
        optional.add_argument('-h','--help',action='help',default=SUPPRESS,help='show this help message and exit') 
        optional.add_argument('--raster_output', type=lambda x: arghelper.is_valid_namefile(parser, x), 
                              help='COG filename output for cropped mosaic (including path).  \
                                Example /home/user/FieldWorkCampaigns/Mocajuba2023/EscolaOficina_20231107/Mosaic/EscolaOficina_7nov-orthophoto_cropped.tif',
                            metavar='path_to_file')
    except:
        print('\n')
        print(100*'-')
        parser.print_help()
        sys.exit(1)
        
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    sys.exit(main(parser.parse_args()))


    


#filename = "/home/user/Desktop/HARMONIZE-Br_Project/src/FieldWorkCampaigns/Mocajuba2023/EscolaOficina_20231107/Mosaic/EscolaOficina_7nov-orthophoto.tif"
#create_polygon(filename)    

