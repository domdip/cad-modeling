#!/usr/bin/python3
"""Box-specific classes for CAD specification.

A 'Box' has six 'Side' objects.  A 'Side' has four 'Edge' objects.

These classes are Python object models.  They do not depend on the
Fusion 360 API.

Note that these classes do not (by themselves) draw anything graphically or
manipulate CAD APIs.  To 'draw' below simply means to create corresponding
objects.

"""


from typing import NamedTuple
from geometry import Dim, Line, Point

# pylint: disable=too-few-public-methods,C0111,C0103,R0913,R0902

EdgeInfo = NamedTuple('EdgeInfo', [("is_wide", bool), ("is_tall", bool),
                                   ("notch_width", Dim), ("notch_height", Dim),
                                   ("notch_height_other", Dim), ("notch_count",
                                                                 Dim)])


class Edge(object):
    """Creates and contains lines for an edge of a side.

    During creation we assume that we are working with the south edge of the
    side, and creating from left to right.

    Args:
        edge_info (EdgeInfo): Contains init params.  See EdgeInfo documentation
        bb_left (Point): Left bounding box of this edge.
        rotate (int, optional): degrees of counter clockwise rotation to apply

    Attributes:
        bb_left (Point): left exterior bounding box point
        notch_width (Dim): width of this edge
        notch_height (Dim): height of this edge
        notch_count (int): number of notches in this edge
        notch_height_other (Dim): height of joining edges
        is_wide (bool): whether the edge's width extends to bounding box
        is_tall (bool): whether the edge's corner height extends to bb
        bb_right (Point): right exterior bounding box point
        inner_bb_left (Point): left interior bounding box point
        lines (list[Line]): lines in this edge

    """
    def __init__(self, edge_info: EdgeInfo, bb_left: Point, rotate: int=0):
        self.bb_left = bb_left
        self.notch_width = edge_info.notch_width
        self.notch_height = edge_info.notch_height
        self.notch_count = edge_info.notch_count
        self.notch_height_other = edge_info.notch_height_other
        self.is_wide = edge_info.is_wide
        self.is_tall = edge_info.is_tall
        self.bb_right = None
        self.inner_bb_left = None

        self.lines = []
        self.create()
        self.rotate(rotate)

    def create(self):
        """Creates lines and bounding box points."""

        # Draw outer horizontal portion of Edge.
        # First and last components are special cases.
        outer_line_extend_edges = (self.is_wide and self.is_tall)
        outer_edge_l = self.bb_left.draw_horiz(self.notch_height_other,
                                               not outer_line_extend_edges)
        outer_lines = []
        next_edge = outer_edge_l.dest.draw_horiz(self.notch_width,
                                                 not self.is_tall)
        outer_lines.append(next_edge)
        for _notch in range(self.notch_count):
            next_edge = next_edge.dest.draw_horiz(self.notch_width,
                                                  self.is_tall)
            outer_lines.append(next_edge)
            next_edge = next_edge.dest.draw_horiz(self.notch_width,
                                                  not self.is_tall)
            outer_lines.append(next_edge)

        outer_edge_r = next_edge.dest.draw_horiz(self.notch_height_other,
                                                 not outer_line_extend_edges)

        self.bb_right = outer_edge_r.dest

        # Draw inner segments.
        inner_line_extend_edges = self.is_wide and not self.is_tall
        inner_edge_l = outer_edge_l.shift_vertically(self.notch_height)
        inner_edge_l.is_construction = not inner_line_extend_edges
        self.inner_bb_left = inner_edge_l.dest
        # Apart from first/last, inner horizontal is the same as outer, with
        # construction line bit flipped and y coordinate shifted up.
        inner_lines = [
            line.toggle_constr_and_shift_vertically(self.notch_height)
            for line in outer_lines
        ]
        inner_edge_r = outer_edge_r.shift_vertically(self.notch_height)
        inner_edge_r.is_construction = not inner_line_extend_edges

        # Merge inner/outer special cases.
        outer_lines = [outer_edge_l] + outer_lines + [outer_edge_r]
        inner_lines = [inner_edge_l] + inner_lines + [inner_edge_r]

        # Draw a vertical portion of the edge where we see gaps between real
        # lines.
        vert_lines = []
        for index in range(len(inner_lines) - 1):
            draw_gap = (not inner_lines[index].is_construction and not
                        outer_lines[index + 1].is_construction) or (
                            not outer_lines[index].is_construction and not
                            inner_lines[index + 1].is_construction)
            line = Line(inner_lines[index].dest, outer_lines[index].dest,
                        not draw_gap)
            vert_lines.append(line)

        unsorted_lines = inner_lines + outer_lines + vert_lines
        self.lines = sorted(unsorted_lines, key=lambda x: x.coords_for_plot())

    # Rotate counter clockwise around initial bounding box point.
    def rotate(self, degrees_in: int):
        around = self.bb_left
        assert (degrees_in % 90 == 0)
        degrees = degrees_in % 360

        if degrees == 0:
            pass
        elif degrees == 90:
            # Take distinct points in case it was used more than once
            points = set()
            for line in self.lines:
                points.update([line.source, line.dest])
            for point in points:
                point.rotate(degrees, around)
        else:
            self.rotate(90)
            self.rotate(degrees - 90)

