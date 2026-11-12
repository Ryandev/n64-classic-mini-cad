"""Omron SS-5GL subminiature snap-action microswitch with hinge lever (`omron_ss5gl.py`).

Shared GBA / N64 Classic Mini BOM component (`2x` used for momentary `POWER` `J-03` and
`RESET` `J-04` top-deck controls). Dimensions from Omron SS-series datasheet (`SS-5GL`,
hinge lever, solder terminals):
  - Body:             `19.8 x 6.4 x 10.2 mm`
  - Mounting holes:   `2x Ø2.35 mm` on `9.50 mm` pitch, `2.90 mm` up from body bottom
                      (`4.65 mm` left of body centre, `4.85 mm` right of body centre)
  - Pin plunger:      `2.35 mm` left of body centre (`7.50 mm` from left end)
  - Hinge lever:      `4.0 mm` wide x `0.30 mm` stainless blade, tips at `X = +7.50 mm`
  - Free Position:    `FP_max = 13.6 mm` above mounting holes (`+10.7 mm` above body bottom)
  - Operating Pos:    `OP = 8.8 +/- 0.8 mm` (`8.0 .. 9.6 mm`) above mounting holes
  - Overtravel:       `OVERTRAVEL_MIN = 1.2 mm` minimum safe travel past `OP`
  - Movement Diff:    `MD_max = 0.8 mm` maximum release hysteresis
  - Operating Force:  `OF_max = 0.49 N` (`50 gf`), Release Force `RF_min = 0.06 N` (`6 gf`)

Local coordinate frame of `get_shape()`:
  - Origin `(0, 0, 0)` on the mounting-hole centreline at body X/Y centre
  - `+X`: toward lever tip (`NC` end); `-X`: toward lever hinge (`COM` end)
  - `+Y`: across `6.4 mm` switch thickness
  - `+Z`: toward lever / actuation side (`-Z` toward solder terminals)
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402

BODY_LENGTH = 19.8
BODY_WIDTH = 6.4
BODY_HEIGHT = 10.2

HOLE_DIA = 2.35
HOLE_PITCH = 9.5
HOLE_Z_FROM_BOTTOM = 2.9
HOLE_LEFT_X = -4.65
HOLE_RIGHT_X = HOLE_LEFT_X + HOLE_PITCH  # +4.85 mm

PLUNGER_X = -2.35
PLUNGER_DIA = 2.0
PLUNGER_Z = 1.2

LEVER_PIVOT_X = -7.0
LEVER_PIVOT_Z = BODY_HEIGHT - HOLE_Z_FROM_BOTTOM + PLUNGER_Z + 0.1  # 8.6: hinge line
LEVER_TIP_X = 7.5
LEVER_WIDTH = 4.0
LEVER_THICK = 0.3
FREE_POSITION_MAX = 13.6
OPERATING_POSITION = 8.8
OPERATING_POSITION_TOL = 0.8
OVERTRAVEL_MIN = 1.2
MOVEMENT_DIFF_MAX = 0.8

OPERATING_FORCE_MAX_N = 0.49
RELEASE_FORCE_MIN_N = 0.06

TERMINAL_XS = (-7.3, 0.2, 7.7)  # COM, NO, NC
TERMINAL_WIDTH = 3.2
TERMINAL_THICK = 0.5
TERMINAL_DROP = 6.6
TERMINAL_HOLE_DIA = 1.2


def get_shape(lever_deflection: float = 0.0) -> cq.Shape:
    """Build the Omron SS-5GL solid in local switch coordinates.

    `lever_deflection` (mm at tip): `0.0` = free position (`z = +13.6 mm`),
    `3.2` = pre-loaded rest (`z = +10.4 mm`), `4.8` = nominal click (`OP = +8.8 mm`).
    """
    body_z_bot = -HOLE_Z_FROM_BOTTOM
    body_z_top = BODY_HEIGHT - HOLE_Z_FROM_BOTTOM

    body = (
        cq.Workplane("XY")
        .workplane(offset=body_z_bot)
        .box(BODY_LENGTH, BODY_WIDTH, BODY_HEIGHT, centered=(True, True, False))
        .val()
    )

    holes = [
        cq.Solid.makeCylinder(
            HOLE_DIA / 2.0,
            BODY_WIDTH + 2.0,
            cq.Vector(hx, -(BODY_WIDTH / 2.0 + 1.0), 0.0),
            cq.Vector(0.0, 1.0, 0.0),
        )
        for hx in (HOLE_LEFT_X, HOLE_RIGHT_X)
    ]
    body = body.cut(*holes)

    plunger_depression = min(PLUNGER_Z - 0.2, lever_deflection * 0.25)
    plunger = cq.Solid.makeCylinder(
        PLUNGER_DIA / 2.0,
        PLUNGER_Z - plunger_depression + 0.5,
        cq.Vector(PLUNGER_X, 0.0, body_z_top - 0.5),
    )

    hinge = (
        cq.Workplane("XY")
        .workplane(offset=body_z_top)
        .center(LEVER_PIVOT_X, 0.0)
        .box(2.2, LEVER_WIDTH, 1.4, centered=(True, True, False))
        .val()
    )

    tip_z = FREE_POSITION_MAX - lever_deflection
    root_z = LEVER_PIVOT_Z  # the lever turns about its hinge; only the plunger moves under it
    dx = LEVER_TIP_X - LEVER_PIVOT_X
    dz = tip_z - root_z
    blade_len = math.hypot(dx, dz)
    blade_angle = math.degrees(math.atan2(dz, dx))

    blade = (
        cq.Workplane("XY")
        .workplane(offset=root_z)
        .center(LEVER_PIVOT_X, 0.0)
        .transformed(rotate=(0.0, -blade_angle, 0.0))
        .box(blade_len, LEVER_WIDTH, LEVER_THICK, centered=(False, True, False))
        .val()
    )

    terminals = []
    for tx in TERMINAL_XS:
        tab = (
            cq.Workplane("XY")
            .workplane(offset=body_z_bot - TERMINAL_DROP)
            .center(tx, 0.0)
            .box(TERMINAL_THICK, TERMINAL_WIDTH, TERMINAL_DROP + 0.5, centered=(True, True, False))
            .val()
        )
        solder_hole = cq.Solid.makeCylinder(
            TERMINAL_HOLE_DIA / 2.0,
            TERMINAL_THICK + 1.0,
            cq.Vector(tx - (TERMINAL_THICK / 2.0 + 0.5), 0.0, body_z_bot - TERMINAL_DROP + 1.6),
            cq.Vector(1.0, 0.0, 0.0),
        )
        terminals.append(tab.cut(solder_hole))

    return body.fuse(plunger, hinge, blade, *terminals)


def placed_at(
    cx: float,
    cy: float = D.OMRON_Y,
    z_hole: float = D.OMRON_HOLE_Z,
    lever_deflection: float = D.OMRON_REST_DEFLECTION,
) -> cq.Shape:
    """Return an `Omron SS-5GL` placed under a top-deck control at `(cx, cy, z_hole)`.

    The switch is oriented with its `19.8 mm` length along `X` (mirrored on the left vs
    right wing so the lever hinge is toward the inner spine and the lever blade extends
    outward under the button centre `cx` at lever ratio `r = 0.72`).
    """
    sw = get_shape(lever_deflection=lever_deflection)
    contact_local_x = LEVER_PIVOT_X + D.OMRON_LEVER_RATIO * (LEVER_TIP_X - LEVER_PIVOT_X)
    if cx < 0.0:
        # Rotate 180 deg about Z so lever root is inboard (-X/+X symmetry)
        sw = sw.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), 180.0)
        x_origin = cx + contact_local_x
    else:
        x_origin = cx - contact_local_x
    return sw.moved(cq.Location(cq.Vector(x_origin, cy, z_hole)))


def lever_top_z(local_x: float, tip_h: float) -> float:
    """Height of the lever's top face above the mounting holes at `local_x`, tip at `tip_h`."""
    frac = (local_x - LEVER_PIVOT_X) / (LEVER_TIP_X - LEVER_PIVOT_X)
    return LEVER_PIVOT_Z + frac * (tip_h - LEVER_PIVOT_Z) + LEVER_THICK


