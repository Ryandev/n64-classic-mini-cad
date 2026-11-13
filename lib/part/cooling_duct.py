"""Printed cooling duct (REQ-04): fan seat, plenum, turning chamber and heat-sink cover in one part.

The fan blows down into a plenum floored by a printed plate (ahead of the board) and the Radxa X4
(over it). The plenum opens rearward into a chamber in front of the heat sink, and side skirts plus
a cover over the pin tips force the air through the 14 x 14 pin fins, front to rear. A pocket
under the fan's front strip, between the USB retainer brackets, keeps that part of the bore
blowing into the plenum too. The cover
rests on the pin tips and clamps the heat sink onto the N100 when the duct is screwed down.
Print in PETG Basic (the heat sink runs at ~60-70 C, near its limit), cover-side down. The
plenum floor is a separate plate (`floor_plate()`, `part/duct_floor.py`) glued into a frame
with a ledge.

Clearances measured against the assembly (2026-11-11): the left plenum wall stands inside the fan
footprint, clear of the power-switch tower (X <= -19.0); the front strip sits above the front
USB socket tops (Z 10.2) and meets the USB retainer bridge, which closes the fan's front
strip from below.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402

PROCESS = "fdm"
MANUFACTURE = "fdm"
PRINT_NORMAL = (0, 0, -1)  # cover face on the bed
# The plenum floor under the fan is a separate plate (`part/duct_floor.py`), glued in after
# printing (owner, 2026-11-13): printed upside down, the floor was a 34 x 16 mm roof over the fan
# bore and needed support inside the duct. Without it the duct prints support-free.
VISIBLE_FACES: tuple[str, ...] = ()

W = D.DUCT_WALL
CLEAR = 0.3  # heat sink to skirt, per side
X_IN_L = D.HS_X0 - CLEAR  # skirt inner faces
X_IN_R = D.HS_X0 + D.HS_W + CLEAR
X_OUT_L, X_OUT_R = X_IN_L - W, X_IN_R + W
X_FAN_WALL = D.FAN_X0  # left plenum wall, inside the fan footprint, ahead of Y_STEP
Y_STEP = -12.0  # left wall steps out to the skirt line here (ahead of the board edge)
Y_BRIDGE = -27.8  # USB retainer bridge rear face: it closes the fan's front strip below
Y_FRONT_OUT = -27.4  # front wall outer face: 0.1 behind the front USB sockets (rear at -27.5),
# 0.4 from the bridge
Y_FRONT_IN = Y_FRONT_OUT + W
# The fan reaches 5.6 mm in front of the front wall. Between the USB retainer brackets (inner
# faces X +-9.2, tops Z 18.4, which dam the bore above them) that strip is open to the tub floor,
# so a pocket carries it into the plenum: else 13 % of the blades blow past the heat sink.
X_POCKET = 9.0  # pocket side walls' outer faces, 0.2 inside the brackets
Y_POCKET_OUT = D.FAN_Y0 - 0.2  # pocket front wall under the fan frame
Y_PLATE0 = -25.6  # plate front edge, behind the tub/USB-socket tops at Y <= -25.8
Y_PLATE1 = -9.0  # plate rear edge, ahead of the RAM (Y >= -8.71) and over the board-edge parts
Y_REAR = D.HS_Y0 + D.HS_W  # heat sink rear face: air leaves into the case here
Z_HIGH = 10.4  # front strip floor: above the front USB sockets' tops (Z <= 10.2), measured by
# point classification (a clash bounding box had wrongly suggested tub structure up to Z 11.6)
Z_PLATE0 = D.RADXA_PCB_Z1 + 0.2  # 10.0, relieved over taller parts (BOARD_PART_RELIEFS)
Z_PLATE1 = Z_PLATE0 + W
Z_SKIRT = D.RADXA_PCB_Z1 + D.DUCT_SKIRT_GAP  # 10.3 over the board
Z_SKIRT_SOC = D.RADXA_PCB_Z1 + D.SOC_H + CLEAR  # 11.6 where the skirts cross the N100 package
Z_COVER0 = D.HS_Z1  # cover rests on the pin tips
Z_COVER1 = Z_COVER0 + D.DUCT_COVER_T
Z_SEAT1 = D.FAN_Z0  # fan seat plate top = fan bottom
Z_SEAT0 = Z_SEAT1 - W
# Small parts on the board's top side under the duct, measured on Radxa's own STEP (lib/step/
# build_radxa_x4.py) in console coordinates, each grown 0.2 mm: x0, x1, y0, y1, z0, z1. The
# duct can't read the board at build time (CI builds the printed parts without it), so the
# G13_COOL row is what proves these cover the real parts.
BOARD_PART_RELIEFS = (
    # a row of six pins under the plate's rear edge: out through the edge, or a lip is left
    (-15.56, -12.23, -10.53, Y_PLATE1 + 0.1, Z_PLATE0 - 0.1, 10.35),
    # a 0.8 x 1.6 mm part under the left skirt: through its full thickness, or a sliver is left
    (-22.98, X_IN_L + 0.1, -8.59, -6.59, Z_SKIRT - 0.1, 10.6),
    (-23.28, -21.28, 33.77, 34.97, Z_SKIRT - 0.1, 10.6),  # another, at the skirt's rear end
)
FAN_Y1 = D.FAN_Y0 + D.FAN_W
# The glued-in floor plate. It drops into a frame (the walls carried down to the plate's
# underside) and seats against a ledge; 0.15 mm a side is GBA's measured PETG locating fit,
# and the glue bead fills it and seals the plenum (notes/PRINTING.md).
FLOOR_GAP = 0.15
LEDGE_W, LEDGE_T = 1.0, 0.4
Y_FLOOR0 = Y_PLATE0 + W  # front frame strip's rear face


def _box(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> cq.Solid:
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


HS_STOP_GAP = 0.3  # each stop clears the heat sink's face by this much
HS_STOP_T, HS_STOP_W = 1.0, 1.5  # stop depth (Y) and width (X) at each corner
HS_STOP_Z0 = 12.0  # down to the sink's 2 mm base plate (Z 11.35..13.35)


def heatsink_stops() -> list[cq.Solid]:
    """Four corner stops that keep the heat sink on the die front-to-back (C9).

    The cover clamps it down and the skirts hold it sideways, but front-to-back only friction did
    (it could slide 5.7 mm forward, more than 6 back). The front pair hangs from the cover; the
    rear pair hooks in from the skirts past the sink's rear face, where the cover ends. At the
    corners only, so the air still leaves through the full pin field.
    """
    y_front, y_rear = D.HS_Y0 - HS_STOP_GAP, Y_REAR + HS_STOP_GAP
    stops = []
    for x_in, x_out, inward in ((X_IN_L, X_OUT_L, 1.0), (X_IN_R, X_OUT_R, -1.0)):
        x_post = sorted((x_in, x_in + inward * HS_STOP_W))
        x_skirt = sorted((x_out, x_in))
        stops.append(_box(*x_post, y_front - HS_STOP_T, y_front, HS_STOP_Z0, Z_COVER0 + 0.1))
        stops.append(_box(*x_post, y_rear, y_rear + HS_STOP_T, HS_STOP_Z0, Z_COVER1))
        stops.append(_box(*x_skirt, Y_REAR - 0.1, y_rear + HS_STOP_T, HS_STOP_Z0, Z_COVER1))
    return stops


def _floor_frame() -> list[cq.Solid]:
    z_ledge = (Z_PLATE1, Z_PLATE1 + LEDGE_T)
    x_fan_in = X_FAN_WALL + W
    return [
        _box(X_FAN_WALL, X_OUT_R, Y_PLATE0, Y_FLOOR0, Z_PLATE0, Z_PLATE1 + LEDGE_T),  # front
        # Ledge, LEDGE_W inside every framed edge (the rear edge is open to the board).
        _box(X_FAN_WALL, X_OUT_R, Y_FLOOR0, Y_FLOOR0 + LEDGE_W, *z_ledge),
        _box(x_fan_in, x_fan_in + LEDGE_W, Y_FLOOR0, Y_STEP, *z_ledge),
        _box(X_IN_L, x_fan_in, Y_STEP, Y_STEP + LEDGE_W, *z_ledge),
        _box(X_IN_L, X_IN_L + LEDGE_W, Y_STEP, Y_PLATE1, *z_ledge),
        _box(X_IN_R - LEDGE_W, X_IN_R, Y_FLOOR0, Y_PLATE1, *z_ledge),
    ]


def _board_cuts() -> list[cq.Shape]:
    """Reliefs over the board's screw heads and small top-side parts, cut from duct and plate."""
    # Relief over the board's screw heads that fall under the duct (front-right hole).
    heads = [
        cq.Solid.makeCylinder(
            D.BOARD_SCREW_HEAD_D / 2.0 + 0.2,
            D.BOARD_SCREW_HEAD_H + 0.3,
            cq.Vector(hx, hy, D.RADXA_PCB_Z1 - 0.1),
        )
        for hx, hy in D.radxa_hole_centres()
    ]
    # Reliefs over the board's small top-side parts under the plate and the left skirt, which
    # Radxa's own model has and the hand-edited one didn't (C10).
    return heads + [_box(*box) for box in BOARD_PART_RELIEFS]


