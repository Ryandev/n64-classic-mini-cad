"""50%-scale N64 Reset Button Plunger (`lib/part/reset_button.py`, `J-04`, `AC-T18`).

Authentic Light Cool Grey stadium `RESET` push button seated in the sculpted right wing
thumb depression (`X = +32.32 mm`, `Y = -28.88 mm`) of `upper_shell`:
  - Flat underside stadium up-stop flange (`11.0 x 16.0 x 1.6 mm` at `Z = 25.40 mm`,
    `> 75%` bed contact with `PRINT_NORMAL = (0, 0, 1)`)
  - Stadium plunger shaft (`8.2 x 13.2 mm`) in `upper_shell`'s `8.7 x 13.7 mm` bore
    (`0.25 mm/side` radial sliding clearance, `1.5 mm` vertical actuation stroke)
  - Crowned by the authentic `R = 19.391 mm` Y-axis cylinder (`(+29.095, 0, 11.90)`) and
    3D-engraved `RESET` lettering (`shared/n64_text.py`)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402
from shared import n64_contours as C  # noqa: E402
from shared import n64_text as T  # noqa: E402

PROCESS = "fdm"
MANUFACTURE = "fdm"
PRINT_NORMAL = (0, 0, 1)
VISIBLE_FACES = ("+Z",)


def get_shape() -> cq.Shape:
    """Build the placed N64 stadium Reset Button Plunger solid in console coordinates."""
    flange = C.stadium_prism(
        D.RESET_BTN_X,
        D.CONTROLS_Y,
        D.RESET_FLANGE_W,
        D.RESET_FLANGE_D,
        D.RESET_Z0,
        D.RESET_FLANGE_T,
    )
    shaft_z0 = D.RESET_Z0 + D.RESET_FLANGE_T - 0.4
    shaft_raw = C.stadium_prism(
        D.RESET_BTN_X,
        D.CONTROLS_Y,
        D.RESET_SHAFT_W,
        D.RESET_SHAFT_D,
        shaft_z0,
        6.0,
    )
    # Authentic R = 19.391 mm Y-axis cylindrical crown matching Solid[0] of Console_N64.step (0.5x)
    crown_cyl = cq.Solid.makeCylinder(
        19.391,
        24.0,
        cq.Vector(29.095, D.CONTROLS_Y - 12.0, 11.90),
        cq.Vector(0.0, 1.0, 0.0),
    )
    cap_body = shaft_raw.intersect(crown_cyl)

    # Surface-conforming 0.22 mm RESET lettering across the centre of the button cap
    dy = D.CONTROLS_Y - (-28.88)
    surface_skin = cap_body.cut(cap_body.moved(cq.Location(cq.Vector(0.0, 0.0, -0.22))))
    glyphs_shifted = [
        g.moved(cq.Location(cq.Vector(0.0, dy, 0.0)))
        for g in T.reset_glyph_prisms(z0=28.0, height=6.0)
    ]
    glyph_cuts = cq.Compound.makeCompound(glyphs_shifted).intersect(surface_skin)

    # Coaxial Ø3.20 mm underside anti-tilt guide hole at (+32.32, -32.20, Z=25.40..29.85 mm)
    # engaging the Ø2.80 mm vertical guide pole on part/usb_retainer_bracket.py (0.20 mm/side fit)
    guide_hole = cq.Solid.makeCylinder(
        1.60,
        28.25 - 25.20,
        cq.Vector(D.RESET_BTN_X, -32.20, 25.20),
    ).fuse(
        cq.Solid.makeCone(
            1.60,
            0.0,
            1.60,
            cq.Vector(D.RESET_BTN_X, -32.20, 28.25),
        )
    )
    return flange.fuse(cap_body).cut(guide_hole, *glyph_cuts.Solids())
