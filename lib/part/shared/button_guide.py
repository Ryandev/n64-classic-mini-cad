"""The lower guide shared by POWER and RESET: a sleeve under the button, sliding on a pole.

The chimney guides the button at the top; this sleeve guides it 3.5 mm below its underside, so the
two guides are far enough apart that the button can't rock (BTN_TILT). Their plays add up to more
than the pole can sit off the chimney's axis, so they never fight (BTN_STACK, datum.SLEEVE_CLEAR).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402


def sleeve(cx: float) -> cq.Shape:
    """The sleeve's tube, from its foot up into the button's underside (bored by `hole`)."""
    return cq.Solid.makeCylinder(
        D.SLEEVE_OD / 2.0,
        D.BUTTON_UNDERSIDE_Z + 0.05 - D.SLEEVE_Z0,
        cq.Vector(cx, D.BUTTON_POLE_Y, D.SLEEVE_Z0),
    )


def hole(cx: float) -> cq.Shape:
    """The bore through the sleeve and up into the button, round the pole at SLEEVE_CLEAR a side."""
    r = D.SLEEVE_ID / 2.0
    bore = cq.Solid.makeCylinder(
        r,
        D.BUTTON_POLE_HOLE_Z1 - (D.SLEEVE_Z0 - 0.2),
        cq.Vector(cx, D.BUTTON_POLE_Y, D.SLEEVE_Z0 - 0.2),
    )
    # 45 deg up to a flat roof at 29.5 (prints without support); a full cone would leave the
    # crown too thin over the hole
    roof = cq.Solid.makeCone(
        r, r - 0.60, 0.60, cq.Vector(cx, D.BUTTON_POLE_Y, D.BUTTON_POLE_HOLE_Z1)
    )
    return bore.fuse(roof)
