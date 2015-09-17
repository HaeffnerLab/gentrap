#!/usr/bin/env python
import argparse
from dxfwrite import DXFEngine as dxf
import os
from Polygon import Polygon
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
    w = 0.5 * parms["width"]
    h = 0.5 * parms["height"]
    layers = {}
    layers["0"] = layout.rf_points(parms)
    for i in range(n):
        layers[str(i + 1)] = layout.dc_points(parms, Align.LEFT, i)
        layers[str(i + n + 1)] = layout.dc_points(parms, Align.RIGHT, i)
    layers[str(2 * n + 1)] = layout.center_points(parms)

    # Workaround for GPC's bottom-up triangulization
    for (k, p) in layers.iteritems():
        layers[k] = flip(p)

    # Define region to cut out from ground plane
    extpolys = [
           geo.extend_poly(parms["gap"], p, True)
                for (_, p) in layers.iteritems()]

    gndplane = Polygon(flip([(-w, -h), (w, -h), (w, h), (-w, h)]))
    for p in extpolys:
        gndplane = gndplane - Polygon(p)

    layers["GROUND"] = gndplane

    # Turn all geometry into quads
    for (k, p) in layers.iteritems():
        # Mapping tristrip_to_quads gives a list of lists of quads,
        # which needs to be flattened
        layers[k] = [
                quad for quads in map(
                         geo.tristrip_to_quads,
                         Polygon(layers[k]).triStrip())
                     for quad in quads]

    # Render to DXF
    drawing = dxf.drawing(fileout)
    for (k, quads) in layers.iteritems():
        for q in quads:
            drawing.add(dxf.face3d(flip(q), layer=k))
    drawing.save()

    return 0

if __name__ == "__main__":
    # Command line parsing
    DESC = "Generate ion trap layout files from specification."
    DEFAULT_PATH = "example_layout.dxf"

    parser = argparse.ArgumentParser(description=DESC)
    parser.add_argument("layout", metavar="LAYOUT", type=str, nargs="?",
            default=None, help="trap layout config file; see "
            "example_config.yaml for file format")
    parser.add_argument("-o", "--output", type=str, action="store",
            default=None, help="output file")

    args = parser.parse_args()

    if args.output is None:
        if args.layout is None:
            args.output = DEFAULT_PATH
        else:
            args.output = os.path.splitext(args.layout)[0] + ".dxf"

    # Initialize parameters
    params = layout.DEFAULT_PARAMS
    if args.layout is not None:
        with open(args.layout) as f:
            tree = yaml.safe_load(f)
            if tree["layout"] is not None:
                params.update(tree)
            else :
                print("Layout file does not have a name - Using default parameters")

    main(params, args.output)
    print("Wrote to '{}'".format(args.output))
