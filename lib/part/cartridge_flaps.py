"""Separately-printed Light Cool Grey N64 Cartridge Slot Dust-Flap Insert (`J-09`).

Authentic 50%-scale dual cartridge dust-flap insert (`Shell[1]` + `Shell[2]` of
`Console_N64.step` at `0.5x`), printed separately in Light Cool Grey PLA/PETG (matching
`power_slider`, `reset_button`, and `4x n64_port_insert`) and seated into the recessed
cartridge throat pocket of the Charcoal Grey `upper_shell` (`J-09`):
  - Exact `57.50 x 10.00 mm` planform (`X = -28.75 .. +28.75 mm`, `Y = 11.439 .. 21.439 mm`)
    with `R = 4.25 mm` rounded front corners (`Y = 11.439 mm`) and `R = 0.50 mm` rear
    corners (`Y = 21.439 mm`)
  - Flat `Z = 25.40 mm` underside (`98.6%` bed contact with `PRINT_NORMAL = (0, 0, 1)`)
    and `Z = 26.75 mm` top deck (`1.35 mm` total thickness, `0.05 mm` glue film gap above
    the `Z = 25.35 mm` pocket floor in `upper_shell`, `0.15 mm/side` XY locating clearance)
  - 3D-engraved `0.35 mm` central flap parting seam along `Y = 16.439 mm` and twin
    `R = 3.00 mm` semicircular end-tab grooves at `(+-25.75, 16.439)`
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet  # noqa: E402

PROCESS = "fdm"
MANUFACTURE = "fdm"
PRINT_NORMAL = (0, 0, 1)
VISIBLE_FACES = ("+Z",)


def get_shape() -> cq.Shape:
    """Build the placed Light Cool Grey N64 Cartridge Slot Flap Insert in console coordinates."""
    wp = (
        cq.Workplane("XY", origin=(0.0, D.CARTRIDGE_FLAP_Y, D.CARTRIDGE_FLAP_Z0))
        .rect(D.CARTRIDGE_FLAP_W, D.CARTRIDGE_FLAP_D)
        .extrude(D.CARTRIDGE_FLAP_T)
    )
    box = wp.val()
    mk = BRepFilletAPI_MakeFillet(box.wrapped)
    for e in box.Edges():
        bb = e.BoundingBox()
        if bb.zmax - bb.zmin > 1.0:
            if bb.ymin < 12.0:
                mk.Add(4.25, e.wrapped)
            else:
                mk.Add(0.50, e.wrapped)
    mk.Build()
    body = cq.Shape.cast(mk.Shape())

    # Authentic central dust-flap parting seam and semicircular end-tab grooves (0.30 mm deep)
    z_seam = D.CARTRIDGE_FLAP_Z - 0.30
    center_seam = cq.Solid.makeBox(
        51.50,
        0.35,
        1.0,
        cq.Vector(-25.75, D.CARTRIDGE_FLAP_Y - 0.175, z_seam),
    )
    tab_l = cq.Solid.makeCylinder(
        2.20,
        1.0,
        cq.Vector(-25.75, D.CARTRIDGE_FLAP_Y, z_seam),
    )
    tab_r = cq.Solid.makeCylinder(
        2.20,
        1.0,
        cq.Vector(25.75, D.CARTRIDGE_FLAP_Y, z_seam),
    )
    return body.cut(center_seam.fuse(tab_l, tab_r))
