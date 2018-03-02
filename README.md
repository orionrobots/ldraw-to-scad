# ldraw-to-scad
A tool to convert from an LDraw drawing to an Open SCAD CAD file

State: Alpha
Intent: Converting LDraw projects to Open SCAD to render, animate or use for other assemblies.

## Usage

Requires python3, with no external dependancies:

    python ldraw-to-scad.py <ldraw file> <scad file>

Currently it requires the ldraw library in lib/ldraw. It may yet need to honour a setting/environment variable to locate the ldraw library.
It also (naively) expects the ldraw library filenames to be lowercase.

## Testing

Requires pytest, currently references mock but is unnecessary.

## Still missing

* Colours - things get a number but the colour list is not read in, and the colour 16 protocol isn't yet there.
* Multipart Dat - currently in development - the ability to have Lego Dat files with multiple parts in the same file (instead of external file references)
