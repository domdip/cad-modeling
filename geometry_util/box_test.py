#!/usr/bin/python3
"""Tests Box class by plotting a sample box's sides.
"""
from box import Box
from box import Point

def plot_box(box: Box):
    """Uses matplotlib to plot a box."""
    import matplotlib.pyplot as plt

    plt.figure()

    xlist = []
    ylist = []
    plt.ylabel("vertical")
    plt.xlabel("horiztonal")
    plt.title('Edge')
    plt.xlim(-100, 280)
    plt.ylim(-100, 150)
    for side in box.sides().values():
        xlist = []
        ylist = []
        for edge_lines in side.edge_line_list():
            for line in edge_lines:
                if not line.is_construction:
                    x_coords, y_coords = line.coords_for_plot()
                    xlist.extend(x_coords)
                    ylist.extend(y_coords)
        plt.plot(xlist, ylist)

    for side in box.sides().values():
        for (kind, _name, corner_1, corner_2) in side.cutouts:
            if kind == "circle":
                # Just draw a diagonal line for now
                plt.plot([corner_1.y, corner_2.y],
                         [corner_1.x, corner_2.x], '--')

    plt.show()


def main():
    """Test case to validate box coordinate creation"""
    box = Box(100, 50, 65, 3, 2, bb_sw_point=Point(0, 0))
    plot_box(box)

if __name__ == "__main__":
    main()
