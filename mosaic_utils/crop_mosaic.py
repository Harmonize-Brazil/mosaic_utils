#
# This file is part of mosaic_utils package.
# Copyright (C) 2026 HARMONIZE/INPE.
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

"""Utility for post-processing mosaics built using drone images to remove edge areas affected by deformations

   This approach is based on Region of interest (ROI) delimitation using pixels with valid values (avoiding NoData) to create a polygon (vectorizing the raster)
   used to crop mosaic using a threshold (%) of the mapped area."""

# --------------------------
#        Imports
# --------------------------
import os
import sys
import time
import numpy as np
import cv2
import rasterio
from rasterio.transform import xy
from rasterio.windows import Window, from_bounds
from rasterio.features import rasterize
from rasterio.enums import ColorInterp
from shapely.geometry import mapping, MultiPolygon, Polygon, GeometryCollection
from shapely.ops import transform as shapely_transform
from shapely import union_all
from multiprocessing import cpu_count
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


def get_metric_crs(geom, src_crs):
    """
    Return a projected CRS suitable for metric operations.

    If the source CRS is already projected in metres, it is returned
    unchanged. Otherwise, an appropriate UTM CRS is selected
    automatically from the geometry centroid.

    Args:
        geom (BaseGeometry): Input geometry.
        src_crs (CRS): Source coordinate reference system.

    Returns:
        CRS: Projected CRS suitable for metric calculations.
    """
    src_crs = CRS.from_user_input(src_crs)

    # Already projected (typically UTM)
    if (
        src_crs.is_projected
        and src_crs.axis_info
        and src_crs.axis_info[0].unit_name.lower() in ("metre", "meter")
    ):
        return src_crs

    lon = geom.centroid.x
    lat = geom.centroid.y

    zone = max(1, min(60, int((lon + 180) / 6) + 1))

    epsg = 32600 + zone if lat >= 0 else 32700 + zone

    return CRS.from_epsg(epsg)


def maybe_reproject(geom, src_crs, dst_crs):
    """
    Reproject a geometry only when source and destination CRS differ.

    Args:
        geom (BaseGeometry): Input geometry.
        src_crs (CRS): Source CRS.
        dst_crs (CRS): Destination CRS.

    Returns:
        BaseGeometry: Geometry in the destination CRS.
    """
    src_crs = CRS.from_user_input(src_crs)
    dst_crs = CRS.from_user_input(dst_crs)

    if src_crs == dst_crs:
        return geom

    return reproject_geom(geom, src_crs, dst_crs)


