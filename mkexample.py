#!/usr/bin/env python
"""Generates 'example_layout.yaml' from 'example_layout.yaml.templ' and
the default values in 'layout.py'"""

import layout
import os
from string import Template

EXAMPLE_LAYOUT = "example_layout.yaml"
EXAMPLE_LAYOUT_TEMPL = "example_layout.yaml.templ"

if __name__ == '__main__':
    if not os.path.exists(EXAMPLE_LAYOUT):
        with open(EXAMPLE_LAYOUT, 'w') as f:
             with open(EXAMPLE_LAYOUT_TEMPL) as g:
                t = Template(g.read())
                f.write(t.safe_substitute(layout.DEFAULT_PARAMS))
                print("Wrote to '{}'".format(EXAMPLE_LAYOUT))
