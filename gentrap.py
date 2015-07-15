#!/usr/bin/env python
from collections import namedtuple
from datetime import datetime
from dxfwrite import DXFEngine as dxf
import os
from Polygon import Polygon
import sys

import geo
import layout
from layout import Align

def main(fileout):
    params = dict(layout.DEFAULT_PARAMS)
    params.update(layout.calc_extra_params(params))

    def flip(p):
        x, y = zip(*p)
        return zip(y, x)

    # Get all electrode points
    n = params["numelectrodes"]
    layers = {}
    layers["0"] = [flip(layout.calc_rf_points(params))]
    for i in range(n):
        layers[str(i + 1)] = [flip(layout.calc_dc_points(
            params, Align.LEFT, i))]
        layers[str(i + n + 1)] = [flip(layout.calc_dc_points(
            params, Align.RIGHT, i))]
    layers[str(2 * n + 1)] = [
        flip(layout.calc_center_points(params, Align.CENTER)),
        flip(layout.calc_center_pads(params, Align.LEFT)),
        flip(layout.calc_center_pads(params, Align.RIGHT))
    ]

    # Define region to cut out from ground plane
    extpolys = [
           geo.extend_poly(params["gap"], p, True)
                for (_, polys) in layers.iteritems()
                for p in polys]

    w = 0.5 * params["totalwidth"]
    h = 0.5 * params["totalheight"]

    gndplane = Polygon([(-h, -w), (h, -w), (h, w), (-h, w)])
    for p in extpolys:
        gndplane = gndplane - Polygon(p)

    layers["GROUND"] = [gndplane]

    # Turn all geometry into quads
    for k in layers.keys():
        # Each layer is a list of polys, and mapping tristrip_to_quads
        # gives a list of lists of quads, which needs to be flattened
        layers[k] = [
                quad for p in layers[k]
                     for quads in map(
                            geo.tristrip_to_quads, Polygon(p).triStrip())
                     for quad in quads]

    # Create DXF file
    drawing = dxf.drawing(fileout)
    for (k, quads) in layers.iteritems():
        for q in quads:
            drawing.add(dxf.face3d(flip(q), layer=k))
    drawing.save()
    print("Wrote to '{}'".format(path))

    return 0

if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = os.path.abspath(sys.argv[1])
    else:
        path = os.path.abspath(
                datetime.now().strftime("./newtrap_%Y%m%d_%H%M%S.dxf"))
    main(path)
