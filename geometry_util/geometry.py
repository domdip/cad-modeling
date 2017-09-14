#!/usr/bin/python3
from typing import Union

"""
Object models that act as containers for data needed to create sketch
primitives in Fusion 360.

These may be used simply as containers for the underlying information (e.g.,
using Point simply to contain coordinates).  They also contain utility
functions to generate new objects from existing ones.

These classes are Python object models.  They do not depend on the
Fusion 360 API.

"""

# pylint: disable=too-few-public-methods,C0111,C0103,R0913


class Dim(object):
    """Corresponds to a 'dimension' -  a distance with an optional
    label.

    The labels are informational right now - the intended future use is that
    they will be passed to 360 so that object dimensions are specfied by user
    parameters.  Alternatively in some cases, user paramters will be generated
    from Dim object labels.

    Operator overloading is employed to make arithmetic elsewhere easier. Not
    all operators are implemented yet, or implemented for 'other' types.

    Negative dimensions may be used for arithmetic purposes but are not
    properly represented in 360 by themselves.

    Args:
        dist (float): amplitude/distance represented by object
        dist_label: optional user parameter forumla associated with the object

    """

    def __init__(self, dist: float, dist_label=None):
        self.dist = dist
        self.dist_label = dist_label

    def __str__(self):
        return str(self.dist)

    def __add__(self, other: Union[float, 'Dim']):
        if isinstance(other, Dim):
            if self.dist_label and other.dist_label:
                new_label = self.dist_label + " + {}".format(other.dist_label)
            else:
                new_label = None
            return Dim(self.dist + other.dist, new_label)
        else:
            new_label = self.dist_label + " + {}".format(
                other) if self.dist_label else None
            return Dim(self.dist + other, new_label)

    def __radd__(self, other):
        return self.__add__(other)

    def __mul__(self, other):
        new_label = "({} * {})".format(self.dist_label,
                                       other) if self.dist_label else None
        return Dim(self.dist * other, new_label)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        new_label = "({} / {})".format(self.dist_label,
                                       other) if self.dist_label else None
        return Dim(self.dist / other, new_label)

    def __neg__(self):
        new_label = "-({})".format(
            self.dist_label) if self.dist_label else None
        return Dim(-self.dist, new_label)


class Point(object):
    """Represents a point (or vector) in the x-y plane.

    Contains utility functions to generate other points or lines, or apply
    geometric transformations.

    Args:
        x (float): x-coordinate
        y (float): y-coordinate
        is_fixed (bool, optional): whether the corresponding sketchpoint is
            'fixed' to the plane in Fusion 360.  Not yet used.

    """
    def __init__(self, x: float, y: float, is_fixed=False):
        self.x = x
        self.y = y
        self.is_fixed = is_fixed

    def __str__(self):
        return "({},{})".format(self.x, self.y)

    def draw_horiz(self, dist_x: Dim, is_construction=False):
        """Creates a horizontal line from this point and a dimension.

        is_construction is currently used to filter out lines that should not
        be drawn (not yet passed to Fusion 360 elsewhere).

        Args:
            dist_x (Dim): x-distance from this point to create other line
                endpoint.
            is_construction (bool, optional): whether to mark the line as
                'construction'

        """

        dest = Point(self.x + dist_x.dist, self.y)
        return Line(self, dest, is_construction, dist_x)

    def draw_vert(self, dist_y: Dim, is_construction=False):
        """Creates a vertical line from this point and a dimension.

        Args:
            dist_y (Dim): y-distance from this point to create other line
                endpoint.
            is_construction (bool, optional): whether to mark the line as
                'construction'

        """
        dest = Point(self.x, self.y + dist_y.dist)
        return Line(self, dest, is_construction, dist_y)

    def coords(self):
        """Return tuple containing point's coordinates."""
        return (self.x, self.y)

    def rotate(self, degrees_in: int, around: 'Point'):
        """Rotates the point (in-place) counter clockwise around a given point.

        Currently only supports multiples of 90 degrees.

        Args:
            degrees_in (int): number of degrees to rotate point.
            around (Point): point around which to rotate

        """
        assert (degrees_in % 90 == 0)
        degrees = degrees_in % 360
        ox, oy = around.coords()
        px, py = self.coords()

        cos = {0: 1, 90: 0, 180: -1, 270: 0}[int(degrees)]
        sin = {0: 0, 90: 1, 180: 0, 270: -1}[int(degrees)]

        self.x = ox + cos * (px - ox) - sin * (py - oy)
        self.y = oy + sin * (px - ox) + cos * (py - oy)

    def relative_to(self, other: 'Point'):
        """Returns a new point offset by a given Point vector."""
        new_x = self.x + other.x
        new_y = self.y + other.y
        return Point(new_x, new_y)

    def midpoint(self, other: 'Point'):
        """Returns a point with coordinates equal to the midpoint of this point
        and a given point."""
        new_x = (self.x + other.x) / 2.0
        new_y = (self.y + other.y) / 2.0
        return Point(new_x, new_y)


class Line(object):
    """Represents a line defind by two points.

    Contains utility functions to generate other lines, or apply
    geometric transformations.

    is_construction is currently used to filter out lines that should not
    be drawn (not yet passed to Fusion 360 elsewhere).

    Args:
        source (Point): endpoint of line
        dest (Point): other endpoint
        is_fixed (bool, optional): whether the corresponding sketchpoint is
            'fixed' to the plane in Fusion 360.  Not yet used.
        is_construction (bool, optional): whether to mark the line as
            'construction'
        length (Dim, optional): dimension corresponding to length of line

    """

    def __init__(self,
                 source: Point,
                 dest: Point,
                 is_construction=False,
                 length=None):
        self.source = source
        self.dest = dest
        self.is_construction = is_construction
        self.length = length

    def __str__(self):
        return "({},{},{})".format(self.source, self.dest,
                                   self.is_construction)

    def shift_vertically(self, dist_y: Dim):
        """Returns new line shifted vertically a given distance"""
        new_source = Point(self.source.x, self.source.y + dist_y.dist)
        new_dest = Point(self.dest.x, self.dest.y + dist_y.dist)
        return Line(
            new_source,
            new_dest,
            is_construction=self.is_construction,
            length=self.length)

    def toggle_constr_and_shift_vertically(self, dist_y: Dim):
        """Shifts vertically and flips is_construction bit"""
        line = self.shift_vertically(dist_y)
        line.is_construction = not line.is_construction
        return line

    def points(self):
        """Returns list containing endpoints"""
        return [self.source, self.dest]

    def coords_for_plot(self):
        """Utility function returning coordinates of endpoints."""
        x_coords = [self.source.x, self.dest.x]
        y_coords = [self.source.y, self.dest.y]
        return [x_coords, y_coords]
