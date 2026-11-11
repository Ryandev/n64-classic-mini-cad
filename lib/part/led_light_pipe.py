"""Clear PETG Front Power LED Light-Pipe (`lib/part/led_light_pipe.py`, `J-07`).

Printed in **Clear / Translucent Red PETG** (`PRINT_NORMAL = (0, -1, 0)`, rear flat face on the
build plate for `> 65%` bed contact and `0.0 mm^2` overhang).
Connects a wired **3 mm red diffused through-hole LED** (held inside `lower_tub`'s integrated
LED holder cradle and wired to the Radxa X4 GPIO header) to the authentic N64 front Power LED
aperture (`Face[1823]` of `Console_N64.step` at `0.5x` scale):
  - Front `-Y` lens (`Y = -46.56 .. -44.26 mm`): Exact `6.36 x 1.76 mm` horizontal lenticular /
    biconvex almond N64 Power LED lens (`C.n64_led_lens_prism`) sitting flush on the untouched
    central front apron (`X = 0.0, Z = 8.24 mm`) between the twin controller bays
  - Middle retention flange (`Y = -44.26 .. -42.76 mm`): `7.80 x 3.80 x 1.50 mm` stadium collar
    that seats against the internal step behind the front apron (`0.10 mm/side` lens clearance)
  - Rear optical light-guide barrel (`Y = -42.76 .. -39.56 mm`): `5.20 x 3.80 x 3.20 mm` stadium
    light pipe that slides into `variant/lower_tub`'s internal LED holder cradle and couples via
    a conical `45 deg` rear collimator dimple to the `3 mm` red LED dome (`Y = -39.56 mm`)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace  # noqa: E402
from shared import n64_contours as C  # noqa: E402

PROCESS = "fdm"
MANUFACTURE = "fdm"
MATERIAL = "Clear PETG"
PRINT_NORMAL = (0, -1, 0)
VISIBLE_FACES = ("-Y",)


def _xz_stadium_prism(
    cx: float,
    zc: float,
    width_x: float,
    height_z: float,
    y0: float,
    depth_y: float,
) -> cq.Shape:
    """Horizontal stadium solid in `XZ` extruded along `+Y` from `y0` to `y0 + depth_y`."""
    r = 0.5 * height_z
    dx = 0.5 * (width_x - height_z)
    wp = (
        cq.Workplane("XZ", origin=(0.0, y0, 0.0))
        .moveTo(cx - dx, zc + r)
        .lineTo(cx + dx, zc + r)
        .threePointArc((cx + dx + r, zc), (cx + dx, zc - r))
        .lineTo(cx - dx, zc - r)
        .threePointArc((cx - dx - r, zc), (cx - dx, zc + r))
        .close()
    )
    face = cq.Face.cast(BRepBuilderAPI_MakeFace(wp.wire().val().wrapped, True).Face())
    return cq.Solid.extrudeLinear(face, cq.Vector(0.0, depth_y, 0.0))


def get_shape() -> cq.Shape:
    """Construct the Clear PETG N64 front Power LED light-pipe solid."""
    y_front = D.LED_PIPE_Y0  # -46.56 mm flush with central front apron
    y_flange0 = y_front + 2.30  # -44.26 mm (0.10 mm behind -44.36 mm front wall inner step)
    y_guide0 = y_flange0 + D.LED_FLANGE_T  # -42.76 mm
    y_rear = y_guide0 + 3.20  # -39.56 mm flat print-bed & 3mm-LED coupling plane

    # 1. Exact 6.36 x 1.76 mm horizontal lenticular N64 front lens (Y = -46.56 .. -44.21 mm)
    lens = C.n64_led_lens_prism(
        y0=y_front,
        depth_y=2.35,
        clearance=0.0,
        z_centre=D.LED_PIPE_Z,
    )

    # 2. Internal stadium retention collar (7.80 x 3.80 x 1.50 mm, Y = -44.26 .. -42.76 mm)
    collar = _xz_stadium_prism(
        cx=D.LED_PIPE_X,
        zc=D.LED_PIPE_Z,
        width_x=D.LED_FLANGE_W,
        height_z=D.LED_FLANGE_D,
        y0=y_flange0,
        depth_y=D.LED_FLANGE_T,
    )

    # 3. Rear optical light-guide barrel (5.20 x 3.80 x 3.20 mm, Y = -42.76 .. -39.56 mm)
    #    Extended to full 7.80 x 3.80 mm base at Y = -39.56 mm so bed contact is 100% flat
    #    and print orientation PRINT_NORMAL = (0, -1, 0) has 0.0 mm^2 overhang!
    guide_body = _xz_stadium_prism(
        cx=D.LED_PIPE_X,
        zc=D.LED_PIPE_Z,
        width_x=D.LED_FLANGE_W,
        height_z=D.LED_FLANGE_D,
        y0=y_flange0,
        depth_y=y_rear - y_flange0,
    )

    # 4. Conical 45-deg rear LED collimator dimple on the +Y face (Y = -39.56 mm) to gather light
    #    from the 3 mm diffused red LED dome while keeping 0.0 mm^2 overhang on the bed
    collimator = cq.Solid.makeCone(
        1.10,
        0.10,
        1.05,
        cq.Vector(D.LED_PIPE_X, y_rear + 0.05, D.LED_PIPE_Z),
        cq.Vector(0.0, -1.0, 0.0),
    )

    return lens.fuse(collar, guide_body).cut(collimator)
