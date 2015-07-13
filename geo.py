"""Some utilities for working with geometry"""

import Polygon
from collections import namedtuple
from math import *

def v2norm(v):
    """Returns a unit vector in the same direction as the given pair."""

    s = 1.0 / sqrt(v[0] * v[0] + v[1] * v[1])
    return (s * v[0], s * v[1])

def extend_poly(margin, points, cw=False):
    """Adds padding to the edges of a polygon to create a new one.
    
    Given a non-intersecting polygon, returns a new polygon created by
    expanding each edge normally outward. Assumes counter-clockwise
    winding by default. This particular algorithm works by placing a
    point on the line bisecting the angle between two adjacent edges of
    the polygon. It is liable to give poor results if the margin is
    larger than the length of some of the sides."""

    newpoints = []

    for i in range(len(points)):
        p0 = points[i]
        p1 = points[(i + 1) % len(points)]
        p2 = points[(i + 2) % len(points)]

        v1 = v2norm((p0[0] - p1[0], p0[1] - p1[1]))
        v2 = v2norm((p2[0] - p1[0], p2[1] - p1[1]))

        # Get angle between vectors
        theta1 = atan2(v1[1], v1[0])
        theta2 = atan2(v2[1], v2[0])
        dtheta = 0.5 * (theta2 - theta1)

        # Edges are parallel
        if dtheta == 0:
            continue

        if cw:
            d = -margin / sin(dtheta)
        else:
            d = margin / sin(dtheta)

        theta = 0.5 * (theta1 + theta2)
        r = (d * cos(theta), d * sin(theta))

        newpoints.append((p1[0] + r[0], p1[1] + r[1]))

    return newpoints

def tristrip_to_quads(strip):
    """Turns a triangle strip into a list of quadrilaterals.

    If the strip has an odd number of triangles, the last element of
    the list will be a quad with two of its points equal. See
    Polygon.Polygon.tristrip for details on the format of a triangle
    strip."""

    if len(strip) < 4:
        raise RuntimeError("need at least two triangles to make a quad")

    quads = []
    for i in range(0, len(strip) - 3, 2):
        quads.append([strip[i], strip[i + 1], strip[i + 3], strip[i + 2]])

    if len(strip) % 2 == 1:
        quads.append([strip[-3], strip[-2], strip[-1], strip[-1]])

    return quads