def compute_negative_buffer(step_num, total_steps, geom, threshold_area, geom_crs):
    """
    Apply a negative buffer to a geometry based on a percentage of its area.

    The geometry is reprojected to a suitable metric CRS only when the
    source CRS is geographic or uses non-metric units. After buffering,
    the result is transformed back to the original CRS if necessary.

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
    t0 = step(f"Computing negative buffer...", step_num, total_steps)

    # Use a projected CRS to perform distance calculations in metres.
    src_crs = CRS.from_user_input(geom_crs)
    metric_crs = get_metric_crs(geom, src_crs)

    # Reproject to a metric CRS only when required.
    geom_metric = maybe_reproject(geom, src_crs, metric_crs)

    # area in metric units (m^2)
    area = geom_metric.area

    # Empirical buffer distance proportional to the ROI area.
    # This heuristic has been calibrated for drone mosaics.
    distance = (area * threshold_area) / 100.0
    print('Distance (m2):',distance)

    # buffer negative in meters
    geom_metric = geom_metric.buffer(-distance, resolution=8)

    # Reproject back to the original CRS if necessary.
    buffered = maybe_reproject(geom_metric, metric_crs, src_crs)

    # ensure valid
    buffered = ensure_valid_geometry(buffered)

    end(t0)
    return buffered


def ensure_valid_geometry(geom):
    """
    Ensure that a geometry is valid and non-empty.

    Invalid geometries are repaired recursively using a zero-width buffer
    (``buffer(0)``). GeometryCollection objects are reduced to their polygonal
    components.

    Args:
        geom (BaseGeometry): Input geometry.

    Returns:
        Polygon or MultiPolygon: Valid geometry.

    Raises:
        RuntimeError: If the geometry cannot be repaired or contains no
            valid polygonal components.
        TypeError: If the geometry type is unsupported.
    """

    if geom.is_empty:
        raise RuntimeError("Geometry is empty.")

    # Repair invalid geometry.
    if not geom.is_valid:
        repaired = geom.buffer(0)

        if repaired.is_empty:
            raise RuntimeError("Geometry became empty after repair.")

        if repaired.wkb == geom.wkb:
            raise RuntimeError("Unable to repair invalid geometry.")

        return ensure_valid_geometry(repaired)

    # Polygon
    if isinstance(geom, Polygon):
        if geom.area <= 0:
            raise RuntimeError("Polygon has zero area.")
        return geom

    # MultiPolygon
    if isinstance(geom, MultiPolygon):
        polys = [
            p for p in geom.geoms
            if not p.is_empty and p.area > 0
        ]
        if not polys:
            raise RuntimeError("MultiPolygon contains no valid polygons.")

        if len(polys) == len(geom.geoms):
            return geom

        # Some polygons were discarded.
        # Validate the merged result recursively.
        return ensure_valid_geometry(union_all(polys))

    # GeometryCollection
    if isinstance(geom, GeometryCollection):
        polys = [
            g for g in geom.geoms
            if isinstance(g, (Polygon, MultiPolygon))
            and not g.is_empty
            and g.area > 0
        ]
        if not polys:
            raise RuntimeError("GeometryCollection contains no polygonal geometries.")

        return ensure_valid_geometry(union_all(polys))

    raise TypeError(f"Unsupported geometry type: {type(geom).__name__}")


def read_valid_mask(src, mask_threshold=None, mask_band=1):
    """
    Read or derive the validity mask for a raster dataset.

    The function attempts to determine the most appropriate validity mask
    using the following priority:

        1. Alpha band (RGBA imagery);
        2. GDAL dataset mask (NoData or internal mask);
        3. Automatic background detection;
        4. User-defined threshold.

    Args:
        src (rasterio.io.DatasetReader):
            Open Rasterio dataset.

        mask_threshold (float, optional):
            Pixel threshold used to create a validity mask when no alpha
            band or dataset mask is available.

        mask_band (int, optional):
            Raster band used for thresholding.
            Defaults to 1.

    Returns:
        numpy.ndarray:
            Boolean mask where True represents valid pixels.

    Raises:
        RuntimeError:
            If no valid mask can be determined.
    """

    # 1. Alpha band
    if ColorInterp.alpha in src.colorinterp:

        alpha = src.colorinterp.index(ColorInterp.alpha) + 1

        print("Using alpha band as validity mask.")

        return src.read(alpha) > 0

    # 2. GDAL dataset mask
    dataset_mask = src.dataset_mask()

    if dataset_mask.min() == 0 and dataset_mask.max() > 0:

        print("Using GDAL dataset mask.")

        return dataset_mask > 0

    # 3. Automatic background detection
    band = src.read(mask_band)

    finite = band[np.isfinite(band)]

    if finite.size == 0:
        raise RuntimeError("Raster contains no finite values.")

    if finite.min() == 0 and finite.max() > 0:

        print("Automatically detected background value = 0.")

        return band > 0

    # 4. User-defined threshold
    if mask_threshold is None:

        print("\nUnable to determine a validity mask automatically.\n")

        print(f"Raster minimum : {finite.min():.3f}")
        print(f"Raster maximum : {finite.max():.3f}")

        mask_threshold = float(
            input("\nEnter the minimum valid pixel value: ")
        )

    print(
        f"Using threshold {mask_threshold} "
        f"on band {mask_band}."
    )

    return band > mask_threshold


def iter_intersecting_blocks(src, crop_window):
    """
    Yield raster windows intersecting a crop window.

    Instead of iterating over every raster block, this function computes
    directly the block indices intersecting the crop window. Each yielded
    window corresponds only to the portion of a raster block that overlaps
    the crop region, minimizing disk I/O.

    Args:
        src (DatasetReader): Open raster dataset.
        crop_window (Window): Bounding window of the cropping geometry.

    Yields:
        Window: Raster window intersecting the crop area.

    Raises:
        RuntimeError: If raster bands do not share the same block layout.
    """

    if len(set(src.block_shapes)) != 1:
        raise RuntimeError(
            "Raster bands use different block layouts."
        )

    block_height, block_width = src.block_shapes[0]

    first_row = int(crop_window.row_off // block_height)
    last_row = int(
        (crop_window.row_off + crop_window.height - 1)
        // block_height
    )

    first_col = int(crop_window.col_off // block_width)
    last_col = int(
        (crop_window.col_off + crop_window.width - 1)
        // block_width
    )

    for row in range(first_row, last_row + 1):

        row_off = row * block_height
        height = min(block_height, src.height - row_off)

        for col in range(first_col, last_col + 1):

            col_off = col * block_width
            width = min(block_width, src.width - col_off)

            block = Window(
                col_off=col_off,
                row_off=row_off,
                width=width,
                height=height,
            )

            #
            # IMPORTANT:
            # return only the useful portion of the block
            #
            yield block.intersection(crop_window)


def crop_with_mask(step_num, total_steps, input_path, output_path, geom, geom_crs):
    """
    Crop a raster using block-wise streaming.

    The cropping geometry is rasterized only once into a binary mask.
    During processing, each raster block reuses the corresponding slice
    of this mask, avoiding repeated geometry rasterization.

    Args:
        step_num (int): Current processing step.
        total_steps (int): Total number of processing steps.
        input_path (str): Input raster.
        output_path (str): Output raster.
        geom (Polygon or MultiPolygon): Cropping geometry.
        geom_crs (CRS): Geometry CRS.

    Returns:
        None
    """

    t0 = step("Cropping the mosaic...", step_num, total_steps)

    with rasterio.Env(GDAL_NUM_THREADS=num_workers):
        with rasterio.open(input_path) as src:
            # Reproject geometry if necessary
            geom = maybe_reproject(geom, geom_crs, src.crs)
            
            # Bounding window of the ROI
            crop_window = from_bounds(*geom.bounds, transform=src.transform)

            crop_window = (crop_window.round_offsets().round_lengths())
            
            # Output profile
            profile = src.profile.copy()

            profile.update(
                width=int(crop_window.width),
                height=int(crop_window.height),
                transform=src.window_transform(crop_window),
            )

            # Rasterize the polygon
            crop_mask = rasterize(
                [(mapping(geom), 1)],
                out_shape=(
                    int(crop_window.height),
                    int(crop_window.width),
                ),
                transform=src.window_transform(crop_window),
                fill=0,
                dtype="uint8",
            ).astype(bool)


            # Streaming copy
            with rasterio.open(output_path, "w", **profile) as dst:

                # Dataset metadata
                dst.update_tags(**src.tags())

                # Band descriptions
                for i, desc in enumerate(src.descriptions, start=1):
                    if desc:
                        dst.set_band_description(i, desc)

                # Color interpretation
                dst.colorinterp = src.colorinterp

                # Bands metadata
                for i in range(1, src.count + 1):
                    dst.update_tags(i, **src.tags(i))

                # Preserve the source NoData value if it exists
                nodata = src.nodata
                if nodata is None:
                    nodata = 0

                for window in iter_intersecting_blocks(src, crop_window):

                    # Read source data
                    data = src.read(window=window)

                    # Window position inside crop_mask
                    row0 = int(window.row_off - crop_window.row_off)
                    row1 = row0 + int(window.height)

                    col0 = int(window.col_off - crop_window.col_off)
                    col1 = col0 + int(window.width)

                    # Slice the already-rasterized mask
                    mask_window = crop_mask[
                        row0:row1,
                        col0:col1,
                    ]

                    # Set pixels outside the ROI
                    data[:, ~mask_window] = nodata

                    # Destination coordinates
                    dst_window = Window(
                        col_off=col0,
                        row_off=row0,
                        width=window.width,
                        height=window.height,
                    )

                    # Write every window, including windows completely outside the polygon.
                    dst.write(data, window=dst_window)

    end(t0)


def outer_polygon_from_mask(step_num, total_steps, mask, transform, erosion_pixels=3, simplify_pixels=2.0, min_area_pixels=100):
    """
    Extract the outer polygon of a raster mask using OpenCV.

    The mask is slightly eroded before contour extraction so the resulting
    polygon is guaranteed to lie inside the valid raster region. Only the
    largest external contour is retained.

    Args:
        step_num (int): 
            Current processing step.

        total_steps (int):
            Total number of processing steps.

        mask (numpy.ndarray):
            Boolean validity mask (True = valid pixels).

        transform (Affine):
            Raster affine transform.

        erosion_pixels (int, optional):
            Number of erosion iterations.
            Defaults to 3.

        simplify_pixels (float, optional):
            Douglas–Peucker tolerance in pixels.
            Set to 0 to disable contour simplification.

        min_area_pixels (float, optional):
            Ignore contours smaller than this area.

    Returns:
        Polygon:
            Valid polygon representing the outer boundary.

    Raises:
        RuntimeError:
            If no suitable contour is found.
    """
    t0 = step("Extracting and simplifying the outer polygon of a raster mask...", step_num, total_steps)

    # Convert to OpenCV binary image
    img = mask.astype(np.uint8) * 255

    # Create a small artificial border so contours touching the raster edge become closed.
    padding = erosion_pixels + 2

    img = cv2.copyMakeBorder(img, padding, padding, padding, padding, cv2.BORDER_CONSTANT, value=0)

    # Slightly shrink the mosaic.
    kernel = np.ones((3, 3), np.uint8)

    img = cv2.erode(img, kernel, iterations=erosion_pixels)

    # External contours only.
    contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        raise RuntimeError("No contour found.")

    # Remove tiny contours.
    contours = [
        c for c in contours
        if cv2.contourArea(c) >= min_area_pixels
    ]

    if not contours:
        raise RuntimeError("No contour larger than minimum area.")

    # Largest contour.
    contour = max(contours, key=cv2.contourArea)

    # Douglas–Peucker simplification.
    if simplify_pixels > 0:

        epsilon = float(simplify_pixels)

        contour = cv2.approxPolyDP(contour, epsilon, closed=True)

    # Convert to map coordinates.
    coords = []

    for p in contour[:, 0]:

        col = int(p[0]) - padding
        row = int(p[1]) - padding

        x, y = xy(
            transform,
            row,
            col,
            offset="center",
        )

        coords.append((x, y))

    # Explicitly close the ring.
    if coords[0] != coords[-1]:
        coords.append(coords[0])

    poly = Polygon(coords)

    end(t0)

    return ensure_valid_geometry(poly)


# --------------------------
# MAIN PIPELINE
# --------------------------
def crop_mosaic_by_polygon(input_file, output_file, threshold_area, mask_threshold, mask_band):
    """
    Crop a mosaic using a validity mask and geometry-based processing.

    The processing pipeline performs the following steps:

        1. Build a validity mask from the raster (alpha band, GDAL mask,
           NoData, or a user-defined threshold).
        2. Extract and simplifly the outer polygon from the mask.
        3. Compute a negative buffer.
        4. Crop the mosaic using Rasterio.

    Args:
        input_file (str): Path to the input raster mosaic.
        output_file (str): Path to the output cropped raster.
        threshold (float): Area percentage used to compute the negative
            buffer distance.
        mask_threshold (float | None): Pixel value threshold used to
            identify valid pixels when a validity mask cannot be
            determined automatically. If ``None``, the threshold may be
            inferred automatically or requested interactively.
        mask_band (int | None): Raster band used to generate the validity
            mask. If ``None``, the function automatically selects the most
            appropriate source (alpha band, GDAL mask, or the first band).

    Returns:
        None
    """
    total_start = step("Crop Mosaic Pipeline")
    total_steps = 4  

    # read transform, CRS and mask
    with rasterio.open(input_file) as src:
        transform = src.transform
        raster_crs = src.crs.to_string()
        print('Source NoData:',src.nodata)

        # Step 1 – build a validity mask from the raster
        t0 = step("Reading or deriving a binary validity mask...", 1, total_steps)
        mask = read_valid_mask(src, mask_threshold, mask_band)
        end(t0)

    # Step 2 – extract the outer polygon of a raster mask using OpenCV.
    geom = outer_polygon_from_mask(2, total_steps, mask, transform, erosion_pixels=3)

    # Step 3 – compute a negative buffer (computed in metric CRS and converted back)
    geom = compute_negative_buffer(3, total_steps, geom, threshold_area, raster_crs)

    # Step 4 – crop the mosaic using RasterIO
    crop_with_mask(4, total_steps, input_file, output_file, geom, raster_crs)

    print(f"{GREEN}\nMosaic cropped successfully!\nSaved at: {output_file}{RESET}")

    end(total_start)

# --------------------------
# CLI
# --------------------------
def main():
    """
    Command-line interface for the crop mosaic tool.

    Parses user arguments, sets the output file, and launches the full
    crop pipeline.

    Returns:
        None
    """
    try:
        from colorama import just_fix_windows_console
        just_fix_windows_console()
    except ImportError:
        pass

    # Disable default help
    parser = argparse.ArgumentParser(description="Crop GeoTIFF mosaics by automatically detecting the mapped area, \
                                     applying morphological filtering, generating a convex hull with an optional \
                                     negative buffer, and producing a clean cropped raster while preserving the \
                                     original raster characteristics.", add_help=False)
    required = parser.add_argument_group('required arguments')
    optional = parser.add_argument_group('optional arguments')

    # Add back help
    optional.add_argument('-h','--help',action='help',default=argparse.SUPPRESS,help='show this help message and exit') 
    
    required.add_argument("--mosaic_image", required=True)
    required.add_argument("--threshold_area", type=float, required=True, help=(
        "Empirical percentage of the mapped area used to compute the negative buffer "
        "distance. Increase this value to remove more irregular border artifacts; "
        "decrease it to preserve more of the original mosaic boundary. "
        "Default: 0.005. "))
    
    optional.add_argument("--raster_output", default=None)
    optional.add_argument("--mask_threshold", type=float, default=None, help=(
        "Threshold used to identify valid pixels when the raster "
        "does not contain an alpha band or NoData mask."
    ))
    optional.add_argument("--mask_band", type=int, default=1, help=(
        "Band used to build the validity mask when "
        "--mask-threshold is specified."
    ))

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    if args.raster_output is None:
        prefix, ext = os.path.splitext(args.mosaic_image)
        output = prefix + "_cropped" + ext
    else:
        output = args.raster_output

    crop_mosaic_by_polygon(args.mosaic_image, output, args.threshold_area, args.mask_threshold, args.mask_band)


if __name__ == "__main__":
    main()
