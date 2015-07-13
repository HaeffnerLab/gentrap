from collections import namedtuple
from datetime import datetime
from dxfwrite import DXFEngine as dxf
from geo import *
import operator
import os
from Polygon import Polygon
import sys

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

def calc_vertical_section_index(whichturn):
    """
    Takes a "whichturn" list of 1s and -1s and creates a list which
    ascends for every stretch of 1s and descends for every stretch of -1s.
    Example:

        >> calc_vertical_secion_index([-1, -1, -1, 1, 1, 1, 1])
        [2, 1, 0, 0, 1, 2, 3]
    """
    # Do error checking for good measure
    for i in range(len(whichturn)):
        if whichturn[i] != 1 and whichturn[i] != -1:
            raise RuntimeError("calc_vertical_section_index: Invalid whichturn"
                    "index {}: {}".format(i, whichturn[i]))

    my_range = lambda n: range(n) if n >= 0 else range(-n - 1, -1, -1)

    vsi = []
    count = 0
    for i in range(len(whichturn)):
        count += whichturn[i]
        if i + 1 == len(whichturn) or whichturn[i] != whichturn[i + 1]:
            vsi += my_range(count)
            count = 0

    return vsi

# Calcuate dictionary of other layout parameters
def calc_extra_params(params):
    numelectrodes = params["numelectrodes"]
    dcwidths = params["dcwidths"]
    gap = params["gap"]
    padgaps = params["padgaps"]
    dcpadoffset = params["dcpadoffset"]
    dcpadz = params["dcpadz"]

    # Calculate DC center positions

    # Constant offsets
    center_pos_offset = -0.5 * (sum(dcwidths) + (numelectrodes - 1) * gap)
    pad_center_pos_offset = dcpadoffset + 0.5 * dcpadz - 0.5 * (numelectrodes *
            dcpadz + sum(padgaps)) - (numelectrodes - 1) * gap

    # DC electrode absolute center positions
    dccenterpositions = [0.5 * dcwidths[i] + sum(dcwidths[:i]) + i * gap +
            center_pos_offset for i in range(numelectrodes)]

    # DC electrode bonding pad absolute center positioins
    dcpadcenterpositionsleft = [i * (dcpadz + 2 * gap) + sum(padgaps[:i]) +
            pad_center_pos_offset for i in range(numelectrodes)]

    # useless or what?
    dcpadcenterpositionsright = dcpadcenterpositionsleft

    # Calculate bonding pad bridge layout

    sign = lambda x: 1 if x > 0 else -1 if x < 0 else 0

    # These tell which way to turn to go from the electrode to the
    # bonding pad, an unnecessarily complex system for sure.
    # -1 means turn "down" (to negative z), +1 means turn "up".
    whichturnleft = map(sign, map(operator.sub, dcpadcenterpositionsleft,
            dccenterpositions))
    whichturnright = map(sign, map(operator.sub, dcpadcenterpositionsright,
            dccenterpositions))

    verticalsectionindexleft = calc_vertical_section_index(whichturnleft)
    verticalsectionindexright = calc_vertical_section_index(whichturnright)

    return {
        "dccenterpositions": dccenterpositions,
        "dcpadcenterpositionsleft": dcpadcenterpositionsleft,
        "dcpadcenterpositionsright": dcpadcenterpositionsright,
        "whichturnleft": whichturnleft,
        "whichturnright": whichturnright,
        "verticalsectionindexleft": verticalsectionindexleft,
        "verticalsectionindexright": verticalsectionindexright
    }

class Align:
    BOTTOM = -2
    LEFT = -1
    CENTER = 0
    RIGHT = 1
    TOP = 2

# Faces for the center electrode.
def calc_center_points(params, side):
    d = 0.5 * params["centerwidth"]

    if side == Align.CENTER:
        x1 = -d
        x2 = d
    elif side == Align.RIGHT:
        x1 = 0.5 * params["gap"]
        x2 = d
    else:
        x1 = -0.5 * params["gap"]
        x2 = -d

    y1 = -0.5 * params["centerlength"]
    y2 = 0.5 * params["rflength"] + params["rfdcbondinggap"] + \
            params["bridgewidth"]

    xs = [x1, x2, x2, x1]
    ys = [y1, y1, y2, y2]
    ps = zip(xs, ys)

    # Error checking
    w = 0.5 * params["totalwidth"]
    h = 0.5 * params["totalheight"]
    for (x, y) in ps:
        if abs(x) > w or abs(y) > h:
            raise RuntimeError("calc_center_points: central electrode length "
                    "exceeds chip size")

    return ps

