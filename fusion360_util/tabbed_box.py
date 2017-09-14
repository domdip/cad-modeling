#!/usr/bin/python3
"""Interacts with Fusion 360 API to create a tabbed box.

Contains a class to create or retrieve sketches.  Contains another to make
Fusion 360 elements from a (geometric) box.

See projects/psu_4mm_acrylic for an example of a Fusion 360
script that uses these classes.

"""

from typing import List

from adsk.core import ValueInput, Point3D
from adsk.fusion import SketchPoint, FeatureOperations

from geometry_util.geometry import Point, Line, Dim
from geometry_util.box import Side


class SketchContainer(object):
    """Creates or retrieves a sketch from the current Fusion 360 document.

    Sketches are created on the XY construction plane of the given root
    component.  A Z offset may be applied (this has not yet been tested).

    The Fusion 360 API ignores document default units, and defaults to cm.
    Desired scaling can be obtained via conv_factor.

    Sketches may be created, retrieved, or extruded via class methods.  Note
    that retrieved sketches don't retrieve the original conversion factor,
    z coordinate, or list of (geometric, non-360-sketchpoint) points.

    Args:
        name (string): Name of the sketch to be drawn or retrieved
        root_comp: Root component of the design
        z_coord (float, optional): z component of sketch objects in cm.
        conv_factor (float, optional): factor to multiply units by before
            creating objects.  Defaults to 0.1 (mm) since 360 default is cm.

    Attributes:
        points: dict from geometric points (used when constructing) to
            Fusion 360 sketchpoints
        sketch: Fusion 360 sketch object
        sketch_points: Fusion 360 object for managing sketch points
        sketch_lines: Fusion 360 object for managing sketch lines
        sketch_circles: Fusion 360 object for managing sketch circles

    """

    def __init__(self, name, root_comp, z_coord=0, conv_factor=0.1):
        self.name = name
        self.root_comp = root_comp
        self.z_coord = z_coord
        self.conv_factor = conv_factor
        self.points = {}
        self.sketch = None
        self.sketch_points = None
        self.sketch_lines = None
        self.sketch_circles = None

    def retrieve(self):
        sketches = self.root_comp.sketches
        existing_sketch = sketches.itemByName(self.name)
        if not existing_sketch:
            raise
        self.sketch = existing_sketch
        self.sketch_points = self.sketch.sketchPoints
        self.sketch_lines = self.sketch.sketchCurves.sketchLines
        self.sketch_circles = self.sketch.sketchCurves.sketchCircles

    def create(self, overwrite=True):
        sketches = self.root_comp.sketches
        if self.name:
            existing_sketch = sketches.itemByName(self.name)
        else:
            existing_sketch = None
        if existing_sketch and not overwrite:
            self.sketch = existing_sketch
        else:
            if existing_sketch:
                existing_sketch.deleteMe()
            xyPlane = self.root_comp.xYConstructionPlane
            self.sketch = sketches.add(xyPlane)
            if self.name:
                self.sketch.name = self.name
            else:
                self.name = self.sketch.name
        self.sketch_points = self.sketch.sketchPoints
        self.sketch_lines = self.sketch.sketchCurves.sketchLines
        self.sketch_circles = self.sketch.sketchCurves.sketchCircles

    def plot_points(self, points: List[Point]) -> List[SketchPoint]:
        """Takes a list of geometric points and returns sketch points, creating
         them if they aren't already present (in this class).

        Args:
            points: list of geometric points

        Returns:
            list of sketch points (same length as input list)

        """
        plotted = []
        for point in points:
            coords = point.coords()
            if coords not in self.points:
                sp = self.new_sketchpoint_from_point(point)
                self.points[coords] = sp
            else:
                sp = self.points[coords]
            plotted.append(sp)
        return plotted

    def new_sketchpoint_from_point(self, point: Point):
        sketch_point = self.sketch_points.add(self.point3d_from_point(point))
        return sketch_point

    def point3d_from_point(self, point: Point):
        return Point3D.create(point.x * self.conv_factor,
                              point.y * self.conv_factor, self.z_coord)

    def plot_line(self, line: Line):
        source, dest = self.plot_points(line.points())
        self.sketch_lines.addByTwoPoints(source, dest)

    def draw_circle_from_2_points(self, corner_1, corner_2):
        """Creates a sketch circle from opposite corners of bounding square.

        Currently there is no check to ensure inputs have same vert/horiz
        distance.  Vertical midpoints are used (so horizontal distance sets the
        diameter).

        Args:
            corner_1: corner of bounding square of desired circle
            corner_2: bounding square corner opposite to corner_1

        """

        # We need to input 2 points on diameter.  So take vertical midpoints
        vert_mid = (corner_1.y + corner_2.y) / 2.0
        diam_1 = Point(corner_1.x, vert_mid)
        diam_2 = Point(corner_2.x, vert_mid)
        point_1 = self.point3d_from_point(diam_1)
        point_2 = self.point3d_from_point(diam_2)
        self.sketch_circles.addByTwoPoints(point_1, point_2)

    def draw_rect_from_2_points(self, corner_1, corner_2):
        """Creates a sketch rectangle from opposite corners."""
        point_1 = self.point3d_from_point(corner_1)
        point_2 = self.point3d_from_point(corner_2)
        self.sketch_lines.addTwoPointRectangle(point_1, point_2)

    def draw_side(self, side: Side, draw_construction):
        """Takes a geometric Side and creates corresponding sketch components

        Note that construction lines on the 360 side are not yet implemented.
        All lines will appear as real sketch lines - the parameter is intended
        for future use.

        Args:
            side: geometric side to be drawn/created
            draw_construction: if false, we ignore construction lines.

        """
        for line in side.all_lines():
            if draw_construction or not line.is_construction:
                self.plot_line(line)

    def extrude(self, thickness: Dim, operation, name_body=False):
        """Extrudes the sketch a specified distance in a specified way.

        This should not be used on sketches with multiple profiles unless care
        is taken to ensure the last profile is the desired one.  Profiles are
        not well-labeled and so inferring the correct profile is application
        dependent.

        Args:
            thickness (Dim): distance to extrude
            operation (FeatureOperations): type of extrusion (e.g., cut or new
                component)
            name_body (bool): if true, assign current sketch name to the new
                body.
        """
        profiles = self.sketch.profiles
        # Take the last profile (arbitrary)
        profile = profiles.item(profiles.count - 1)
        extrudes = self.root_comp.features.extrudeFeatures
        extrude_distance = ValueInput.createByReal(
            thickness.dist * self.conv_factor)
        ext = extrudes.addSimple(profile, extrude_distance, operation)
        if name_body:
            ext.bodies.item(0).name = self.name


