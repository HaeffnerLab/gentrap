import operator

DEFAULT_PARAMS = {
    "width": 12000,
    "height": 12000,
    "gap": 10,
    "center_width": 320,
    "center_length": 11000,
    "center_bridge_width": 50,
    "center_pad_margin": 3000,
    "dc_count": 10,
    "dc_widths": [400, 400, 400, 400, 400, 200, 400, 400, 400, 400],
    "dc_length": 300,
    "dc_lead_width": 50,
    "dc_lead_sep": 130,
    "dc_pad_seps": [100, 100, 450, 100, 100, 100, 100, 100, 100],
    "dc_pad_width": 400,
    "dc_pad_height": 400,
    "dc_pad_margin": 100,
    "dc_pad_offset_left": 0,
    "dc_pad_offset_right": 0,
    "rf_width_left": 120,
    "rf_width_right": 120,
    "rf_length": 11500,
    "rf_bridge_width": 150,
    "rf_pad_width": 400,
    "rf_pad_height": 400,
    "rf_pad_offset": 680,
    "rf_center_bridge_sep": 0,
}
"""Default/sample trap layout parameters.

See 'example_layout.yaml' for documentation of each value. Said file
is generated by 'mkexample.py'."""

class Align:
    LEFT = -1
    CENTER = 0
    RIGHT = 1

# Faces for the center electrode.
def center_points(params):
    w = 0.5 * params["width"]
    h = 0.5 * params["height"]

    # Top to bottom
    y1 = 0.5 * params["rf_length"] + params["rf_center_bridge_sep"] + \
            params["gap"] + params["center_bridge_width"]
    y2 = y1 - params["center_bridge_width"]
    y3 = y1 - params["dc_pad_height"]
    y4 = -0.5 * params["center_length"]

    # Right to left
    x1 = w - params["center_pad_margin"]
    x2 = x1 - params["dc_pad_width"]
    x3 = 0.5 * params["center_width"]
    x4 = -x3
    x5 = -x2
    x6 = -x1

    xs = [x6, x6, x5, x5, x4, x4, x3, x3, x2, x2, x1, x1]
    ys = [y1, y3, y3, y2, y2, y4, y4, y2, y2, y3, y3, y1]
    ps = zip(xs, ys)

    # Error checking
    for (x, y) in ps:
        if abs(x) > w or abs(y) > h:
            raise RuntimeError("center electrode length exceeds chip size")

    return ps

def rf_points(params):
    rfpadx = params["rf_pad_width"]
    rfpadz = params["rf_pad_height"]
    rfwidthleft = params["rf_width_left"]
    rfwidthright = params["rf_width_right"]
    rfpadoffset = params["rf_pad_offset"]
    gap = params["gap"]
    bridgewidth = params["rf_bridge_width"]
    centerlength = params["center_length"]
    c = 0.5 * params["center_width"]
    l = 0.5 * params["rf_length"]

    x1 = -c - gap - rfwidthleft
    x2 = -rfpadoffset
    x3 = -rfpadoffset - rfpadx
    x4 = c + gap + rfwidthright
    x5 = c + gap
    x6 = -x5

    y1 = l
    y2 = -l + 0.5 * rfpadz + 0.5 * bridgewidth + gap
    y3 = -l + rfpadz
    y4 = -l
    y5 = -l + 0.5 * rfpadz - 0.5 * bridgewidth
    y6 = -0.5 * centerlength - gap

    xs = [x1, x1, x2, x2, x3, x3, x2, x2, x1, x1, x4, x4, x5, x5, x6, x6]
    ys = [y1, y2, y2, y3, y3, y4, y4, y5, y5, y4, y4, y1, y1, y6, y6, y1]
    ps = zip(xs, ys)

    w = 0.5 * params["width"]
    h = 0.5 * params["height"]
    for (x, y) in ps:
        if abs(x) > w or abs(y) > h:
            raise RuntimeError("rf electrode exceeds chip size")

    return ps

def vertical_section_index(whichturn):
    """
    Takes a list of 1s, 0s, and -1s and creates a list which ascends for
    every stretch of 1s and descends for every stretch of -1s.

    Example:
        >>> vertical_section_index([-1, -1, -1, 1, 1, 1, 1])
        [2, 1, 0, 0, 1, 2, 3]
    """

    my_range = lambda n: range(n) if n >= 0 else range(-n - 1, -1, -1)

    vsi = []
    count = 0
    for i in range(len(whichturn)):
        if whichturn[i] == 0:
            vsi += [0]
        else:
            count += whichturn[i]
            if i + 1 == len(whichturn) or whichturn[i] != whichturn[i + 1]:
                vsi += my_range(count)
                count = 0

    return vsi

