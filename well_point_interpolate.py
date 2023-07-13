#!/usr/bin/env python

import argparse
import json
import logging
import pandas as pd
import pyproj
import well_profile as wp


def get_args() -> argparse.Namespace:
    """Define and parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Interpolate a point along a well trajectory at a given measured depth (MD)",
    )

    parser.add_argument(
        "md",
        help="Measured Depth(s) to return points for. Use commas (,) to separate multiple values.",
    )
    parser.add_argument(
        "csv",
        help=(
            "Path to a CSV file containing well trajectory data."
            " Must contain columns 'md' (measured depth), 'azi' (azimuth), and 'inc' (inclination)."
        ),
    )

    crs_group = parser.add_argument_group()
    crs_group.add_argument(
        "-w",
        "--wkid",
        type=int,
        help="WKID (EPSG code) of spatial reference system used for well X/Y coordinates",
    )
    crs_group.add_argument(
        "-x",
        "--x0",
        type=float,
        help="Well X-coordinate (easting) at MD=0. (Must use the same units as `md`.)",
    )
    crs_group.add_argument(
        "-y",
        "--y0",
        type=float,
        help="Well Y-coordinate (northing) at MD=0. (Must use the same units as `md`.)",
    )
    crs_group.add_argument(
        "-z",
        "--z0",
        type=float,
        help="Well Z-coordinate (elevation) at MD=0. (Must use the same units as `md`.)",
    )
    crs_group.add_argument(
        "-a",
        "--azi_adj",
        type=float,
        help="Azimuth adjustment to add to all well terminals",
    )

    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",  # Returns True if flag is used
        help="Run program in debug mode",
    )
    return parser.parse_args()


def get_logger(log_level: int) -> logging.Logger:
    """"""
    # logging.basicConfig(format="%(levelname)s - %(message)s", level=log_level)
    logger = logging.getLogger("well_point_interpolate")
    logger.setLevel(log_level)
    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


def add_latlon(point: dict, transformer: pyproj.Transformer) -> dict:
    """Calculate a point's WGS84 latitude/longitude from x, y and wkid"""
    try:
        lon, lat = transformer.transform(xx=point["x"], yy=point["y"])
    except TypeError:
        lon = lat = None
    point["lat"] = lat
    point["lon"] = lon
    return point


def main() -> None:
    """Main program logic"""
    # Get arguments
    args = get_args()

    # Initialize logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logger = get_logger(log_level)

    logger.debug(f"md: {args.md}")
    logger.debug(f"csv: {args.csv}")
    logger.debug(f"wkid: {args.wkid}")
    logger.debug(f"x0: {args.x0}")
    logger.debug(f"y0: {args.y0}")
    logger.debug(f"z0: {args.z0}")
    logger.debug(f"azi_adj: {args.azi_adj}")
    logger.debug(f"debug: {args.debug}")

    # Validate args
    logger.debug(f"Parsing args")
    try:
        mds = [float(md) for md in args.md.split(",")]
    except ValueError:
        logger.exception(
            "Could not parse `md` parameter. Expecting comma-delimited list of floats."
        )

    wkid = args.wkid
    x0 = args.x0 if args.x0 else 0
    y0 = args.y0 if args.y0 else 0
    z0 = args.z0 if args.z0 else 0
    azi_adj = args.azi_adj if args.azi_adj else 0

    # Load the well profile data into a pandas df
    logger.debug(f"Loading input CSV into pd.DataFrame")
    well_df = pd.read_csv(args.csv)
    # print(well_df)

    # Verify well profile contains all required columns
    logger.debug(f"Validating columns in input data")
    well_cols = set(well_df.columns)
    required_cols = {"md", "azi", "inc"}
    if missing_cols := required_cols - well_cols:
        err = f"Input well data is missing required columns: {missing_cols}"
        logger.critical(err)
        raise Exception(err)

    # Create a well trajectory from df using well_profile package
    logger.debug(f"Creating well trajectory from input data")
    well = wp.load(
        well_df,
        set_start={"east": x0, "north": y0},
        change_azimuth=azi_adj,
    )

    # Get points at input MDs
    points = []
    for md in mds:
        logger.debug(f"Interpolating point at MD={md}")
        try:
            p = well.get_point(md)
            point = {
                "md": md,
                "x": p["east"],
                "y": p["north"],
                "z": z0 - p["tvd"],  # Subtract because tvd is positive underground
            }
        except ValueError:
            logger.error(f"Could not interpolate point at MD={md}")
            point = {
                "md": md,
                "x": None,
                "y": None,
                "z": None,
            }
        points.append(point)

    # Get WGS84 lat/long (if possible)
    get_latlon = wkid and x0 and y0
    if get_latlon:
        logger.debug(f"Projecting XY coordinates (WKID {wkid}) to WGS84 lat/lon")
        try:
            t = pyproj.Transformer.from_crs(crs_from=wkid, crs_to=4326, always_xy=True)
            points = [add_latlon(p, t) for p in points]
        except pyproj.exceptions.CRSError:
            logger.error(f"Could not create a transformation from WKID {wkid} to WGS84")
    elif wkid:
        logger.warning(
            f"WKID was supplied without x0/y0, so WGS84 lat/lon cannot be determined"
        )

    logger.debug("Processsed points:")
    for point in points:
        logger.debug(f"MD {point['md']}: {point}")

    # Print JSONified points to stdout
    result = json.dumps(points, separators=(",", ":"))
    print(result)


if __name__ == "__main__":
    main()
