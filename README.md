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

## Making animations

This requires a bit of OpenSCAD knowledge.
First - ensure you have clearly separated the sections that will move relative to each other.
For now - until there is mpd support, that means putting them in a couple of separate LDraw DAT files.

You can then add the movement transformations. LDraw actually stores matrices that are relative to the parts origin. You will want to wrap these in simple transformations - like translate and rotate.

OpenSCAD has a special variable $t - which is a time offset between 0 and 1. 
You can multiple $t by a value to create movement. You can then enable animation in the window options, and specify a framerate, and the total number of steps in the animation.

This will start OpenSCAD rendering in the preview window.
To start exporting the frames - tick the "Dump Pictures" box under the window.
Warning - "Dump Pictures" will dump the resolution the preview window is in, which may be a bit odd.

You can then use FFMpeg or AVtools to stitch them into a video:

    avconv -framerate 20 -i frame%05d.png -c:v libx264 -r 30 out.mp4