SideInfo = NamedTuple(
    'SideInfo', [("bb_sw_corner", Point), ("is_wide", bool), ("is_tall", bool),
                 ("ew_notch_width", Dim), ("ew_notch_height",
                                           Dim), ("ew_notch_count", Dim),
                 ("ns_notch_width", Dim), ("ns_notch_height",
                                           Dim), ("ns_notch_count", Dim)])
SideInfo.__doc__ = """Container for inputs to a Side object.
Args:
    bb_sw_corner: southwest corner of side's outer bounding box
    is_wide: whether the side's width extends to bounding box
    is_tall: whether the side's corner height extends to bounding box
    ew_notch_width: notch width of horizontal sides
    ew_notch_height: notch height of horizontal sides
    ew_notch_count: notch count of horizontal sides
    ns_notch_width: notch width of vertical sides
    ns_notch_height: notch height of vertical sides
    ns_notch_count: notch count of vertical sides

"""


class Side(object):

    """Creates and contains edges for a side of a box.

    Args:
        side_info (SideInfo): Contains init params.  See SideInfo documentation

    Attributes:
        bounding_box (dict): map of exterior bounding box points.
        inner_bounding_box (dict): map of interior bounding box points.
        cutouts (list): Features to cut out of this side.
        west_face (Side): west side of box
        north_face (Side): north side of box
        east_face (Side): east side of box
        south_face (Side): south side of box

    """

    def __init__(self, side_info: SideInfo):
        self.side_info = side_info
        self.west_face = None
        self.north_face = None
        self.east_face = None
        self.south_face = None
        self.bounding_box = None
        self.inner_bounding_box = None
        self.create()
        self.cutouts = []

    def create(self):
        # For the vertical sides
        ns_edge_info = EdgeInfo(
            self.side_info.is_tall, self.side_info.is_wide,
            self.side_info.ns_notch_width, self.side_info.ns_notch_height,
            self.side_info.ew_notch_height, self.side_info.ns_notch_count)
        # For the horizontal sides
        ew_edge_info = EdgeInfo(
            self.side_info.is_wide, self.side_info.is_tall,
            self.side_info.ew_notch_width, self.side_info.ew_notch_height,
            self.side_info.ns_notch_height, self.side_info.ew_notch_count)
        self.south_face = Edge(ew_edge_info, self.side_info.bb_sw_corner)
        self.east_face = Edge(ns_edge_info, self.south_face.bb_right, 90)
        self.north_face = Edge(ew_edge_info, self.east_face.bb_right, 180)
        self.west_face = Edge(ns_edge_info, self.north_face.bb_right, 270)

        self.inner_bounding_box = {
            'sw': self.south_face.inner_bb_left,
            'se': self.east_face.inner_bb_left,
            'ne': self.north_face.inner_bb_left,
            'nw': self.west_face.inner_bb_left,
        }

        self.bounding_box = {
            'sw': self.side_info.bb_sw_corner,
            'se': self.south_face.bb_right,
            'ne': self.east_face.bb_right,
            'nw': self.north_face.bb_right
        }

    def all_lines(self):
        return (self.south_face.lines + self.east_face.lines +
                self.north_face.lines + self.west_face.lines)

    def edge_line_list(self):
        return [
            self.south_face.lines, self.east_face.lines, self.north_face.lines,
            self.west_face.lines
        ]

    def add_cutout(self,
                   kind,
                   corner_1,
                   corner_2,
                   bb_inner='sw',
                   name=None,
                   rotate=0,
                   flipxy=False):
        import copy
        c1 = copy.copy(corner_1)
        c2 = copy.copy(corner_2)
        # Change signs so positive relative movements go into the side
        if 'n' in bb_inner:
            c1.y = -corner_1.y
            c2.y = -corner_2.y
        if 'e' in bb_inner:
            c1.x = -corner_1.x
            c2.x = -corner_2.x

        if flipxy:
            c1 = Point(c1.y, c1.x)
            c2 = Point(c2.y, c2.x)

        bb = self.inner_bounding_box[bb_inner]
        c1 = c1.relative_to(bb)
        c2 = c2.relative_to(bb)
        c1.rotate(rotate, bb)
        c2.rotate(rotate, bb)
        self.cutouts.append((kind, name, c1, c2))


