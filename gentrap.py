#!/usr/bin/env python
import argparse
from collections import namedtuple
from datetime import datetime
from dxfwrite import DXFEngine as dxf
import os
import parameters
from Polygon import Polygon
from string import Template
import yaml

import geo
import layout
from layout import Align

def main(parms, fileout):
    def flip(p):
        x, y = zip(*p)
        return zip(y, x)

    # Get all electrode points
    n = parms["dc_count"]
    layers = {}
    layers["0"] = [flip(layout.calc_rf_points(parms))]
    for i in range(n):
        layers[str(i + 1)] = [flip(layout.calc_dc_points(
            parms, Align.LEFT, i))]
        layers[str(i + n + 1)] = [flip(layout.calc_dc_points(
            parms, Align.RIGHT, i))]
    layers[str(2 * n + 1)] = [
        flip(layout.calc_center_points(parms, Align.CENTER)),
        flip(layout.calc_center_pads(parms, Align.LEFT)),
        flip(layout.calc_center_pads(parms, Align.RIGHT))
    ]

    # Define region to cut out from ground plane
    extpolys = [
           geo.extend_poly(parms["gap"], p, True)
                for (_, polys) in layers.iteritems()
                for p in polys]

    w = 0.5 * parms["width"]
    h = 0.5 * parms["height"]

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
    print("Wrote to '{}'".format(fileout))

    return 0

if __name__ == "__main__":
    # Command line parsing
    DESC = "Generate ion trap layout files from specification."
    DEFAULT_PATH = os.path.abspath(datetime.now().strftime(
            "./newtrap_%Y%m%d_%H%M%S.dxf"))

    parser = argparse.ArgumentParser(description=DESC)
    parser.add_argument("layout", metavar="LAYOUT", type=str, nargs="?",
            default=None, help="trap layout config file; see "
            "example_config.yaml for file format")
    parser.add_argument("-o", "--output", type=str, action="store",
            default=DEFAULT_PATH, help="output file")

    args = parser.parse_args()

    # Initialize parameters
    params = parameters.DEFAULT_PARAMS
    if args.layout is not None:
        with open(args.layout) as f:
            tree = yaml.safe_load(f)
            if tree["layout"] is not None:
                params.update(tree["layout"])

    # Keep the example config around
    if not os.path.exists(parameters.EXAMPLE_LAYOUT):
        with open(parameters.EXAMPLE_LAYOUT_TEMPL) as f, \
                open(parameters.EXAMPLE_LAYOUT, 'w') as g:
            s = Template(f.read())
            g.write(s.safe_substitute(parameters.DEFAULT_PARAMS))

    main(params, args.output)
