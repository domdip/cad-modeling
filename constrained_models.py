# -*- coding: utf-8 -*-
from enum import Enum

# pylint: disable=too-few-public-methods,C0111,C0103,R0913

class Point(object):
    def __init__(self, x, y)

class Direction(Enum):
    NORTH = 0  #Also rotational no-op
    EAST = 1  #Also a 90 degree rotation
    SOUTH = 2  #180 rotation
    WEST = 3  #270 degree rotation


class Orientation(object):
    def __init__(self, direction, clockwise):
        self.direction = direction
        self.clockwise = clockwise


class ConstrainedPoint(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.is_fixed = False
        self.ref_point = None
        #TODO: from orientation?
        # self.horiz_dim = False
        # self.vert_dim = False
        self.x_dist = None
        self.y_dist = None
        # self.vert = False
        # self.horiz = False
        # self.parallel = False

    @classmethod
    def origin(cls):
        point = cls(0.0, 0.0)
        point.is_fixed = True
        return point

    def coords(self):
        return (self.x, self.y)


class ConstrainedLine(object):
    def __init__(self, s, t):
        self.s = s
        self.t = t
        # self.is_fixed = False
        # self.is_construction = False
        # self.ref_line = None
        # self.parallel = False
        # self.perpendicular = False
        # self.vert = False
        # self.horiz = False
        # self.equal = False


    #Keep track of value in cm as well as parameter name.
    #May also be flipped.  If so, when used as a delta we use its negative value.
class Val(object):
    def __init__(self, name, value, flipped=False):
        self.name = name
        self.value = value
        self.flipped = flipped

    def __add__(self, other):
        # if isinstance(other, Val):
        #     if self.value >= 0 and other.value >= 0:
        #         return Val(self.name + " + " + other.name,
        #                    self.value + other.value)
        #     elif self.value >= 0 and self.value >= other.value:
        #         return Val(self.name + " - " + other.name,
        #                    self.value + other.value)
        #     elif self.value < 0 and other.value < 0:
        #         return Val(self.name + " + " + other.name,
        #                    self.value + other.value)
        #     else:
        #         return Val(other.name + " - " + self.name,
        #                    self.value + other.value)

        # else:
        if isinstance(other, Val):
            if self.flipped ^ other.flipped:
                raise TypeError("Summed Vals must be same flip type")
            else:
                return Val(self.name + " + " + other.name,
                           self.value + other.value, self.flipped)
        else:
            return Val(self.name + " + " + str(other), self.value + other)

    def __mul__(self, other):
        return Val("(" + self.name + ") * " + str(other), self.value * other)

    def __truediv__(self, other):
        return Val("(" + self.name + ") / " + str(other), self.value / other)

    def __neg__(self):
        return Val(self.name, self.value, not self.flipped)

    def __repr__(self):
        return "Val(" + self.name + "," + str(self.value) + "," + str(
            self.flipped) + ")"


def point_from_ref_point(source, x_dist, y_dist):
    """Generates a ConstrainedPoint from an existing point and distances.

    If the new point has the same coordinates, we simply return the original
    point.

    Args:
        source: ConstrainedPoint
        x_dist: x coordinate distance (Val, None, or 0)
        y_dist: y coordinate distance (Val, None, or 0)

    Returns:
        ConstrainedPoint: the generated point

    """
    (x0, y0) = source.coords()
    x = x0 if not x_dist else x0 + x_dist.value
    y = y0 if not y_dist else y0 + y_dist.value

    if x == x0 and y == y0:  #noop
        return source

    point = ConstrainedPoint(x, y)
    point.ref_point = source
    point.x_dist = x_dist
    point.y_dist = y_dist

    return point


def bounding_box_corners(bottom_left, x_dist, y_dist):
    """Generates corner points of a box.

    TODO: comment about why we did it in this order/way

    Args:
        bottom_left: ConstrainedPoint for bottom left corner.  If None, we
            use the origin.
        x_dist(Val): Width
        y_dist(Val): Height

    Returns:
        Tuple4[ConstrainedPoint]: corners in CCW order

    """
    if not bottom_left:
        bottom_left = ConstrainedPoint.origin()

    bottom_right = point_from_ref_point(bottom_left, x_dist, None)
    top_right = point_from_ref_point(bottom_right, None, y_dist)
    top_left = point_from_ref_point(top_right, -x_dist, None)

    corner_list = (bottom_left, bottom_right, top_right, top_left)

    return corner_list


#Create a new point at (x, y) subject to a rotation
def create_oriented_point(source, dist_x, dist_y, rotation):
    if rotation is Orientation.NORTH:
        return point_from_ref_point(source, dist_x, dist_y)
    elif rotation is Orientation.EAST:
        return point_from_ref_point(source, dist_y, -dist_x)
    elif rotation is Orientation.SOUTH:
        return point_from_ref_point(source, -dist_x, -dist_y)
    else:
        return point_from_ref_point(source, -dist_y, dist_x)


#Create a new point by moving in the given distance and orientation
def create_simple(source, dist, orientation):
    #By definition this is equivalent to moving North under a rotation
    return create_oriented_point(source, 0.0, dist, orientation)


def create_and_append_point(notch_width, points, orientation):
    #TODO: add check for existing point with same coords
    new_point = create_simple(points[-1], notch_width, orientation)
    points.append(new_point)


def create_edge(starting_point,
                notch_width,
                notch_height,
                notch_count,
                start_wide,
                start_tall,
                rotation,
                adjust_corner=False):
    """Generates points for an edge of a box.

        Draws a given number of notches.  This is written from the perspective
        of a west edge proceeding north.  However, rotation parameter can change these directions.

        Args:
            starting_point(ConstrainedPoint): Starting location
            notch_width(Val): width of notches
            notch_height(Val): height of notches
            notch_count(int): number of notches
            start_wide(bool): this edge starts at bounding box width-wise
            start_tall(bool): this edge starts at bounding box height-wise
            rotation: added to each orientation (rotates 90 degrees per 1 value)
            adjust_corner: if True starting_point is a bounding box corner and we
                check if an adjustment is needed

        Returns:
            TODO
    """
    relative_north = Orientation.NORTH + rotation

    points = []  #Collector for edge points

    #If we started with a bounding box point, need to adjust location of first edge point.
    if adjust_corner:
        dist_x = 0.0
        dist_y = 0.0
        if not start_wide:
            dist_x = notch_height
        if not start_tall:
            dist_y = notch_height
        first_edge_point = create_oriented_point(starting_point, dist_x,
                                                 dist_y, rotation)
        points.append(first_edge_point)
    else:
        points.append(starting_point)

    #Unadjusted, our first notch is east if we start wide.  Otherwise we need to flip direction.
    height_orientation_adj = Orientation(0) if start_wide else Orientation(2)

    if start_tall:
        create_and_append_point(notch_height, points, relative_north)

    for _notch in range(0, notch_count):
        create_and_append_point(notch_width, points, relative_north)

        create_and_append_point(
            notch_height, points,
            Orientation.EAST + rotation + height_orientation_adj)

        create_and_append_point(notch_width, points, relative_north)

        create_and_append_point(
            notch_height, points,
            Orientation.WEST + rotation + height_orientation_adj)

        create_and_append_point(notch_width, points, relative_north)

    if start_tall:
        create_and_append_point(notch_height, points, relative_north)
    return points


def create_face_from_notch_width(southwest_corner, x_, notch_height,
                                 notch_count, wide, tall, orientation):
    """Creates a face.

    Code is written as if given a point in the southwest corner of the bounding box, then drawing
    clockwise.

    Args:
        wide: if true, west edges start with a tab (vs a cut)
        tall: if true, south edges start with a tab
    """
    west_face = create_edge(
        southwest_corner,
        notch_width,
        notch_height,
        notch_count,
        wide,
        tall,
        orientation + Orientation(0),
        adjust_corner=True)
    north_face = create_edge(west_face[-1], notch_width, notch_height,
                             notch_count, tall, wide,
                             orientation + Orientation(1))
    east_face = create_edge(north_face[-1], notch_width, notch_height,
                            notch_count, wide, tall,
                            orientation + Orientation(2))
    south_face = create_edge(east_face[-1], notch_width, notch_height,
                             notch_count, tall, wide,
                             orientation + Orientation(3))
    return (west_face, north_face, east_face, south_face)


def create_box(southwest_corner, width, height, depth, spacing, notch_count,
               bottom_wide, bottom_tall):
    """Lays out the faces of a box.

    Args:
        bottom_wide: if true, west edge of bottom face starts with a tab (vs a cut)
        bottom_tall: if true, south edge of bottom face with a tab
    """

    return


def main():
    starting_point = ConstrainedPoint.origin()
    notch_width = Val("NW", 2)
    notch_height = Val("NH", 3)
    notch_count = 4

    wide, tall = (True, False)

    both = (False, )
    # for orientation in Orientation:
    for wide in both:
        for tall in both:
            edges = create_face_from_notch_width(starting_point, notch_width,
                                                 notch_height, notch_count,
                                                 wide, tall, Orientation(0))
            point_list = [(point.x, point.y) for edge in edges
                          for point in edge]
    1


if __name__ == "__main__":
    main()