RIDGE_W = 1.2  # the strip of a button's underside left to press the lever (C3)


def lever_pockets(cx: float) -> list[cq.Shape]:
    """Pockets in a button's underside over its switch lever, either side of a ridge at `cx` (C3).

    Only the ridge, under the button centre (`OMRON_LEVER_RATIO` along the lever), touches the
    lever: towards the tip the lever rises at rest, towards the hinge it rises once the tip has
    dropped below the hinge, and a flat underside would press it there instead.
    """
    contact_x = LEVER_PIVOT_X + D.OMRON_LEVER_RATIO * (LEVER_TIP_X - LEVER_PIVOT_X)
    toward_tip = -1.0 if cx < 0.0 else 1.0  # placed_at mirrors the left switch
    w = LEVER_WIDTH + 1.2
    z0 = D.BUTTON_UNDERSIDE_Z - 0.1
    ceiling = D.RESET_Z0 + 0.4  # above the lever tip's top face at rest (25.5)
    half = RIDGE_W / 2.0
    tip_reach = LEVER_TIP_X - contact_x + 0.5  # 0.9 mm of wall left at the button's rounded end
    spans = ((half, half + tip_reach - half), (-half - 6.0, -half))  # (start, end) along the lever
    out = []
    for a, b in spans:
        lo, hi = sorted((cx + toward_tip * a, cx + toward_tip * b))
        out.append(
            cq.Solid.makeBox(hi - lo, w, ceiling - z0, cq.Vector(lo, D.OMRON_Y - w / 2.0, z0))
        )
    return out
