## Summary

This repo contains CAD project files and supporting code.  It is oriented around Fusion 360 scripts and supporting Python code.  It is used to programmatically create models within Fusion 360 for the purpose of laser cutting.  The initial model is a tabbed box with cutouts for jacks/cables.

## Code Example

The utility code is designed to make project specification brief and independent of the Fusion 360 API.  For instance, the snippet below is the meat of a script to draw and extrude a tabbed box.

```python
app = Application.get()

box = specify_box()

box_plotter = BoxPlotter(app, box)
box_plotter.sketch_sides()
box_plotter.sketch_cutouts()
box_plotter.extrude_sides()
box_plotter.cut_sides()
```

The function `specify_box()` uses only Python objects to capture the box's geometry.  These objects are interpreted by `BoxPlotter`, which makes the actual Fusion 360 API calls.

## Motivation

Most existing box generators yield output in PDF, SVG, or DXF output.  However, PDF and SVG require lines to have thickness.  Thick lines cause a loss of precision when converted to DXF or passed to CNC tools.  Thin lines present problems for path generation when opened by open source design tools such as Inkscape.  And DXF output is not easily edited by free or open source design tools (Inkscape saves modified DXF files in a buggy manner, and Fusion 360 can 'blow up' when handed complicated DXF files).  Also, the world needs yet another box generator.

Fusion 360 is very useful but complicated sketches require a lot of manual input.  It was chosen in large part because of its support for parameterized modeling.

This motivates the use of the Fusion 360 API.  However, usage of the API can sometimes be laggy and unpredictable.  For instance, a bad import will result in silent failure, and large sketches can cause slowness or crashes.  Hence it is useful to prototype models in pure Python before converting them to corresponding Fusion 360 objects via the API.

The eventual goal of this project is code that generates fully parameterized models with appropriate constraints.  This would combine the rigor of API-generated models with the flexibility of modifying parameters and reshaping models within the Fusion 360 UI.  However, at the moment it does not pass any constraints or parameters to Fusion 360 - all parameter modification must be done within Python, and the script must be re-run to reflect the changes.

[Fusion 360](https://www.autodesk.com/products/fusion-360/students-teachers-educators) is currently available free for non-commercial or limited commercial use.

## Installation and Example Usage

The code has been tested on Python 3.6.2 on OS X.  It uses [type hints](https://docs.python.org/3/library/typing.html), so it probably will not run as-is on Python versions earlier than 3.5.

The utility code has two components.  The first (`geometry_util`) simply takes box specifications and creates Python objects representing the individual components (such as points and lines).  The second (`fusion360_util`) creates objects in Fusion 360 from the Python components.

As a simple usage of `geometry_util`, you can generate a sample tabbed box and plot it using [matplotlib](https://matplotlib.org/faq/installing_faq.html), run:

``python3 geometry_util/box_test.py``

This is useful to validate the user Python environment (which is not needed for Fusion 360 scripting but useful for prototyping).

A sample Fusion 360 script is located in the `projects/psu_4mm_acrylic` directory.  To run it,
1.  Create a new design in Fusion 360
2.  Click Add-Ins, then the green plus sign next to "My Scripts"
3.  Navigate to `projects/psu_4mm_acrylic`
4.  Click "Open" to select the directory.

    `psu_4mm_acrylic` should now appear in your "My Scripts" list.

5.  Click `psu_4mm_acrylic`, then "Run".

    If you zoom out, you should see something like [this](https://github.com/domdip/cad-modeling/raw/master/projects/psu_4mm_acrylic/psu_4mm_acrylic.png "PSU Box Model").

Note that running unknown scripts presents a security risk.  You probably shouldn't do any of the above unless you audit the code or you have a reason to trust me.

## Roadmap

Feature requests and contributions are welcome.  I will otherwise primarily be adding features to support specific projects.  Some low hanging fruit I expect to implement soon:

- Storage of box specifications in Fusion 360 user parameters, so that the code can understand what existing design it is looking at
- An interface to create a box based off of exterior dimensions (instead of deriving interior dimensions and passing those)
- Passing construction lines to Fusion 360
- Passing constraints to Fusion 360
- Some initial parameter modeling (likely around box thickness)
- Cleanup of treatment of box thickness (support for boxes with sides having different thicknesses is only half-implemented at the moment)

## License

MIT License

Copyright (c) [2017] [Dominic DiPalantino]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.