class Box(object):

    """Creates and contains elements (sides and associated objects) of a box.

        ASCII art via Rahul:
        https://github.com/rahulbot/box-designer-website
        <pre>
                    ----------
          top ->    |  w x d |
                    ----------
                    ----------
        upper ->    |  w x h |
                    |        |
                    ----------
         ---------  ----------  ---------
         | d x h |  |  w x d |  | d x h |
         ---------  ----------  ---------
                    ----------
        lower ->    |  w x h |
                    |        |
                    ----------
        </pre>

    Args:
        width (float): Description
        height (float): Description
        depth (float): Description
        thickness (float): Description
        spacing (float): Description
        tab_width (Optional[int]): Description
        bb_sw_point (Optional[Point]): Description

    Attributes:
        bottom_side (Side): bottom side object
        left_side (Side): left side object
        lower_side (Side): lower side object
        right_side (Side): right side object
        top_side (Side): top side object
        upper_side (Side): upper side object

    """

    def __init__(
            self,
            width: float,
            height: float,
            depth: float,
            thickness: float,
            spacing: float,
            tab_width: int=False,
            bb_sw_point: Point=False):
        self.width = Dim(float(width), "W")
        self.height = Dim(float(height), "H")
        self.depth = Dim(float(depth), "D")
        self.thickness = Dim(float(thickness), "THICKNESS")
        self.spacing = Dim(spacing, "SPACING")
        self.tab_width = tab_width
        self.bb_sw_point = bb_sw_point if bb_sw_point else Point(0, 0)
        self.create()

    def create(self):
        """Creates sides of the box.

        Uses the inputs to create sides of a box with appropiate tabs and
        shapes.
        """

        (tab_num_w, tab_width_w) = self.calc_tab_num_and_length(self.width)
        (tab_num_h, tab_width_h) = self.calc_tab_num_and_length(self.height)
        (tab_num_d, tab_width_d) = self.calc_tab_num_and_length(self.depth)

        # Draw the bottom side w x d.  We assume it is short and narrow so the
        # lid is easier to place (bottom will be identical to the lid)
        bottom_info = SideInfo(self.bb_sw_point, False, False, tab_width_w,
                               self.thickness, tab_num_w, tab_width_d,
                               self.thickness, tab_num_d)
        self.bottom_side = Side(bottom_info)

        # Draw right side h x d
        spacing_line = self.bottom_side.bounding_box['se'].draw_horiz(
            self.spacing, True)
        # Since this is horizontal to a narrow side it must be wide.
        # We also make it tall (this is optional but has to oppose upper/lower)
        right_info = SideInfo(spacing_line.dest, True, True, tab_width_h,
                              self.thickness, tab_num_h, tab_width_d,
                              self.thickness, tab_num_d)
        self.right_side = Side(right_info)

        # Draw upper side w x h
        spacing_line = self.bottom_side.bounding_box['nw'].draw_vert(
            self.spacing, True)
        # Since it fits vertically against a short side it must be tall
        upper_info = SideInfo(spacing_line.dest, False, True, tab_width_w,
                              self.thickness, tab_num_w, tab_width_h,
                              self.thickness, tab_num_h)
        self.upper_side = Side(upper_info)

        # Draw left side h x d
        spacing_line = self.bottom_side.bounding_box['sw'].draw_horiz(
            -(self.spacing + self.height + 2 * self.thickness), True)
        left_info = SideInfo(spacing_line.dest, True, True, tab_width_h,
                             self.thickness, tab_num_h, tab_width_d,
                             self.thickness, tab_num_d)
        self.left_side = Side(left_info)

        # Draw top side w x d
        spacing_line = self.right_side.bounding_box['se'].draw_horiz(
            self.spacing, True)
        # Since this is horizontal to a wide side it must be narrow
        top_info = SideInfo(spacing_line.dest, False, False, tab_width_w,
                            self.thickness, tab_num_w, tab_width_d,
                            self.thickness, tab_num_d)
        self.top_side = Side(top_info)

        # Draw lower side w x h
        spacing_line = self.bottom_side.bounding_box['sw'].draw_vert(
            -(self.spacing + self.height + 2 * self.thickness), True)
        # Since it fits vertically against a short side it must be tall
        lower_info = SideInfo(spacing_line.dest, False, True, tab_width_w,
                              self.thickness, tab_num_w, tab_width_h,
                              self.thickness, tab_num_h)
        self.lower_side = Side(lower_info)
        # import ipdb; ipdb.set_trace()

    def calc_tab_num_and_length(self, dim: Dim):
        """Determines number and length of tab segments for a given length.

        Args:
            dim (Dim): object containing length of side

        Returns:
            number of tabs (int), length of segments (Dim)
        """
        segment_upper_bound_2 = (dim.dist / self.thickness.dist) // 2
        tab_upper_bound_2 = (segment_upper_bound_2 - 1) // 2
        num_tabs_2 = (tab_upper_bound_2 if tab_upper_bound_2 % 2 == 1 else
                      tab_upper_bound_2 - 1)
        # But we prefer at least 3 tabs with 3x thickness
        segment_upper_bound_3 = (dim.dist / self.thickness.dist) // 3
        tab_upper_bound_3 = (segment_upper_bound_3 - 1) // 2
        num_tabs_3 = (tab_upper_bound_3 if tab_upper_bound_3 % 2 == 1 else
                      tab_upper_bound_3 - 1)
        num_tabs = num_tabs_3 if num_tabs_3 >= 3 else num_tabs_2
        return int(num_tabs), dim / (2 * num_tabs + 1)

    def all_lines(self):
        """Returns lines from all sides in a single list."""
        return self.bottom_side.all_lines() + self.right_side.all_lines(
        ) + self.upper_side.all_lines() + self.left_side.all_lines(
        ) + self.top_side.all_lines() + self.lower_side.all_lines()

    def sides(self):
        """Returns dict of box's sides."""
        side_dict = {
            "bottom": self.bottom_side,
            "right": self.right_side,
            "upper": self.upper_side,
            "left": self.left_side,
            "top": self.top_side,
            "lower": self.lower_side
        }
        return side_dict
