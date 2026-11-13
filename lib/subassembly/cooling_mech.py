"""Active cooling subassembly (REQ-04): heat sink, fan, printed duct and hood, rubber feet.

Pairs with `lib/subassembly/cooling_check.py`.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from component import bumpon_sj5012, hsb26_343408, sunon_mf30060v2  # noqa: E402
from part import cooling_duct, cooling_hood  # noqa: E402


def bodies() -> list[tuple[str, cq.Shape]]:
    """The cooling parts by name, in console coordinates."""
    return [
        ("hsb26_heatsink", hsb26_343408.placed()),
        ("fan_mf30060v2", sunon_mf30060v2.envelope()),
        ("cooling_duct", cooling_duct.get_shape()),
        ("duct_floor", cooling_duct.floor_plate()),
        ("cooling_hood", cooling_hood.get_shape()),
        ("feet_sj5012", bumpon_sj5012.placed()),
    ]


def get_shape() -> cq.Shape:
    """Compound of every cooling part."""
    return cq.Compound.makeCompound([shape for _, shape in bodies()])
