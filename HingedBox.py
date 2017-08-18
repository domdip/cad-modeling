# -*- coding: utf-8 -*-
"""Interacts with Fusion 360 API to create a parameterized hinge box.

TODO: longer description

Example:
    Examples can be given using either the ``Example`` or ``Examples``
    sections. Sections support any reStructuredText formatting, including
    literal blocks::

        $ python example_google.py

Section breaks are created by resuming unindented text. Section breaks
are also implicitly created anytime a new section starts.

Todo:
    * Long list, tracked elsewhere at the moment

"""
import adsk.core, adsk.fusion, adsk.cam, traceback
from . import box
from adsk.core import ValueInput, Application, Point3D
from adsk.fusion import DimensionOrientations

#Keep track of value in cm as well as parameter name
class Val(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __mul__(self, other):
        return Val(self.name + " * " + str(other), self.value * other)

    def __truediv__(self, other):
        return Val(self.name + " / " + str(other), self.value / other)

    def __neg__(self):
        return Val("-" + self.name, -self.value)

    def __repr__(self):
        return "Val(" + self.name + "," + str(self.value) + ")"


def sketch_point_coords(sp):
    sp_coords = sp.worldGeometry.asArray()
    return tuple(sp_coords[0:3])


class BoxMaker(object):
    def __init__(self):
        self.user_params = Application.get().activeProduct.userParameters
        self.sketch = None
        self.sketch_points = None
        self.__lines = None
        self.origin = None

    def set_param(self, name, value):
        curVal = self.user_params.itemByName(name)
        if curVal:
            curVal.expression = "{} mm".format(value)
            return curVal
        else:
            val = ValueInput.createByString("{} mm".format(value))
            return self.user_params.add(name, val, "mm", "")

    def set_params(self, length, width, height, tab_width, spacing, thickness):
        self.lengthParam = self.set_param("Length", length)
        self.length = Val("Length", length)
        self.widthParam = self.set_param("Width", width)
        self.width = Val("Width", width)
        self.heightParam = self.set_param("Height", height)
        self.height = Val("Height", height)
        self.tabWidthParam = self.set_param("TabWidth", tab_width)
        self.tab_width = Val("TabWidth", tab_width)
        self.thicknessParam = self.set_param("Thickness", thickness)
        self.thickness = Val("Thickness", thickness)

        self.spacingParam = self.set_param("Spacing", spacing)

    def start_sketch(self):
        app = Application.get()
        design = app.activeProduct

        # Get the root component of the active design.
        rootComp = design.rootComponent

        # Create a new sketch on the xy plane.
        sketches = rootComp.sketches
        xyPlane = rootComp.xYConstructionPlane
        self.sketch = sketches.add(xyPlane)
        self.sketch_points = self.sketch.sketchPoints
        self.origin = self.sketch_points.add(Point3D.create(0, 0, 0))

    @property
    def lines(self):
        if (not self.__lines) or (not self.__lines.isValid):
            self.__lines = self.sketch.sketchCurves.sketchLines
        return self.__lines

    def draw_line(self, fromX, fromY, toX, toY):
        self.lines.addByTwoPoints(
            adsk.core.Point3D.create(fromX, fromY, 0),
            adsk.core.Point3D.create(toX, toY, 0))

    def draw_vertical_line(self, fromX, fromY, length, param_constraint=None):
        vert_line = self.lines.addByTwoPoints(
            adsk.core.Point3D.create(fromX, fromY, 0),
            adsk.core.Point3D.create(fromX, fromY + length, 0))
        self.sketch.geometricConstraints.addVertical(vert_line)
        dim = self.sketch.sketchDimensions.addDistanceDimension(
            vert_line.startSketchPoint, vert_line.endSketchPoint,
            adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
            adsk.core.Point3D.create(fromX - 1, fromY + 0.5 * length, 0))
        if param_constraint:
            dim.parameter.expression = param_constraint
        else:
            dim.parameter.expression = str(length)

    def draw_vert(self, source, dist):
        (x, y, z) = sketch_point_coords(source)
        dest = self.sketch_points.add(Point3D.create(x, y + dist.value, z))
        line = self.lines.addByTwoPoints(source, dest)
        self.sketch.geometricConstraints.addVertical(line)
        dim = self.sketch.sketchDimensions.addDistanceDimension(
            source, dest, DimensionOrientations.VerticalDimensionOrientation,
            Point3D.create(x - 1, y + 0.5 * dist.value, z))
        dim.parameter.expression = dist.name
        return dest

    def draw_horiz(self, source, dist):
        (x, y, z) = sketch_point_coords(source)
        dest = self.sketch_points.add(Point3D.create(x + dist.value, y, z))
        line = self.lines.addByTwoPoints(source, dest)
        self.sketch.geometricConstraints.addHorizontal(line)
        dim = self.sketch.sketchDimensions.addDistanceDimension(
            source, dest, DimensionOrientations.HorizontalDimensionOrientation,
            Point3D.create(x + 0.5 * dist.value, y - 1, z))
        dim.parameter.expression = dist.name
        return dest

    def draw_vertical_edge(self, ref_point, notch_width, notch_count,
                           notch_height, smallside):
        coords = sketch_point_coords(ref_point)

        point = self.draw_vert(ref_point, notch_width)
        point = self.draw_horiz(point, notch_height)
        point = self.draw_vert(point, notch_width)

    def closest_odd(self, number):
        '''
        Find and return the closest odd number to the one passed in
        '''
        num = int(float(number) + 0.5)
        closest_odd = None
        if num % 2 == 0:
            closest_odd = num - 1
        else:
            closest_odd = num
        return float(closest_odd)


def run(context):
    ui = None
    try:
        app = Application.get()
        ui = app.userInterface

        box_maker = BoxMaker()
        box_maker.set_params(20, 30, 50, 5, 2, 3)
        box_maker.start_sketch()
        # box_maker.draw_line(0, 0, 100, 20)
        # box_maker.draw_vertical_line(0, 5, 20, "Length")

        box_maker.draw_vertical_edge(box_maker.origin, box_maker.tab_width, 2,
                                     box_maker.thickness, False)

        ui.messageBox('Huh')

        # sketch = box_maker.sketch

        # origin_point = adsk.core.Point3D.create(0, 0, 0)

        # # Draw two connected lines.
        # lines = sketch.sketchCurves.sketchLines
        # line1 = lines.addByTwoPoints(origin_point,
        #                              adsk.core.Point3D.create(3, 1, 0))
        # line2 = lines.addByTwoPoints(line1.endSketchPoint,
        #                              adsk.core.Point3D.create(1, 4, 0))

        # # Draw a rectangle by two points.
        # recLines = lines.addTwoPointRectangle(
        #     adsk.core.Point3D.create(4, 0, 0),
        #     adsk.core.Point3D.create(7, 2, 0))

        # # Use the returned lines to add some constraints.
        # sketch.geometricConstraints.addHorizontal(recLines.item(0))
        # sketch.geometricConstraints.addHorizontal(recLines.item(2))
        # sketch.geometricConstraints.addVertical(recLines.item(1))
        # sketch.geometricConstraints.addVertical(recLines.item(3))
        # sketch.sketchDimensions.addDistanceDimension(
        #     recLines.item(0).startSketchPoint,
        #     recLines.item(0).endSketchPoint,
        #     adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
        #     adsk.core.Point3D.create(5.5, -1, 0))

        # # Draw a rectangle by three points.
        # recLines = lines.addThreePointRectangle(
        #     adsk.core.Point3D.create(8, 0, 0),
        #     adsk.core.Point3D.create(11, 1, 0),
        #     adsk.core.Point3D.create(9, 3, 0))

        # # Draw a rectangle by a center point.
        # recLines = lines.addCenterPointRectangle(
        #     adsk.core.Point3D.create(14, 3, 0),
        #     adsk.core.Point3D.create(16, 4, 0))

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
