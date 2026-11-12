"""Separately-printed USB-A Top Retainer & Button Travel-Stop Bracket (`usb_retainer_bracket.py`).

Printed flat on its rear `+Y` face (`PRINT_NORMAL = (0, 1, 0)`, zero supports, 100% vertical walls,
`2` identical instances per console — Right `P3+P4 / Reset` is a `180 deg` Z-rotation of Left
`P1+P2 / Power`) and glued onto the `Z = 11.55 mm` shelves of `lower_tub`'s 3 vertical USB-A
cradle walls after the 4 `TE Connectivity 292303-7` USB-A receptacles are dropped in from `+Z`:
  - Solves physical assembly: the 4 USB-A receptacles (`Z = 17.45 mm` front EMI flange at
    `Y = -41.70 mm` and `Z = 6.08 mm` downward retention legs at `Y = -32.22 .. -30.00 mm`) drop
    straight down from `+Z` into `lower_tub` first; then each `usb_retainer_bracket` drops down over
    the pair of USB-A shells, registers forward against `lower_tub`'s `Z = 12.94 mm` shoulders at
    `Y = -36.70 mm` (`0.10 mm` clearance), and glues onto the 3 `Z = 11.55 mm` wall shelves
  - Positive `+Z` USB-A lock: `31.60 x 8.80 x 1.60 mm` bridge (`Y = -36.60 .. -27.80 mm`,
    `Z = 16.85 .. 18.45 mm`) clamps across the `Z = 16.70 mm` top face of all 4 USB-A receptacles
    with `0.15 mm` clearance
  - Extended `8.80 mm` front/mid button travel-stop shelf (`Y = -36.60 .. -27.80 mm`,
    `Z = 18.45 .. BUTTON_STOP_Z` at `X = +-32.32 mm`): extends `Face854` all the way back to
    `Y = -27.80 mm` (`0.45 mm` ahead of the `Omron SS-5GL` switch body at `Y = -27.35 mm`),
    preventing front-heavy button presses or spring return from tilting or pushing `POWER`/`RESET`
    into the shell
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402

PROCESS = "fdm"
MANUFACTURE = "fdm"
PRINT_NORMAL = (0, 1, 0)
VISIBLE_FACES = ()

BRACKET_Y0 = -36.60
BRACKET_DY = 8.80  # Y = -36.60 .. -27.80 mm (0.45 mm ahead of Omron SS-5GL at Y = -27.35 mm)
POLE_Y = BRACKET_Y0 + 0.5 * BRACKET_DY  # -32.20 mm (exact midpoint of Face70 for 180-deg symmetry)
POLE_R = 1.40  # Ø2.80 mm vertical guide pole (0.20 mm/side fit in Ø3.20 mm button underside hole)
LEG_Z0 = 11.60  # 0.05 mm glue gap above lower_tub's Z = 11.55 mm cradle wall shelf
BRIDGE_Z0 = 16.85  # 0.15 mm clearance above Z = 16.70 mm USB-A top metal shell
BRIDGE_Z1 = 18.45
STOP_Z1 = D.BUTTON_STOP_Z  # button stroke limit below its Z = 25.40 mm bottom face
POLE_CYL_Z1 = 26.50
POLE_TIP_Z1 = 27.10  # 3.65 mm tall pole (engaged 1.70 mm at rest, 3.60 mm at full press)


def _left_bracket() -> cq.Shape:
    """Build the Left (`P1+P2 / Power`, `bx = -25.0 mm`, `cx = -32.32 mm`) retainer bracket."""
    bx = D.FRONT_BAY_XS[0]  # -25.0 mm
    cx = D.POWER_SLIDER_X  # -32.32 mm
    bridge = cq.Solid.makeBox(
        31.60,
        BRACKET_DY,
        BRIDGE_Z1 - BRIDGE_Z0,
        cq.Vector(bx - 15.80, BRACKET_Y0, BRIDGE_Z0),
    )
    leg_out = cq.Solid.makeBox(
        1.50,
        BRACKET_DY,
        (BRIDGE_Z0 + 0.20) - LEG_Z0,
        cq.Vector(bx - 15.80, BRACKET_Y0, LEG_Z0),
    )
    leg_mid = cq.Solid.makeBox(
        1.70,
        BRACKET_DY,
        (BRIDGE_Z0 + 0.20) - LEG_Z0,
        cq.Vector(bx - 0.85, BRACKET_Y0, LEG_Z0),
    )
    leg_in = cq.Solid.makeBox(
        1.50,
        BRACKET_DY,
        (BRIDGE_Z0 + 0.20) - LEG_Z0,
        cq.Vector(bx + 14.30, BRACKET_Y0, LEG_Z0),
    )
    stop_block = cq.Solid.makeBox(
        5.00,
        BRACKET_DY,
        STOP_Z1 - (BRIDGE_Z1 - 0.20),
        cq.Vector(cx - 2.50, BRACKET_Y0, BRIDGE_Z1 - 0.20),
    )
    pole_cyl = cq.Solid.makeCylinder(
        POLE_R,
        POLE_CYL_Z1 - (STOP_Z1 - 0.20),
        cq.Vector(cx, POLE_Y, STOP_Z1 - 0.20),
    )
    pole_tip = cq.Solid.makeCone(
        POLE_R,
        0.80,
        POLE_TIP_Z1 - POLE_CYL_Z1,
        cq.Vector(cx, POLE_Y, POLE_CYL_Z1),
    )
    return bridge.fuse(leg_out, leg_mid, leg_in, stop_block, pole_cyl, pole_tip)


def bracket_at(bay_x: float = D.FRONT_BAY_XS[0]) -> cq.Shape:
    """Return the placed bracket at `bay_x` (`-25.0` Left or `+25.0` Right via 180-deg Z-rot)."""
    left = _left_bracket()
    if bay_x < 0.0:
        return left
    y_mid = BRACKET_Y0 + 0.5 * BRACKET_DY  # -32.20 mm
    return left.rotate(cq.Vector(0.0, y_mid, 0.0), cq.Vector(0.0, y_mid, 1.0), 180.0)


def brackets() -> list[cq.Shape]:
    """Return both Left (`P1+P2 / Power`) and Right (`P3+P4 / Reset`) placed brackets."""
    return [bracket_at(D.FRONT_BAY_XS[0]), bracket_at(D.FRONT_BAY_XS[1])]


def get_shape() -> cq.Shape:
    """Return a single manifold solid (`Left` orientation) for STEP export and `plate.py`."""
    return _left_bracket()
