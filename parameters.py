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
    "rf_center_bridge_sep": 0,
}

EXAMPLE_LAYOUT = "example_layout.yaml"
EXAMPLE_LAYOUT_TEMPL = "example_layout.yaml.templ"

