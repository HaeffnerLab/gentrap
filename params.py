import operator

DEFAULT_PARAMS = {
    # Overall dimensions of chip
    "width": 12000,
    "height": 12000,
    # Width of the empty gap between electrodes
    "gap": 10,
    # Width and length of center electrode
    "center_width": 320,
    "center_length": 11000,
    # Width of bridge from center electrode to bonding pad
    "center_bridge_width": 50,
    # Distance of center electrode pads to edge
    "center_pad_margin": 3000,
    # Number of DC electrodes per side
    "dc_count": 10,
    # DC electrode widths along the central axis
    "dc_widths": [400, 400, 400, 400, 400, 200, 400, 400, 400, 400],
    # DC electrode length away from the central axis
    "dc_length": 300,
    # Width of leads from electrodes to bonding pads
    "dc_lead_width": 50,
    # Separation between DC leads in vertical section
    "dc_lead_sep": 130,
    # Vertical separation from each bonding pad to the next
    "dc_pad_seps": [100, 100, 450, 100, 100, 100, 100, 100, 100],
    # Dimesnions of DC bonding pads
    "dc_pad_width": 400,
    "dc_pad_height": 400,
    # Distance of DC bonding pads from edge
    "dc_pad_margin": 100,
    # Vertical displacement of DC bonding pads from center
    "dc_pad_offset": 125,
    # Width of left and right RF electrodes
    "rf_width_left": 120,
    "rf_width_right": 120,
    # Length of both RFs
    "rf_length": 11500,
    # Width of bridge between RF electrode and bonding pad
    "rf_bridge_width": 150,
    # Dimensions of RF bonding pads
    "rf_pad_width": 400,
    "rf_pad_height": 400,
    # Distance of RF bonding pad from electrode
    "rf_pad_offset": 680,
    # Distance end of RF electrode to center electrode bonding
    # pad bridge
    "rf_center_bridge_sep": 10,
}

def calc_vertical_section_index(whichturn):
    """
    Takes a "whichturn" list of 1s and -1s and creates a list which
    ascends for every stretch of 1s and descends for every stretch of -1s.

    Example:
        >>> calc_vertical_section_index([-1, -1, -1, 1, 1, 1, 1])
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
    numelectrodes = params["dc_count"]
    dcwidths = params["dc_widths"]
    gap = params["gap"]
    padgaps = params["dc_pad_seps"]
    dcpadoffset = params["dc_pad_offset"]
    dcpadz = params["dc_pad_height"]

    # Calculate DC center positions

    # Constant offsets
    center_pos_offset = -0.5 * (sum(dcwidths) + (numelectrodes - 1) * gap)
    pad_center_pos_offset = dcpadoffset + 0.5 * dcpadz - 0.5 * (numelectrodes *
            dcpadz + sum(padgaps)) - (numelectrodes - 1) * gap

    # DC electrode absolute center positions
    dccenterpositions = [0.5 * dcwidths[i] + sum(dcwidths[:i]) + i * gap +
            center_pos_offset for i in range(numelectrodes)]

    # DC electrode bonding pad absolute center positioins
    dcpadcenterpositions = [i * (dcpadz + 2 * gap) + sum(padgaps[:i]) +
            pad_center_pos_offset for i in range(numelectrodes)]

    # Calculate bonding pad bridge layout

    sign = lambda x: 1 if x > 0 else -1 if x < 0 else 0

    # These tell which way to turn to go from the electrode to the
    # bonding pad, an unnecessarily complex system for sure.
    # -1 means turn "down" (to negative z), +1 means turn "up".
    whichturn = map(sign, map(operator.sub, dcpadcenterpositions,
            dccenterpositions))

    verticalsectionindex = calc_vertical_section_index(whichturn)

    return {
        "dc_center_positions": dccenterpositions,
        "dc_pad_center_positions": dcpadcenterpositions,
        "whichturn": whichturn,
        "vertical_section_index": verticalsectionindex,
    }