# Calcuate dictionary of other layout parameters
def dc_params(params):
    numelectrodes = params["dc_count"]
    dcwidths = params["dc_widths"]
    gap = params["gap"]
    padgaps = params["dc_pad_seps"]
    dcpadoffsetl = params["dc_pad_offset_left"]
    dcpadoffsetr = params["dc_pad_offset_right"]
    dcpadz = params["dc_pad_height"]

    # DC electrode absolute center positions
    centerposoffs = -0.5 * (sum(dcwidths) + (numelectrodes - 1) * gap)
    dccenterpositions = [0.5 * dcwidths[i] + sum(dcwidths[:i]) + i * gap +
            centerposoffs for i in range(numelectrodes)]

    # DC electrode bonding pad absolute center positions
    padcenterposoffs = -0.5 * (numelectrodes * dcpadz + (numelectrodes - 1) * 2
            * gap + sum(padgaps)) + 0.5 * dcpadz
    dcpadcenterpositionsl = [i * (dcpadz + 2 * gap) + sum(padgaps[:i]) +
            dcpadoffsetl + padcenterposoffs for i in range(numelectrodes)]
    dcpadcenterpositionsr = [i * (dcpadz + 2 * gap) + sum(padgaps[:i]) +
            dcpadoffsetr + padcenterposoffs for i in range(numelectrodes)]

    # Calculate bonding pad bridge layout

    sign = lambda x: 1 if x > 0 else -1 if x < 0 else 0

    # These tell which way to turn to go from the electrode to the
    # bonding pad, an unnecessarily complex system for sure.
    # -1 means turn "down" (to negative z), +1 means turn "up".
    whichturnl = map(sign, map(operator.sub, dcpadcenterpositionsl,
            dccenterpositions))
    whichturnr = map(sign, map(operator.sub, dcpadcenterpositionsr,
            dccenterpositions))

    verticalsectionindexl = vertical_section_index(whichturnl)
    verticalsectionindexr = vertical_section_index(whichturnl)

    return {
        "dc_center_positions": dccenterpositions,
        "dc_pad_center_positions_left": dcpadcenterpositionsl,
        "dc_pad_center_positions_right": dcpadcenterpositionsr,
        "whichturn_left": whichturnl,
        "whichturn_right": whichturnr,
        "vertical_section_index_left": verticalsectionindexl,
        "vertical_section_index_right": verticalsectionindexr,
    }


# Calculate points for the ith DC electrode on the left or right side
def dc_points(params, side, i):
    width = params["dc_widths"][i]
    gap = params["gap"]
    dcleadspacing = params["dc_lead_sep"]
    dclength = params["dc_length"]
    dcpadx = params["dc_pad_width"]
    dcpadz = params["dc_pad_height"]
    rfwidthleft = params["rf_width_left"]
    rfwidthright = params["rf_width_right"]
    spacefromedge = params["dc_pad_margin"]
    w = 0.5 * params["width"]
    h = 0.5 * params["height"]
    c = 0.5 * params["center_width"]
    b = 0.5 * params["dc_lead_width"]

    dcparms = dc_params(params)

    if side == Align.LEFT:
        dcpcp = dcparms["dc_pad_center_positions_left"]
        whichturn = dcparms["whichturn_left"]
        vsi = dcparms["vertical_section_index_left"]
    else:
        dcpcp = dcparms["dc_pad_center_positions_right"]
        whichturn = dcparms["whichturn_right"]
        vsi = dcparms["vertical_section_index_right"]
    dccenterpositions = dcparms["dc_center_positions"]

    if side == Align.LEFT:
        x1 = c + 2 * gap + rfwidthleft
    else:
        x1 = c + 2 * gap + rfwidthright
    
    if whichturn[i] == 0:
        x2 = x1 + dclength
        x3 = w - spacefromedge - dcpadx
        x4 = w - spacefromedge

        y1 = dccenterpositions[i] - 0.5 * width
        y2 = dccenterpositions[i] - b
        y3 = dccenterpositions[i] - 0.5 * dcpadz
        y4 = dccenterpositions[i] + 0.5 * dcpadz
        y5 = dccenterpositions[i] + b
        y6 = dccenterpositions[i] + 0.5 * width

        xs = [x1, x2, x2, x3, x3, x4, x4, x3, x3, x2, x2, x1]
        ys = [y1, y1, y2, y2, y3, y3, y4, y4, y5, y5, y6, y6]
    else:
        x2 = x1 + dclength
        x3 = w - spacefromedge - dcpadx - (vsi[i] + 1.5) * dcleadspacing + \
                whichturn[i] * b
        x4 = w - spacefromedge - dcpadx
        x5 = w - spacefromedge
        x6 = w - spacefromedge - dcpadx - (vsi[i] + 1.5) * dcleadspacing - \
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
            raise RuntimeError("dc electrode {} exceeds chip size".format(i))

    return ps
