"""50%-scale N64 Momentary Power Push Button (`lib/part/power_slider.py`, `J-03`, `REQ-08`).

Authentic Light Cool Grey stadium `POWER` momentary push button seated in the sculpted
left wing thumb depression (`X = -32.32 mm`, `Y = -28.88 mm`) of `upper_shell`:
  - Identical button profile to `reset_button.py` (transverse slider nub removed so
    `POWER` and `RESET` share the exact same smooth cylindrical-crowned stadium button cap)
  - Flat underside stadium up-stop flange (`11.0 x 17.2 x 1.6 mm` at `Z = 25.40 mm`), with a
    `Ø5.1 mm` guide sleeve below it on the bracket's pole (`shared/button_guide.py`); printed crown
    up standing on the sleeve, the flange on PLA-interface support
  - Stadium plunger shaft (`8.5 x 14.5 mm`) in `upper_shell`'s `8.94 x 14.94 mm` bore
    (`0.22 mm/side` radial sliding clearance, `2.10 mm` stroke to its stops, onto
    an `Omron SS-5GL` hinge-lever microswitch)
  - Crowned by the authentic `R = 19.391 mm` Y-axis cylinder (`(-29.095, 0, 11.90)`) and
    3D-engraved `POWER` lettering (`shared/n64_text.py`) centered on the cap
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402
from component import omron_ss5gl  # noqa: E402
from shared import button_guide  # noqa: E402
from shared import n64_contours as C  # noqa: E402
from shared import n64_text as T  # noqa: E402

PROCESS = "fdm"
MANUFACTURE = "fdm"
PROFILE = "fdm_petg_x2d"  # process/profiles.py: allowances added at print time
PRINT_NORMAL = (0, 0, 1)
VISIBLE_FACES = ("+Z",)
# Printed crown up, it stands on its guide sleeve (shared/button_guide.py): the flange's underside
# is held by support, PETG body with a PLA interface (owner's rule; notes/PRINTING.md). That face
# is hidden inside the console, and only the switch lever touches it, where the ~0.10 mm a
# supported face comes out proud costs 0.10 of the 0.26 mm release margin (OMRON_ACT).
SUPPORT_MM2 = 125.0  # 116 measured by layers, 2026-11-17
# The sleeve's ring is the only face on the bed (13 of 189 mm^2); the 8 mm brim the slicer
# requires (slicing/bambu.py) holds it down, and the part is short (9.7 mm over an 11 mm base).
MIN_BED_RATIO = 0.06


def get_shape() -> cq.Shape:
    """Build the placed N64 stadium Momentary Power Button Plunger solid in console coordinates."""
    flange = C.stadium_prism(
        D.POWER_SLIDER_X,
        D.CONTROLS_Y,
        D.SLIDER_FLANGE_W,
        D.SLIDER_FLANGE_D,
        D.SLIDER_Z0,
        D.SLIDER_FLANGE_T,
    )
    shaft_z0 = D.SLIDER_Z0 + D.SLIDER_FLANGE_T - 0.4
    shaft_raw = C.stadium_prism(
        D.POWER_SLIDER_X,
        D.CONTROLS_Y,
        D.SLIDER_NECK_W,
        D.SLIDER_NECK_D,
        shaft_z0,
        6.0,
    )

    # Stadium shaft/cap crowned by the authentic R = 19.391 mm Y-axis cylinder (matching Reset)
    crown_cyl = cq.Solid.makeCylinder(
        19.391,
        24.0,
        cq.Vector(-29.095, D.CONTROLS_Y - 12.0, 11.90),
        cq.Vector(0.0, 1.0, 0.0),
    )
    cap_body = shaft_raw.intersect(crown_cyl)

    # Surface-conforming 0.22 mm POWER lettering centered across the smooth stadium cap
    # (+1.65 mm in +Y aligns POWER's Y centre -32.22 + 1.65 = -30.57 mm with RESET's -30.57 mm)
    dy = (D.CONTROLS_Y - (-28.88)) + 1.65
    surface_skin = cap_body.cut(cap_body.moved(cq.Location(cq.Vector(0.0, 0.0, -0.22))))
    glyphs_shifted = [
        g.moved(cq.Location(cq.Vector(0.0, dy, 0.0)))
        for g in T.power_glyph_prisms(z0=28.0, height=6.0)
    ]
    glyph_cuts = cq.Compound.makeCompound(glyphs_shifted).intersect(surface_skin)

    # Flat underside 0.33 mm lower, pocketed over the lever's outer part: the pocket's edge
    # presses the switch lever under the button centre (C3)
    pad = C.stadium_prism(
        D.POWER_SLIDER_X,
        D.CONTROLS_Y,
        D.SLIDER_FLANGE_W,
        D.SLIDER_FLANGE_D,
        D.BUTTON_UNDERSIDE_Z,
        D.RESET_Z0 - D.BUTTON_UNDERSIDE_Z + 0.05,
    )
    pockets = omron_ss5gl.lever_pockets(D.POWER_SLIDER_X)
    # Sleeve on the guide pole: the button's lower guide (shared/button_guide.py, BTN_TILT)
    return flange.fuse(cap_body, pad, button_guide.sleeve(D.POWER_SLIDER_X)).cut(
        button_guide.hole(D.POWER_SLIDER_X), *pockets, *glyph_cuts.Solids()
    )
