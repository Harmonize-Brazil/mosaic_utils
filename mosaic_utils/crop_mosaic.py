#
# This file is part of mosaic_utils package.
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

   This approach is based on Region of interest (ROI) delimitation using pixels with valid values (avoiding NoData) to create a polygon (vectorizing the raster)
   used to crop mosaic using a threshold (%) of the mapped area."""

# --------------------------
#        Imports
# --------------------------
import os
import time
import numpy as np
import rasterio
from rasterio.windows import Window
from rasterio.features import geometry_mask
from rasterio.shutil import copy as rio_copy
from rasterio.features import shapes
from shapely.geometry import shape, mapping, MultiPolygon, Polygon
from shapely.ops import unary_union, transform as shapely_transform
from multiprocessing import Pool, cpu_count
import argparse
from pyproj import Transformer, CRS


""" Settings """
num_workers = int(cpu_count() - (cpu_count() * 0.20)) # using about 80% of cores


# ANSI COLORS
RED     = "\033[91m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
BLUE    = "\033[94m"
MAGENTA = "\033[95m"
CYAN    = "\033[96m"
BOLD    = "\033[1m"
RESET   = "\033[0m"


# --------------------------
#        Functions
# --------------------------
def step(name: str, step_num=None, total_steps=None):
    """
    Start a timed processing step and print a formatted header.

    This function prints a formatted message indicating the start of a
    processing step, optionally including step counters (e.g., "3/10").
    It returns a timestamp that should later be passed to `end()` to
    compute and display the elapsed execution time.

    Args:
        name (str): Descriptive name of the processing step.
        step_num (int, optional): Index of the current step in a sequence.
            If provided, the message is printed in the format
            "[step_num/total_steps] <name>...".
        total_steps (int, optional): Total number of steps in the sequence.
            Required when `step_num` is used.

    Returns:
        float: Timestamp (in seconds since epoch) marking when the step began.
    """
    if step_num != None:
        print(f"\n{RED}{BOLD}[{step_num}/{total_steps}]{CYAN} {name}...{RESET}")
    else:
        print(f"\n{CYAN}=== {name} ==={RESET}")
    return time.time()


def end(t0):
    """
    Finalize a timed processing step and print the elapsed time.

    Calculates the execution time of a previously started step and
    prints it using ANSI-colored formatting.

    Args:
        t0 (float): Timestamp returned by `step()`, representing the
            start time.

    Returns:
        float: Elapsed time for the completed step.
    """
    dt = time.time() - t0
    print(f"{MAGENTA}→ Step time: {dt:.2f} s{RESET}")
    return dt


def reproject_geom(geom, src_crs, dst_crs):
    """
    Reproject a Shapely geometry between two coordinate reference systems.

    Args:
        geom (shapely.geometry.base.BaseGeometry): Input geometry.
        src_crs (str or CRS): Source CRS, in any format supported by
            `pyproj.CRS.from_user_input`.
        dst_crs (str or CRS): Destination CRS.

    Returns:
        shapely.geometry.base.BaseGeometry: The geometry reprojected into
        the destination CRS.

    Raises:
        ValueError: If the source CRS is None.
    """
    if src_crs is None:
        raise ValueError("source CRS is None, cannot reproject geometry")
    if isinstance(src_crs, CRS):
        src = src_crs
    else:
        src = CRS.from_user_input(src_crs)
    dst = CRS.from_user_input(dst_crs)
    if src == dst:
        return geom
    transformer = Transformer.from_crs(src, dst, always_xy=True)
    return shapely_transform(transformer.transform, geom)


def ensure_valid_geometry(geom):
    """
    Ensure a geometry is valid and non-empty, fixing it if necessary.

    Invalid polygons are repaired using a zero-width buffer. MultiPolygon
    objects are cleaned to remove zero-area parts before merging.

    Args:
        geom (shapely.geometry.Polygon or MultiPolygon): Input geometry.

    Returns:
        shapely.geometry.Polygon or MultiPolygon: A valid geometry.

    Raises:
        RuntimeError: If all polygons have zero area after cleaning.
        TypeError: If the input geometry type is not supported.
    """

    # Case geom is Polygon
    if isinstance(geom, Polygon):
        if geom.is_valid and geom.area > 0:
            return geom
        else:
            geom = geom.buffer(0)
            return geom

    # Case geom is MultiPolygon
    if isinstance(geom, MultiPolygon):
        polys = [p for p in geom.geoms if p.area > 0]
        if not polys:
            raise RuntimeError("All polygons have zero area after cleanup.")
        merged = unary_union(polys)
        return merged

    # Any other unexpected type
    raise TypeError(f"Unsupported geometry type: {type(geom)}")


def _shapes_from_tile_alpha(args):
    """
    Extract polygons from the alpha band of a raster tile.

    This worker function is used in parallel processing to extract valid
    polygon shapes from the alpha band (band 4) of a windowed subset of
    the raster.

    Args:
        args (tuple): A tuple containing:
            - path (str): Path to the raster file.
            - window (rasterio.windows.Window): Window region to read.

    Returns:
        list[shapely.geometry.Polygon]: A list of polygons extracted from
        the tile. Returns an empty list if the tile has no valid pixels.
    """
    path, window = args

    with rasterio.open(path) as src:
        # Read ONLY alpha band
        alpha = src.read(4, window=window)

        # Quickly skip completely empty tiles
        if not np.any(alpha):
            return []

        mask = alpha > 0
        transform = src.window_transform(window)

        results = []
        for geom, value in shapes(mask.astype(np.uint8), mask=mask, transform=transform):
            if value == 1:
                results.append(shape(geom))

        return results


def raster_to_polygon_parallel(step_num, total_steps, path, block_size=2048):
    """
    Extract polygons from an RGB(A) raster using only the alpha mask.

    The raster is processed in rectangular tiles, enabling parallel
    processing for large mosaics. Only pixels where the alpha band is
    greater than zero are considered valid.

    Args:
        step_num (int): Index of the current step in a sequence.
        total_steps (int): Total number of steps in the sequence.
        path (str): Path to the raster file.
        block_size (int, optional): Tile size (in pixels) used for
            parallel processing. Defaults to 2048.

    Returns:
        Polygon or MultiPolygon: A merged geometry representing the union
        of all valid polygons extracted from the alpha mask.

    Raises:
        RuntimeError: If no polygons are found or if the cleaned polygon
            list is empty.
    """
    t0 = step("Converting mask to polygons (parallel tiles)",step_num,total_steps)

    
    # Create list of tiles    
    with rasterio.open(path) as src:
        width, height = src.width, src.height
        transform = src.transform

        tiles = []
        for y in range(0, height, block_size):
            for x in range(0, width, block_size):
                w = Window(
                    col_off=x,
                    row_off=y,
                    width=min(block_size, width - x),
                    height=min(block_size, height - y)
                )
                tiles.append((path, w))

    print(f"{YELLOW}→ Tiles to process: {len(tiles)} using {num_workers} cores{RESET}")

    
    # Process tiles in parallel
    polys = []
    with Pool(processes=num_workers) as p:
        for result in p.imap_unordered(_shapes_from_tile_alpha, tiles, chunksize=1):
            if result:
                polys.extend(result)

    if not polys:
        raise RuntimeError("No polygons extracted from raster (alpha mask may be empty).")

    
    # Final cleaning    
    cleaned = []
    for p in polys:
        if p.is_empty or p.area == 0:
            continue
        if not p.is_valid:
            p = p.buffer(0)
        if isinstance(p, (Polygon, MultiPolygon)) and not p.is_empty:
            cleaned.append(p)

    if not cleaned:
        raise RuntimeError("Polygon list empty after cleaning.")

    
    # Merge polygons    
    try:
        merged = unary_union(cleaned)
    except Exception:
        # retry safer
        merged = unary_union([g.buffer(0) for g in cleaned])

    end(t0)
    return merged


def compute_negative_buffer(step_num, total_steps, geom, threshold_area, geom_crs):
    """
    Apply a negative buffer to a geometry based on a percentage of its area.

    The geometry is reprojected to a suitable metric CRS so the buffer
    distance is computed in meters. After buffering, the result is
    reprojected back to the original CRS.

    Args:
        step_num (int): Index of the current step in a sequence.
        total_steps (int): Total number of steps in the sequence.
        geom (Polygon or MultiPolygon): Input geometry in the raster CRS.
        threshold_area (float): Area-based threshold used to compute the
            buffer distance (threshold_area * area / 100).
        geom_crs (str or CRS): CRS of the geometry.

    Returns:
        Polygon or MultiPolygon: Buffered and reprojected geometry.

    Raises:
        ValueError: If CRS is invalid or reprojection fails.
    """
    t0 = step(f"Negative buffer with distance in meters: ({threshold_area} * ROI_area) / 100", step_num, total_steps)
    # For distance calculations use a metric CRS. Choose an appropriate UTM zone or WebMercator
    # Determine a suitable metric CRS: use local UTM from centroid if geom_crs is geographic
    src_crs = CRS.from_user_input(geom_crs)
    metric_crs = None
    if src_crs.is_geographic:
        # choose UTM zone from centroid
        lon, lat = geom.centroid.x, geom.centroid.y
        utm_crs = CRS.from_proj4(f"+proj=utm +zone={int((lon + 180) / 6) + 1} +datum=WGS84 +units=m +no_defs")
        metric_crs = utm_crs
    else:
        # use same CRS if it's already projected
        metric_crs = src_crs

    # reproject geom to metric CRS
    geom_metric = reproject_geom(geom, src_crs, metric_crs)

    # area in metric units (m^2)
    area = geom_metric.area
    # threshold_area provided by the user is expected as a fraction of the total area
    dist = (area * threshold_area) / 100.0

    # buffer negative in meters
    geom_metric_buffered = geom_metric.buffer(-dist, resolution=8)

    # project back to original geom_crs
    buffered_back = reproject_geom(geom_metric_buffered, metric_crs, src_crs)

    # ensure valid
    buffered_back = ensure_valid_geometry(buffered_back)

    end(t0)
    return buffered_back


def fast_convex_hull(step_num, total_steps, geom):
    """
    Compute the convex hull of a geometry with validation.

    Args:
        step_num (int): Index of the current step in a sequence.
        total_steps (int): Total number of steps in the sequence.
        geom (Polygon or MultiPolygon): Geometry for which the convex
            hull is computed.

    Returns:
        Polygon: Valid convex hull geometry.
    """
    t0 = step("Convex hull simplification", step_num, total_steps)
    hull = geom.convex_hull
    hull = ensure_valid_geometry(hull)
    end(t0)
    return hull


def crop_with_mask(step_num, total_steps, input_path, output_path, geom, geom_crs):
    """
    Crop a raster using a geometry as a mask with memory-efficient
    windowed processing, and generate a Cloud Optimized GeoTIFF (COG).

    The raster is processed block-by-block to minimize memory usage.
    A temporary tiled and compressed GeoTIFF is first created, then
    converted into a standards-compliant COG using rasterio's COG driver.

    Args:
        step_num (int): Index of the current step in a sequence.
        total_steps (int): Total number of steps in the sequence.
        input_path (str): Path to the input raster.
        output_path (str): Path to the output COG file.
        geom (Polygon or MultiPolygon): Cropping geometry in raster CRS.
        geom_crs (str or CRS): CRS of the geometry.

    Returns:
        None
    """

    t0 = step("Cropping (streaming mode)...", step_num, total_steps)

    tmp_tif = output_path.replace(".tif", "_tmp.tif")

    with rasterio.Env(GDAL_NUM_THREADS="ALL_CPUS"):

        with rasterio.open(input_path) as src:

            geom_proj = reproject_geom(geom, geom_crs, src.crs)
            geojson_geom = [mapping(geom_proj)]

            profile = src.profile.copy()
            profile.update({
                "tiled": True,
                "blockxsize": 256,
                "blockysize": 256,
                "compress": "DEFLATE",
                "predictor": 2
            })

            with rasterio.open(tmp_tif, "w", **profile) as dst:

                for ji, window in src.block_windows(1):

                    mask_block = geometry_mask(
                        geojson_geom,
                        transform=src.window_transform(window),
                        invert=True,
                        out_shape=(window.height, window.width)
                    )

                    if not mask_block.any():
                        continue

                    data = src.read(window=window)
                    data[:, ~mask_block] = 0

                    dst.write(data, window=window)

    end(t0)

    # ---------------------------------------
    # Convert to true COG
    # ---------------------------------------
    t1 = step("Generating Cloud Optimized GeoTIFF (COG)...", step_num + 1, total_steps)

    rio_copy(
        tmp_tif,
        output_path,
        driver="COG",
        compress="DEFLATE",
        blocksize=256,
        overview_resampling="nearest",
        NUM_THREADS="ALL_CPUS"
    )

    # Remove temporary file
    try:
        os.remove(tmp_tif)
    except Exception:
        pass

    end(t1)


# MAIN PIPELINE
def crop_mosaic_by_polygon(input_file, output_file, threshold):
    """
    Full mosaic cropping pipeline using alpha mask + geometry processing.

    This pipeline:
      1. Extracts polygons from the alpha band.
      2. Computes a negative buffer.
      3. Applies a convex hull.
      4. Validate the convex hull.
      5. Crops the mosaic using RasterIO.

    Args:
        input_file (str): Path to the input mosaic.
        output_file (str): Path where the cropped mosaic will be saved.
        threshold (float): Area-based threshold used for negative buffering.

    Returns:
        None
    """
    total_start = step("Crop Mosaic Pipeline")

    # read transform and CRS
    with rasterio.open(input_file) as src:
        transform = src.transform
        raster_crs = src.crs.to_string()

    total_steps = 6
    # Step 1 – polygon (mask pixels to polygons in raster CRS)
    geom = raster_to_polygon_parallel(1, total_steps, input_file, block_size=2048)

    # Step 2 – negative buffer (computed in metric CRS and converted back)
    nb = compute_negative_buffer(2, total_steps, geom, threshold, raster_crs)

    # Step 3 – convex hull
    hull = fast_convex_hull(3, total_steps,nb)

    # Step 4 - ensure hull is in raster CRS (it already is, but we enforce type)
    t0 = step("Validating convex hull...", 4,total_steps)
    hull = ensure_valid_geometry(hull)
    end(t0)

    # Step 5 and 6 – crop and covert to COG
    crop_with_mask(5, total_steps, input_file, output_file, hull, raster_crs)

    print(f"{GREEN}\nMosaic cropped successfully!\nSaved at: {output_file}{RESET}")

    end(total_start)


# CLI
def main():
    """
    Command-line interface for the crop mosaic tool.

    Parses user arguments, sets the output file, and launches the full
    crop pipeline.

    Returns:
        None
    """
    parser = argparse.ArgumentParser(description="Crop mosaic tool")
    parser.add_argument("--mosaic_image", required=True)
    parser.add_argument("--threshold_area", type=float, required=True)
    parser.add_argument("--raster_output", default=None)

    args = parser.parse_args()

    if args.raster_output is None:
        prefix, ext = os.path.splitext(args.mosaic_image)
        output = prefix + "_cropped" + ext
    else:
        output = args.raster_output

    crop_mosaic_by_polygon(args.mosaic_image, output, args.threshold_area)


if __name__ == "__main__":
    main()
