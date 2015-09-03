#!/usr/bin/env python
import argparse
import sys

import dxfgrabber
from dxfwrite import DXFEngine
from Polygon import Polygon

import geo

# This utility has a lot of common functionality with gentrap.py, so you
# should see that script too.
def main(filein, fileout, width, height, gap):
    d = dxfgrabber.read(filein)

    def flipxy(p):
        return (p[1], p[0])

    layers = {}
    for r in d.entities:
        if not r.layer in layers:
            layers[r.layer] = []
        layers[r.layer].append(map(flipxy, r.points))

    polys_to_cut = []
    for (_, ps) in layers.iteritems():
        polys_to_cut += map(lambda p: geo.extend_poly(gap, p, False), ps)

    h = height / 2.0
    w = width / 2.0

    gndplane = Polygon([(h, w), (-h, w), (-h, -w), (h, -w)])

    for p in polys_to_cut:
        gndplane = gndplane - Polygon(p)

    # Polygon.triStrip() returns a list of tristrips which need to be
    # turned into quads, and the list needs to be flattened.
    layers["GROUND"] = [
            quad for quads in map(
                geo.tristrip_to_quads,
                gndplane.triStrip())
            for quad in quads]

    drawing = DXFEngine.drawing(fileout)
    for (l, qs) in layers.iteritems():
        for q in qs:
            drawing.add(DXFEngine.face3d(map(flipxy, q), layer=l))
    drawing.save()

if __name__ == '__main__':
    DESC = "Cut out the ground plane for an electrode layout."

    parser = argparse.ArgumentParser(description=DESC)
    parser.add_argument('layout', metavar='LAYOUT', type=str, nargs='?',
            help="DXF file containing just the electrode layout")
    parser.add_argument('output', metavar='OUTPUT', type=str, nargs='?',
            help="Output DXF file")
    parser.add_argument('width', metavar='WIDTH', type=int, nargs='?',
            help="Width of the ground plane to cut out")
    parser.add_argument('height', metavar='HEIGHT', type=int, nargs='?',
            help="Height of the ground plane to cut out")
    parser.add_argument('gap', metavar='GAP', type=int, nargs='?',
            help="Spacing between electrodes and ground plane")

    if len(sys.argv) != 6:
        parser.print_help()
        sys.exit()

    args = parser.parse_args()

    print(args.layout)

    main(file(args.layout), args.output, args.width, args.height, args.gap)
    print("Wrote to {}".format(args.output))
