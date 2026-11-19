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
from part.shared import n64_contours as C  # noqa: E402


def _tapered_stadium(
    cx: float, cy: float, w0: float, d0: float, w1: float, d1: float, z0: float, h: float
) -> cq.Shape:
    """Vertical stadium frustum tapering from `(w0, d0)` at `z0` to `(w1, d1)` at `z0 + h`."""
    r0, r1 = 0.5 * w0, 0.5 * w1
    dy = 0.5 * (d0 - w0)  # semicircle centre offset along Y (constant for uniform wall taper)
    c_front = cq.Solid.makeCone(r0, r1, h, cq.Vector(cx, cy - dy, z0))
    c_back = cq.Solid.makeCone(r0, r1, h, cq.Vector(cx, cy + dy, z0))
    pts0 = [(-r0, -dy, 0.0), (r0, -dy, 0.0), (r0, dy, 0.0), (-r0, dy, 0.0)]
    pts1 = [(-r1, -dy, h), (r1, -dy, h), (r1, dy, h), (-r1, dy, h)]
    w_bot = cq.Wire.makePolygon([cq.Vector(cx + x, cy + y, z0 + z) for x, y, z in pts0 + [pts0[0]]])
    w_top = cq.Wire.makePolygon([cq.Vector(cx + x, cy + y, z0 + z) for x, y, z in pts1 + [pts1[0]]])
    mid = cq.Solid.makeLoft([w_bot, w_top], True)
    return c_front.fuse(c_back, mid)


def sleeve(cx: float) -> cq.Shape:
    """The oblong sleeve's tube (`5.10 x 6.50 mm`), from its foot up into the button's underside."""
    return C.stadium_prism(
        cx,
        D.BUTTON_POLE_Y,
        D.SLEEVE_OD,
        D.SLEEVE_LEN_Y_OD,
        D.SLEEVE_Z0,
        D.BUTTON_UNDERSIDE_Z + 0.05 - D.SLEEVE_Z0,
    )


def hole(cx: float) -> cq.Shape:
    """The oblong bore (`3.10 x 4.50 mm`) through the sleeve and up into the button."""
    bore = C.stadium_prism(
        cx,
        D.BUTTON_POLE_Y,
        D.SLEEVE_ID,
        D.SLEEVE_LEN_Y_ID,
        D.SLEEVE_Z0 - 0.2,
        D.BUTTON_POLE_HOLE_Z1 - (D.SLEEVE_Z0 - 0.2),
    )
    # 45 deg up to a flat roof at 29.5 (prints without support); a full cone would leave the
    # crown too thin over the hole
    roof = _tapered_stadium(
        cx,
        D.BUTTON_POLE_Y,
        D.SLEEVE_ID,
        D.SLEEVE_LEN_Y_ID,
        D.SLEEVE_ID - 1.20,
        D.SLEEVE_LEN_Y_ID - 1.20,
        D.BUTTON_POLE_HOLE_Z1,
        0.60,
    )
    return bore.fuse(roof)
