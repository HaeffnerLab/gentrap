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

# TODO rename everything nicer
DEFAULT_PARAMS = {
    # Number of electrodes per side
    "numelectrodes": 10,
    # DC electrode widths
    "dcwidths": [400, 400, 400, 400, 400, 200, 400, 400, 400, 400],
    # DC electrode length
    "dclength": 300,
    # Gap between electrodes and ground plane
    "gap": 10,
    # Width and length of center electrode
    "centerwidth": 320,
    "centerlength": 11000,
    # Width of left and right RF electrodes
    "rfwidthleft": 120,
    "rfwidthright": 120,
    # Length of both RFs
    "rflength": 11500,
    # Width of bridge between electrode and bonding pad
    "bridgewidth": 50,
    # Gap between bonding pads
    "padgaps": [100, 100, 450, 100, 100, 100, 100, 100, 100],
    # Overall dimensions of board
    "totalwidth": 12000,
    "totalheight": 12000,
    # XXX undocumented
    "spacefromedge": 100,
    # XXX undocumented
    "centerspacefromedge": 3000,
    # XXX undocumented
    "rfdcbondinggap": 50,
    # XXX undocumented
    "groundplanecutoutlength": 0,
    # XXX undocumented
    "dcleadspacing": 130,
    # XXX undocumented
    "rfpadoffset": 680,
    # Offset in X direction of DC bonding pad array on left and right
    "dcpadoffset": 125,
    # Dimesnions of DC bonding pads
    "dcpadx": 400,
    "dcpadz": 400,
    # Dimensions of RF bonding pads
    "rfpadx": 400,
    "rfpadz": 400,
    # Dimensions and position of thermometer placement pad
    "thermpadz": 400,
    "thermpadx": 600,
    "thermpadoffsxleft": 1200,
    "thermpadoffsxright": 500,
    # Width of fingers attached to center electrode pads
    "fingerwidth": 40,
    # Round dimensions to this resolution (in microns)
    "resolution": 0.1,
}

def main(fileout):
    params = dict(DEFAULT_PARAMS)
    params.update(layout.calc_extra_params(DEFAULT_PARAMS))

    def flip(p):
        x, y = zip(*p)
        return zip(y, x)

    # Get all electrode points
    layers = {}
    layers["0"] = [flip(layout.calc_rf_points(params))]
    for i in range(params["numelectrodes"]):
        layers[str(i + 1)] = [flip(layout.calc_dc_points(
            params, Align.LEFT, i))]
        layers[str(i + 11)] = [flip(layout.calc_dc_points(
            params, Align.RIGHT, i))]
    layers["21"] = [
        flip(layout.calc_center_points(params, Align.CENTER)),
        flip(layout.calc_center_pads(params, Align.LEFT)),
        flip(layout.calc_center_pads(params, Align.RIGHT))
    ]
    layers["22"] = [
        flip(layout.calc_therm_points(params, Align.LEFT)),
        flip(layout.calc_therm_points(params, Align.RIGHT))
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
