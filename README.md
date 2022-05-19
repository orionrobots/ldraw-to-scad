# ldraw-to-scad
A tool to convert from an LDraw drawing to an Open SCAD CAD file

State: Alpha
Intent: Converting LDraw projects to Open SCAD to render, animate or use for other assemblies.

## Usage

Requires python3, with no external python dependancies:

    python ldraw-to-scad.py <ldraw file> <scad file>

Besides this basic parameters several options are available to generate results either as self-contained OpenSCAD files or relying on an LDraw OpenSCAD library that can be generated with this tool as well. Invoke the tool with the --help option for more information.

By default it requires the ldraw library in lib/ldraw relative to the working directory you run this from. Alternatively you can point the tool to a different location for the libray with the --lib option.
It also (naively) expects the ldraw library filenames to be lowercase.

## Testing

Install the test-requirements.txt file, then run `pytest .`.

## Making animations

This requires a bit of OpenSCAD knowledge.
First - ensure you have clearly separated the sections that will move relative to each other.
You can put them either in one single MPD file or put them in a couple of separate LDraw DAT files.

You can then add the movement transformations. LDraw actually stores matrices that are relative to the parts origin. You will want to wrap these in simple transformations - like translate and rotate.

OpenSCAD has a special variable $t - which is a time offset between 0 and 1. 
You can multiple $t by a value to create movement. You can then enable animation in the window options, and specify a framerate, and the total number of steps in the animation.

This will start OpenSCAD rendering in the preview window.
To start exporting the frames - tick the "Dump Pictures" box under the window.
Warning - "Dump Pictures" will dump the resolution the preview window is in, which may be a bit odd.

You can then use FFMpeg or AVtools to stitch them into a video:

    avconv -framerate 20 -i frame%05d.png -c:v libx264 -r 30 out.mp4

