"""The cooling duct's plenum floor: a flat plate glued into the duct after printing (REQ-04).

Printed upside down, the floor was a 34 x 16 mm roof over the fan bore and needed support inside
the duct; as its own plate it prints flat and the duct prints support-free (owner, 2026-11-13).
The geometry lives with the duct (`cooling_duct.floor_plate()`), which owns the frame it fits.
Glue with 2-part epoxy, both faces scuffed: the bead seals the plenum (notes/PRINTING.md).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from part import cooling_duct  # noqa: E402

PROCESS = "fdm"
MANUFACTURE = "fdm"
PRINT_NORMAL = (0, 0, -1)  # the plenum-side face on the bed; the board-side reliefs face up
VISIBLE_FACES: tuple[str, ...] = ()


def get_shape() -> cq.Shape:
    """The floor plate in console coordinates."""
    return cooling_duct.floor_plate()