class BoxPlotter(object):
    """Utility class for using a geometric box to draw a related box in Fusion
    360.

    Although a box must be supplied, this class may be used primarily for
    retrieving references to sketches of sides.  This is useful when modifying
    cutouts in cases where the rest of the box does not need to be redrawn.

    The Fusion 360 API ignores the document's default units, and defaults to
    cm.  Desired scaling can be obtained via conv_factor.

    Sketches may be created, retrieved, or extruded via class methods.  Note
    that retrieved sketches don't retrieve the original conversion factor,
    z coordinate, or list of (geometric, non-360-sketchpoint) points.

    Args:
        name (string): Name of the sketch to be drawn or retrieved
        root_comp: Root component of the design
        z_coord (float, optional): z component of sketch objects in cm.
        conv_factor (float, optional): factor to multiply units by before
            creating objects.  Defaults to 0.1 (mm) since 360 default is cm.

    Attributes:
        points: dict from geometric points (used when constructing) to
            Fusion 360 sketchpoints
        sketch: Fusion 360 sketch object
        sketch_points: Fusion 360 object for managing sketch points
        sketch_lines: Fusion 360 object for managing sketch lines
        sketch_circles: Fusion 360 object for managing sketch circles

    """
    def __init__(self, app, box, conv_factor=0.1):
        self.app = app
        self.box = box
        self.user_params = app.activeProduct.userParameters
        self.root_comp = app.activeProduct.rootComponent
        self.conv_factor = conv_factor
        self.sketches = {}
        self.cutout_sketches = {}

    # Set a user parameter to a simple Dim name/value
    # Currently unused
    def set_param(self, dim: Dim):
        curVal = self.user_params.itemByName(dim.dist_label)
        if curVal:
            curVal.expression = "{} mm".format(dim.dist)
            return curVal
        else:
            val = ValueInput.createByString("{} mm".format(dim.dist))
            return self.user_params.add(dim.dist_label, val, "mm", "")

    def sketch_sides(self, draw=True, draw_construction=False, overwrite=True):
        for (side_name, side) in self.box.sides().items():
            sketch = SketchContainer(side_name, self.root_comp)
            sketch.create(overwrite=overwrite)
            if draw:
                sketch.draw_side(side, draw_construction)
            self.sketches[side_name] = sketch

    def sketch_cutouts(self, draw_construction=False, overwrite=True):
        for (side_name, side) in self.box.sides().items():
            for cutout in side.cutouts:
                (kind, name, corner_1, corner_2) = cutout
                # TODO: validate cutout type before creating sketch
                sketch = SketchContainer(name, self.root_comp)
                sketch.create(overwrite=overwrite)
                if kind == 'circle':
                    sketch.draw_circle_from_2_points(corner_1, corner_2)
                elif kind == 'rect':
                    sketch.draw_rect_from_2_points(corner_1, corner_2)
                self.cutout_sketches[name] = sketch

    def retrieve(self, sketch_names):
        for side_name in sketch_names:
            sketch = SketchContainer(side_name, self.root_comp)
            sketch.retrieve()
            self.sketches[side_name] = sketch

    def retrieve_sides(self):
        self.retrieve(self.box.sides())

    def extrude_sketch(self,
                       sketch_name,
                       thickness: Dim,
                       operation,
                       name_body=False):
        """Extrudes the sketch a specified distance in a specified way.

        This should not be used on sketches with multiple profiles unless care
        is taken to ensure the last profile is the desired one.  Profiles are
        not well-labeled and so inferring the correct profile is application
        dependent.

        Args:
            thickness (Dim): distance to extrude
            operation (FeatureOperations): type of extrusion (e.g., cut or new
                component)
            name_body (bool): if true, assign current sketch name to the new
                body.
        """
        all_sketches = {**self.sketches, **self.cutout_sketches}
        if sketch_name not in all_sketches:
            raise

        all_sketches[sketch_name].extrude(
            thickness, operation, name_body=name_body)

    def extrude_sides(self, side_names=None):
        """Extrudes a list of sides.

        Sides are extruded a distance equal to the box thickness into new
        components.

        If no side names are passed, all sides are extruded.

        Args:
            side_names: list of side sketch names, or None if all sides should
                be extruded.

        """
        if not side_names:
            side_names = self.box.sides().keys()
        # Extrude sides into new components
        for sketch_name in side_names:
            self.extrude_sketch(
                sketch_name,
                self.box.thickness,
                FeatureOperations.NewComponentFeatureOperation,
                name_body=True)

    def cut_sides(self):
        """Cut-extrudes all cutout features of all sides.

        Cut depth is equal to box thickness to match extrude_sides

        """
        for (name, sketch) in self.cutout_sketches.items():
            self.cut_feature(name, self.box.thickness)

    def cut_feature(self, sketch_name, thickness):
        """Cut-extrudes a single cutout feature.

        Args:
            sketch_name (str): name of sketch to cut with
            thickness (Dim): distance to cut

        """
        self.extrude_sketch(sketch_name, thickness,
                            FeatureOperations.CutFeatureOperation)
