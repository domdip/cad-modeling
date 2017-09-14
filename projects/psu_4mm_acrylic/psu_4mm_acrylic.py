#!/usr/bin/python3
"""4mm acrylic box for PSU project
Created with 0.15mm laser setup, kerf compensation handled by Fusion 360"""
import traceback

from adsk.core import Application

# Due to Fusion 360 limitations we need to modify system path to load modules
# This is necessary boilerplate until they directly add support beyond
# relative imports
from inspect import getsourcefile
import os.path
import sys
current_path = os.path.abspath(getsourcefile(lambda: 0))
current_dir = os.path.dirname(current_path)
parent_dir = current_dir[:current_dir.rfind(os.path.sep)]
grandparent_dir = parent_dir[:parent_dir.rfind(os.path.sep)]
sys.path.insert(0, grandparent_dir)

from fusion360_util.tabbed_box import BoxPlotter
from geometry_util.box import Box
from geometry_util.geometry import Point

def specify_box():
    # Units are in mm
    origin = Point(0, 0)
    width = 120
    box = Box(width, 100, 220, 4.7625, 2, bb_sw_point=origin)

    # Front panel is 'upper' (W x H)
    banana_diam = 7.8
    banana_vert_dist = 19.05
    banana_sw_x = 5
    banana_sw_y = 12
    num_banana_pairs = 7

    switch_w = 10.5
    switch_h = 29

    led_diam = 5
    led_spacing = 10

    # using this since the lower side is upside down as drawn
    fp_rel = 'nw'

    spacing = (width - num_banana_pairs * banana_diam - switch_w) / (
        num_banana_pairs + 2.0)
    for i in range(num_banana_pairs):
        bottom_p1 = Point(banana_sw_x + i * (spacing + banana_diam),
                          banana_sw_y)
        bottom_p2 = Point(banana_sw_x + banana_diam + i *
                          (spacing + banana_diam),
                          banana_sw_y + banana_diam)
        box.lower_side.add_cutout(
            'circle',
            bottom_p1,
            bottom_p2,
            name="banana_lower_{}".format(i),
            bb_inner=fp_rel)
        top_p1 = Point(0, banana_vert_dist).relative_to(bottom_p1)
        top_p2 = Point(0, banana_vert_dist).relative_to(bottom_p2)
        box.lower_side.add_cutout(
            'circle',
            top_p1,
            top_p2,
            name="banana_upper_{}".format(i),
            bb_inner=fp_rel)

    # Put switch to the right of last banana plugs
    # Used midpoint so this math is a little hacky
    switch_p1 = top_p1.midpoint(bottom_p2).relative_to(
        Point(spacing + banana_diam / 2.0, -switch_h / 2.0))
    switch_p2 = switch_p1.relative_to(Point(switch_w, switch_h))
    box.lower_side.add_cutout(
        'rect', switch_p1, switch_p2, name="switch", bb_inner=fp_rel)

    # Put LED above the switch
    led_p1 = switch_p1.midpoint(switch_p2).relative_to(
        Point(-led_diam / 2.0, switch_h / 2.0 + led_spacing))
    led_p2 = led_p1.relative_to(Point(led_diam, led_diam))
    box.lower_side.add_cutout(
        'circle', led_p1, led_p2, name="led", bb_inner=fp_rel)

    # Rear panel (upper)
    # PSU will hug bottom right.  Needs cutout for power cord and 2 cutouts
    # for ventilation.
    # Make these relative to southeast corner (easier math)
    rp_rel = 'se'

    cord_p1 = Point(12, 9)
    cord_p2 = Point(24, 31).relative_to(cord_p1)
    box.upper_side.add_cutout(
        'rect', cord_p1, cord_p2, name="cord", bb_inner=rp_rel)

    vent_far_limit = 61  # Both vents end 61mm from side

    small_vent_height = 32
    small_vent_se_x = 38
    small_vent_se_y = 5
    small_vent_p1 = Point(small_vent_se_x, small_vent_se_y)
    small_vent_p2 = Point(vent_far_limit,
                          small_vent_se_y + small_vent_height)
    box.upper_side.add_cutout(
        'rect',
        small_vent_p1,
        small_vent_p2,
        name="small_vent",
        bb_inner=rp_rel)

    big_vent_height = 38
    big_vent_se_x = 8
    big_vent_se_y = 49

    big_vent_p1 = Point(big_vent_se_x, big_vent_se_y)
    big_vent_p2 = Point(vent_far_limit, big_vent_se_y + big_vent_height)
    box.upper_side.add_cutout(
        'rect', big_vent_p1, big_vent_p2, name="big_vent", bb_inner=rp_rel)

    # Left panel
    # PSU will hug left side
    fan_p1 = Point(38, 6)
    fan_p2 = Point(80, 80).relative_to(fan_p1)
    box.left_side.add_cutout(
        'rect', fan_p1, fan_p2, name="fan", bb_inner='ne', flipxy=True)

    return box

def run(context):
    ui = None
    try:
        app = Application.get()
        ui = app.userInterface

        box = specify_box()

        box_plotter = BoxPlotter(app, box)
        box_plotter.sketch_sides()
        box_plotter.sketch_cutouts()

        box_plotter.extrude_sides()
        box_plotter.cut_sides()

        ui.messageBox('Finished')

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