def calc_center_pads(params, side):
    if side == Align.LEFT:
        bpcp = params["dcpadcenterpositionsleft"]
    else:
        bpcp = params["dcpadcenterpositionsright"]

    w = 0.5 * params["totalwidth"]
    h = 0.5 * params["totalheight"]

    # Left edge of bridge
    x1 = 0.5 * params["centerwidth"]
    # Left edge of pad
    x2 = w - params["centerspacefromedge"] - params["dcpadx"]
    # Right edge of pad
    x3 = w - params["centerspacefromedge"]

    # Top of bridge/pad
    y1 = 0.5 * params["rflength"] + params["rfdcbondinggap"] + \
            params["bridgewidth"]
    # Bottom of bridge
    y2 = y1 - params["bridgewidth"]
    # Bottom of pad
    y3 = y1 - params["dcpadz"]

    xs = [x1, x1, x2, x2, x3, x3]
    ys = [y1, y2, y2, y3, y3, y1]

    if side == Align.LEFT:
        xs = map(operator.neg, xs)

    ps = zip(xs, ys)

    if side == Align.LEFT:
        ps.reverse()

    for (x, y) in ps:
        if abs(x) > w or abs(y) > h:
            raise RuntimeError("calc_center_pads: center electrod pad exceeds "
                    "chip size")

    return ps

def calc_rf_points(params):
    rfpadx = params["rfpadx"]
    rfpadz = params["rfpadz"]
    rfwidthleft = params["rfwidthleft"]
    rfwidthright = params["rfwidthright"]
    rfpadoffset = params["rfpadoffset"]
    gap = params["gap"]
    bridgewidth = params["bridgewidth"]
    centerlength = params["centerlength"]
    c = 0.5 * params["centerwidth"]
    l = 0.5 * params["rflength"]

    x1 = -c - gap - rfwidthleft
    x2 = -rfpadoffset
    x3 = -rfpadoffset - rfpadx
    x4 = c + gap + rfwidthright
    x5 = c + gap
    x6 = -x5

    y1 = l
    y2 = -l + 0.5 * rfpadz + 1.5 * bridgewidth + gap
    y3 = -l + rfpadz
    y4 = -l
    y5 = -l + 0.5 * rfpadz - 1.5 * bridgewidth
    y6 = -0.5 * centerlength - gap

    xs = [x1, x1, x2, x2, x3, x3, x2, x2, x1, x1, x4, x4, x5, x5, x6, x6]
    ys = [y1, y2, y2, y3, y3, y4, y4, y5, y5, y4, y4, y1, y1, y6, y6, y1]
    ps = zip(xs, ys)

    w = 0.5 * params["totalwidth"]
    h = 0.5 * params["totalheight"]
    for (x, y) in ps:
        if abs(x) > w or abs(y) > h:
            raise RuntimeError("calc_rf_points: rf electrode exceeds "
                    "chip size")

    return ps