def floor_plate() -> cq.Shape:
    """The plenum floor, printed flat and glued into the duct's frame (owner, 2026-11-13).

    An L: between the fan-line wall and the right skirt from the front strip back, and out to the
    left skirt behind the step. Rear edge open to the board, as the fused floor was.
    """
    g = FLOOR_GAP
    x_fan_in = X_FAN_WALL + W
    front = _box(x_fan_in + g, X_IN_R - g, Y_FLOOR0 + g, Y_PLATE1, Z_PLATE0, Z_PLATE1)
    left = _box(X_IN_L + g, x_fan_in + g + 1.0, Y_STEP + g, Y_PLATE1, Z_PLATE0, Z_PLATE1)
    return front.fuse(left).cut(*_board_cuts()).clean()


def get_shape() -> cq.Shape:
    """The duct body in console coordinates (the floor plate is `floor_plate()`)."""
    parts = [
        # Cover over the pin tips and the turning chamber, fan rear edge to heat sink rear face.
        _box(X_OUT_L, X_OUT_R, FAN_Y1, Y_REAR, Z_COVER0, Z_COVER1),
        # Right skirt: low over the plate/board, high in front of the plate.
        _box(X_IN_R, X_OUT_R, Y_PLATE0, Y_REAR, Z_SKIRT, Z_COVER1),
        _box(X_IN_R, X_OUT_R, Y_FRONT_OUT, Y_PLATE0, Z_HIGH, Z_SEAT1),
        # Left skirt from the step to the heat sink rear.
        _box(X_OUT_L, X_IN_L, Y_STEP, Y_REAR, Z_SKIRT, Z_COVER1),
        # Step wall joining the skirt line to the fan-line wall.
        _box(X_OUT_L, X_FAN_WALL + W, Y_STEP - W, Y_STEP, Z_PLATE0, Z_SEAT1),
        # Left fan-line wall: low over the plate, high in front of it.
        _box(X_FAN_WALL, X_FAN_WALL + W, Y_PLATE0, Y_STEP, Z_PLATE0, Z_SEAT1),
        _box(X_FAN_WALL, X_FAN_WALL + W, Y_FRONT_OUT, Y_PLATE0, Z_HIGH, Z_SEAT1),
        # Front wall, above the tub and socket tops, against the retainer bridge.
        _box(X_FAN_WALL, X_OUT_R, Y_FRONT_OUT, Y_FRONT_IN, Z_HIGH, Z_SEAT1),
        # Front strip floor, from the front wall back to the plate.
        _box(X_FAN_WALL, X_OUT_R, Y_FRONT_OUT, Y_PLATE0 + 0.1, Z_HIGH, Z_HIGH + W),
        # Frame for the glued-in floor plate: the skirts and the fan-line wall already reach its
        # underside (Z_SKIRT == Z_PLATE0); add a front strip and the ledge the plate seats on.
        *_floor_frame(),
        # Fan seat: closes the plenum top around the fan's bore, including the strip left of the
        # fan behind the step (else the plenum vents straight back to the intake side).
        _box(X_FAN_WALL, X_OUT_R, Y_FRONT_OUT, FAN_Y1, Z_SEAT0, Z_SEAT1),
        _box(X_OUT_L, X_FAN_WALL, Y_STEP - W, FAN_Y1, Z_SEAT0, Z_SEAT1),
        # Beside the fan's rear edge, seat up to cover: closes the chamber from the intake side
        # where the fan frame doesn't.
        _box(X_OUT_L, D.FAN_X0, FAN_Y1 - W, FAN_Y1, Z_SEAT0, Z_COVER1),
        _box(D.FAN_X0 + D.FAN_W, X_OUT_R, FAN_Y1 - W, FAN_Y1, Z_SEAT0, Z_COVER1),
    ]
    duct = parts[0].fuse(*parts[1:])
    cx, cy = D.FAN_X0 + D.FAN_W / 2.0, D.FAN_Y0 + D.FAN_W / 2.0
    # The bore opens only into the plenum: where the 28 mm circle reaches past the front wall it
    # would cut a slot through the wall's top (found by the COOL_SEAL flood check).
    disc = cq.Solid.makeCylinder(D.FAN_BORE_D / 2.0, W + 0.2, cq.Vector(cx, cy, Z_SEAT0 - 0.1))
    bore = disc.intersect(
        _box(X_FAN_WALL + W, X_IN_R, Y_FRONT_IN, FAN_Y1, Z_SEAT0 - 0.2, Z_SEAT1 + 0.2)
    )
    # The front pocket's share of the bore, through the seat strip on the old front wall.
    bore_front = disc.intersect(
        _box(
            -X_POCKET + W, X_POCKET - W, Y_POCKET_OUT + W, Y_FRONT_IN, Z_SEAT0 - 0.2, Z_SEAT1 + 0.2
        )
    )
    # The old front wall opens into the pocket between its side walls.
    opening = _box(
        -X_POCKET + W, X_POCKET - W, Y_FRONT_OUT - 0.1, Y_FRONT_IN + 0.1, Z_HIGH + W, Z_SEAT1 + 0.1
    )
    pocket = [
        _box(-X_POCKET, X_POCKET, Y_POCKET_OUT, Y_POCKET_OUT + W, Z_HIGH, Z_SEAT1),  # front
        _box(-X_POCKET, -X_POCKET + W, Y_POCKET_OUT, Y_FRONT_OUT, Z_HIGH, Z_SEAT1),  # left
        _box(X_POCKET - W, X_POCKET, Y_POCKET_OUT, Y_FRONT_OUT, Z_HIGH, Z_SEAT1),  # right
        _box(-X_POCKET, X_POCKET, Y_POCKET_OUT, Y_FRONT_OUT, Z_HIGH, Z_HIGH + W),  # floor
    ]
    # Skirts clear the N100 package where they cross it (it is 1.5 mm wider than the heat sink);
    # the relief runs through the whole skirt thickness so no sliver is left.
    soc_relief = _box(
        X_OUT_L - 0.1, X_OUT_R + 0.1, D.SOC_Y0 - CLEAR, D.SOC_Y1 + CLEAR, Z_SKIRT - 0.1, Z_SKIRT_SOC
    )
    # Notches round the lower tub's two posts in the front strip (X +-9.0..13.1, Y -27.4..-25.8,
    # up to Z 11.55); the posts themselves close the notches.
    posts = [
        _box(x0 - 0.2, x1 + 0.2, -27.6, -25.6, Z_HIGH - 0.1, 11.75)
        for x0, x1 in ((-13.1, -9.0), (9.0, 13.1))
    ]
    # The right post's notch eats into the right skirt; thicken the skirt outward beside it so a
    # full wall remains.
    patch = _box(13.3, 13.3 + W, -27.4, -25.6, Z_HIGH, 11.75)
    # The pocket is fused after the post notches, which would otherwise nick its side walls.
    return (
        duct.cut(bore, bore_front, opening, soc_relief, *posts, *_board_cuts())
        .fuse(patch, *pocket, *heatsink_stops())
        .clean()
    )
