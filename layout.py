import operator

class Align:
    BOTTOM = -2
    LEFT = -1
    CENTER = 0
    RIGHT = 1
    TOP = 2

# Faces for the center electrode.
def calc_center_points(params, side):
    d = 0.5 * params["center_width"]

    if side == Align.CENTER:
        x1 = -d
        x2 = d
    elif side == Align.RIGHT:
        x1 = 0.5 * params["gap"]
        x2 = d
    else:
        x1 = -0.5 * params["gap"]
        x2 = -d

    y1 = -0.5 * params["center_length"]
    y2 = 0.5 * params["rf_length"] + params["rf_center_bridge_sep"] + \
            params["center_bridge_width"]

    xs = [x1, x2, x2, x1]
    ys = [y1, y1, y2, y2]
    ps = zip(xs, ys)

    # Error checking
    w = 0.5 * params["width"]
    h = 0.5 * params["height"]
    for (x, y) in ps:
        if abs(x) > w or abs(y) > h:
            raise RuntimeError("calc_center_points: central electrode length "
                    "exceeds chip size")

    return ps

def calc_center_pads(params, side):
    w = 0.5 * params["width"]
    h = 0.5 * params["height"]

    # Left edge of bridge
    x1 = 0.5 * params["center_width"]
    # Left edge of pad
    x2 = w - params["center_pad_margin"] - params["dc_pad_width"]
    # Right edge of pad
    x3 = w - params["center_pad_margin"]

    # Top of bridge/pad
    y1 = 0.5 * params["rf_length"] + params["rf_center_bridge_sep"] + \
            params["center_bridge_width"]
    # Bottom of bridge
    y2 = y1 - params["center_bridge_width"]
    # Bottom of pad
    y3 = y1 - params["dc_pad_height"]

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
            raise RuntimeError("calc_rf_points: rf electrode exceeds "
                    "chip size")

    return ps

# Calculate points for the ith DC electrode on the left or right side
def calc_dc_points(params, side, i):
    width = params["dc_widths"][i]
    dccenterpositions = params["dc_center_positions"]
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

    dcpcp = params["dc_pad_center_positions"]
    vsi = params["vertical_section_index"]
    whichturn = params["whichturn"]

    if side == Align.LEFT:
        x1 = c + 2 * gap + rfwidthleft
    else:
        x1 = c + 2 * gap + rfwidthright
    
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
            raise RuntimeError("calc_dc_points: DC electrode " + str(i) +
                    " exceeds chip size")

    return ps