# Calculate points for the ith DC electrode on the left or right side
def calc_dc_points(params, side, i):
    width = params["dcwidths"][i]
    dccenterpositions = params["dccenterpositions"]
    gap = params["gap"]
    dcleadspacing = params["dcleadspacing"]
    dclength = params["dclength"]
    dcpadx = params["dcpadx"]
    dcpadz = params["dcpadz"]
    rfwidthleft = params["rfwidthleft"]
    rfwidthright = params["rfwidthright"]
    spacefromedge = params["spacefromedge"]
    w = 0.5 * params["totalwidth"]
    h = 0.5 * params["totalheight"]
    c = 0.5 * params["centerwidth"]
    b = 0.5 * params["bridgewidth"]

    if side == Align.LEFT:
        x1 = c + 2 * gap + rfwidthleft
        dcpcp = params["dcpadcenterpositionsleft"]
        vsi = params["verticalsectionindexleft"]
        whichturn = params["whichturnleft"]
    else:
        x1 = c + 2 * gap + rfwidthright
        dcpcp = params["dcpadcenterpositionsright"]
        vsi = params["verticalsectionindexright"]
        whichturn = params["whichturnright"]
    
    x2 = x1 + dclength
    x3 = w - spacefromedge - dcpadx - (vsi[i] + 0.5) * dcleadspacing + \
            whichturn[i] * b
    x4 = w - spacefromedge - dcpadx
    x5 = w - spacefromedge
    x6 = w - spacefromedge - dcpadx - (vsi[i] + 0.5) * dcleadspacing - \
            whichturn[i] * b

    y1 = dccenterpositions[i] - 0.5 * width
    y2 = dccenterpositions[i] - b
    y3 = dcpcp[i] - b
    y4 = dcpcp[i] - 0.5 * dcpadz
    y5 = dcpcp[i] + 0.5 * dcpadz
    y6 = dcpcp[i] + b
    y7 = dccenterpositions[i] + b
    y8 = dccenterpositions[i] + 0.5 * width

    xs = [x1, x2, x2, x3, x3, x4, x4, x5, x5, x4, x4, x6, x6, x2, x2, x1]
    ys = [y1, y1, y2, y2, y3, y3, y4, y4, y5, y5, y6, y6, y7, y7, y8, y8]

    if side == Align.LEFT:
        xs = map(operator.neg, xs)

    ps = zip(xs, ys)

    if side == Align.LEFT:
        ps.reverse()

    for (x, y) in ps:
        if abs(x) > w or abs(y) > h:
            raise RuntimeError("calc_dc_points: DC electrode " + str(i) +
                    " exceeds chip size")

    return ps

# Points for pad to place SMD thermometer
def calc_therm_points(params, side):
    h = 0.5 * params["totalheight"]

    if side == Align.LEFT:
        offsx = params["thermpadoffsxleft"]
    else:
        offsx = params["thermpadoffsxright"]

    x1 = offsx
    x2 = offsx + params["thermpadx"]
    y1 = -h + params["thermpadz"]
    y2 = -h

    xs = [x1, x1, x2, x2]
    ys = [y1, y2, y2, y1]

    if side == Align.LEFT:
        xs = map(operator.neg, xs)

    ps = zip(xs, ys)

    if side == Align.LEFT:
        ps.reverse()

    return ps

def main(args):
    params = dict(DEFAULT_PARAMS)
    params.update(calc_extra_params(DEFAULT_PARAMS))

    # Get all electrode points
    layers = {}
    layers["0"] = [calc_rf_points(params)]
    for i in range(params["numelectrodes"]):
        layers[str(i + 1)] = [calc_dc_points(params, Align.LEFT, i)]
        layers[str(i + 11)] = [calc_dc_points(params, Align.RIGHT, i)]
    layers["21"] = [
        calc_center_points(params, Align.CENTER),
        calc_center_pads(params, Align.LEFT),
        calc_center_pads(params, Align.RIGHT)
    ]
    layers["22"] = [
        calc_therm_points(params, Align.LEFT),
        calc_therm_points(params, Align.RIGHT)
    ]

    # Define region to cut out from ground plane
    extpolys = [
            extend_poly(params["gap"], p) for (_, polys) in layers.iteritems()
                                          for p in polys]

    w = 0.5 * params["totalwidth"]
    h = 0.5 * params["totalheight"]

    gndplane = Polygon([(-w, -h), (w, -h), (w, h), (-w, h)])
    for p in extpolys:
        gndplane = gndplane - Polygon(p)

    layers["GROUND"] = [gndplane]

    # Turn all geometry into quads
    for k in layers.keys():
        # Each layer is a list of polys, and mapping tristrip_to_quads
        # gives a list of lists of quads, which needs to be flattened
        layers[k] = [
                quad for p in layers[k]
                     for quads in map(tristrip_to_quads, Polygon(p).triStrip())
                     for quad in quads]

    path = os.path.abspath(
            datetime.now().strftime("./newtrap_%Y%m%d_%H%M%S.dxf"))

    # Create DXF file
    drawing = dxf.drawing(path)
    for (k, quads) in layers.iteritems():
        for q in quads:
            drawing.add(dxf.face3d(q, layer=k))
    drawing.save()
    print("Wrote to '{}'".format(path))

    return 0

if __name__ == "__main__":
    main(sys.argv)
