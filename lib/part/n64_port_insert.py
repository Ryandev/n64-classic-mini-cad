"""Separately-printed shallow N64 Controller Port Insert (`lib/part/n64_port_insert.py`, `J-08`).

Light Cool Grey 50%-scale replica of the original N64 controller socket (`Ø10.88 mm` outer bezel,
`2.00 mm` total depth) printed flat on its `+Y` rear glue face (`PRINT_NORMAL = (0, -1, 0)`)
and bonded into the `Ø8.2 x 0.45 mm` locating pockets on the front of each hinged
`front_port_cover` (`4` inserts total: `P1..P4` at `X = -32.6, -17.4, +17.4, +32.6 mm`).

Geometric detail (measured from `Console_N64.step` `0.5x` controller sockets):
  - Rear locating boss (`Ø7.80 x 0.40 mm`) seating into `front_port_cover` (`0.20 mm/side`, `J-08`)
  - Authentic circular outer N64 bezel (`Ø10.88 x 1.60 mm`)
  - `0.65 mm` deep D-shaped socket recess (`Ø7.88 mm` arc + flat bottom keyway chord)
  - Inner D-shaped 3-pin connector island (`Ø5.88 mm` arc + flat bottom chord)
  - 3 tubular pin barrels (`Ø1.68 mm` OD / `Ø0.56 mm` ID at `dx = -1.55, 0.0, +1.55 mm`)
  - Player `1..4` blind-mate tactile dot pips (`1..4` pips along the lower outer rim)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet  # noqa: E402

PROCESS = "fdm"
MANUFACTURE = "fdm"
PRINT_NORMAL = (0, -1, 0)
VISIBLE_FACES = ("-Y",)


def _d_cylinder_plus_y(
    x: float,
    y0: float,
    z: float,
    radius: float,
    depth_y: float,
    flat_bottom_dz: float,
) -> cq.Shape:
    """Cylinder along `+Y` (`y0` to `y0 + depth_y`) clipped flat below `z - flat_bottom_dz`."""
    cyl = cq.Solid.makeCylinder(
        radius,
        depth_y,
        cq.Vector(x, y0, z),
        cq.Vector(0.0, 1.0, 0.0),
    )
    clip_box = cq.Solid.makeBox(
        radius * 2.4,
        depth_y + 0.4,
        radius * 2.0,
        cq.Vector(x - radius * 1.2, y0 - 0.2, z - flat_bottom_dz - radius * 2.0),
    )
    return cyl.cut(clip_box)


def insert_at(port_x: float, player_num: int = 1) -> cq.Shape:
    """Build one shallow N64 controller port insert at `port_x` for `player_num` (`1..4`)."""
    y_cover_front = D.FRONT_BAY_Y0
    y_flange_back = y_cover_front - D.PORT_INSERT_GAP_Y
    y_boss_back = y_flange_back + D.PORT_INSERT_BOSS_H
    y_front = y_flange_back - D.PORT_INSERT_BEZEL_H
    zc = D.USB_A_Z_CENTRE

    # 1. Rear locating boss (Ø7.80 x 0.40 mm) + outer circular N64 bezel (Ø10.88 x 1.52 mm)
    #    with authentic R = 0.50 mm front -Y circular rim fillet (Face[151] of Console_N64.step)
    boss = cq.Solid.makeCylinder(
        D.PORT_INSERT_BOSS_D / 2.0,
        D.PORT_INSERT_BOSS_H,
        cq.Vector(port_x, y_boss_back, zc),
        cq.Vector(0.0, -1.0, 0.0),
    )
    bezel_raw = cq.Solid.makeCylinder(
        D.PORT_INSERT_OD / 2.0,
        D.PORT_INSERT_BEZEL_H,
        cq.Vector(port_x, y_flange_back, zc),
        cq.Vector(0.0, -1.0, 0.0),
    )
    mf = BRepFilletAPI_MakeFillet(bezel_raw.wrapped)
    for edge in bezel_raw.Edges():
        eb = edge.BoundingBox()
        if abs(eb.ymin - y_front) < 1e-3 and abs(eb.ymax - y_front) < 1e-3 and eb.xlen > 8.0:
            mf.Add(0.50, edge.wrapped)
    mf.Build()
    bezel = cq.Shape.cast(mf.Shape())
    outer = boss.fuse(bezel)

    # 2. Cut 0.65 mm deep D-shaped socket cavity into the front -Y face (Face[1820, 198, 156])
    cavity_depth = 0.65
    cavity = _d_cylinder_plus_y(
        port_x,
        y_front - 0.1,
        zc,
        radius=3.938,
        depth_y=cavity_depth + 0.1,
        flat_bottom_dz=2.45,
    )
    carved = outer.cut(cavity)

    # 3. Fuse inner raised D-shaped connector island (Face[194, 196])
    y_cavity_floor = y_front + cavity_depth
    island_h = 0.52
    y_island_front = y_cavity_floor - island_h
    island = _d_cylinder_plus_y(
        port_x,
        y_island_front,
        zc,
        radius=2.938,
        depth_y=island_h + 0.15,
        flat_bottom_dz=1.55,
    )
    with_island = carved.fuse(island)

    # 4. Cut 3 circular pin wells + Player 1..4 dot pips
    pin_cuts = [
        cq.Solid.makeCylinder(
            0.46,
            0.38,
            cq.Vector(port_x + dx, y_island_front - 0.05, zc + 0.15),
            cq.Vector(0.0, 1.0, 0.0),
        )
        for dx in (-1.55, 0.0, 1.55)
    ]
    n_pips = max(1, min(4, player_num))
    pip_pitch = 1.00
    pip_x0 = -0.5 * (n_pips - 1) * pip_pitch
    for idx in range(n_pips):
        pin_cuts.append(
            cq.Solid.makeCylinder(
                0.25,
                0.22,
                cq.Vector(port_x + pip_x0 + idx * pip_pitch, y_front - 0.05, zc - 4.45),
                cq.Vector(0.0, 1.0, 0.0),
            )
        )
    return with_island.cut(*pin_cuts)


def get_shape() -> cq.Shape:
    """Build the Player 1 (`X = -32.34 mm`) shallow N64 controller port insert."""
    return insert_at(D.PORT_INSERT_XS[0], player_num=1)
