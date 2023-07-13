# well_point_interpolate

## Introduction

**well_point_interpolate** is a python command line tool for interpolating points (XYZ) from a well trajectory and one or more measured depths. This tool is based heavily on the [well_profile](https://github.com/pro-well-plan/well_profile) package.

## Installation

1. Clone the repository

    ```bash
    git clone https://github.com/nmpeterson/well_point_interpolate.git
    ```

1. Set up the virtual environment (using Python 3.8+)

    ```bash
    cd well_point_interpolate
    python -m venv .venv
    ```

1. Activate the virtual environment

    Windows:

    ```powershell
    .venv\Scripts\activate
    ```

    MacOS/Linux:

    ```bash
    source .venv/bin/activate
    ```

1. Install dependencies

    ```bash
    python -m pip install -r requirements.txt
    ```

1. Once installed, the tool can be called with the virtual environment's Python executable. To view the help, for example:

    ```bash
    python well_point_interpolate.py -h
    ```

## Example Usage

This tool has two required parameters:

1. `md` -- A comma-separated list of one or more measured depths for which to interpolate points

1. `csv` -- A filepath for a CSV file containing well trajectory station data. The following columns must exist:

    - **md** (measured depth, in meters or feet)
    - **inc** (inclination, in degrees)
    - **azi** (azimuth, in degrees)

    Example CSV contents:

    |md|inc |azi        |
    |--|----|-----------|
    | 0|0.00|359.8653226|
    |22|0.11|217.3553226|
    |30|0.23|177.1053226|

The tool may be run with only these two parameters, but the resulting points will only be positioned relative to the initial point (i.e. at md=0, x, y and z will also be set to 0, and other points' coordinates will be relative to that origin). Using the example CSV above, we can get the relative coordinates of a point at MD=10:

```bash
$ python well_point_interpolate.py 10 ~/example.csv
[{"md":10.0,"x":0.002647473177328765,"y":0.003468352936992104,"z":-9.9999987307608}]
```

If you want absolute coordinates for your points, the following additional parameters must be supplied:

1. `-x` (`--x0`) -- X-coordinate (easting) at MD=0
1. `-y` (`--y0`) -- Y-coordinate (northing) at MD=0
1. `-z` (`--z0`) -- Z-coordinate (elevation) at MD=0

The values of the X/Y/Z parameters must all be in the same units (meters or feet) and they should come from a locally-accurate projected coordinate system (e.g. the nearest UTM zone) -- *do not use latitude/longitude values!* (If the elevation at MD=0 is 0, or you are not concerned with having accurate elevation data in the results, the `-z` arg can be omitted.)

```bash
$ python well_point_interpolate.py 10 ~/example.csv -x 488817.3087 -y 5909154.619 -z 42.51
[{"md":10.0,"x":488817.3113474732,"y":5909154.622468353,"z":32.5100012692392}]
```

If the **azi** values in the CSV file need to be systematically adjusted, you can supply the `-a` (`--azi_adj`) parameter. The supplied value should be a positive number (0-360) and will be added to each well trajectory station's **azi** value. This can be useful to convert from True North to Grid North (which is what you should use if supplying X/Y args).

```bash
$ python well_point_interpolate.py 10 ~/example.csv -x 488817.3087 -y 5909154.619 -z 42.51 -a 0.134677422  
[{"md":10.0,"x":488817.3113556184,"y":5909154.62246212,"z":32.5100012692392}]
```

Finally, if you want the results to include latitude/longitude information for each point, you must supply the `-w` (`--wkid`) argument. This is the well-known ID (a.k.a. [EPSG](https://epsg.io) code) of the projected coordinate system your X/Y coordinates use (e.g. UTM zone 15N's WKID is `26915`). When this is supplied, each point interpolated point will include `lat` and `lon` values, giving their [WGS84](https://epsg.io/4326) coordinates.

```bash
$ python well_point_interpolate.py 10 ~/example.csv -w 26915 -x 488817.3087 -y 5909154.619 -z 42.51 -a 0.134677422
[{"md":10.0,"x":488817.3113556184,"y":5909154.62246212,"z":32.5100012692392,"lat":53.3314395589143,"lon":-93.16792011437819}]
```
