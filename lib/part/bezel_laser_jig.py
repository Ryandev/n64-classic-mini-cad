"""Diode-Laser 3.0mm Birch Plywood Cutting & Cricut Alignment Jig (`part/bezel_laser_jig.py`).

Because a `450 nm` blue diode laser passes through clear acrylic without cutting it, this
`3.0 mm` Birch Plywood jig (`50.0 x 36.0 x 3.0 mm`, exported to `export/2d/bezel_laser_jig.svg`
and `export/3d/bezel_laser_jig.step`) is cut directly on a diode laser and serves two workshop
functions:
  1. **Clear Acrylic Shaping / Scoring / Flush-Trim Template:** Clamp a rough blank of `2.0 mm`
     clear acrylic under the laser-cut `24.14 x 15.50 mm` N64 jewel window (using the 4x `Ø3.2`
     M3 corner clamp holes) to score around the inside edge with a blade, flush-trim with a
     rotary bearing bit / sanding file, or diode-laser score against a dark sacrificial backing.
  2. **Dead-Centre Cricut Sticker Registration Nest:** Drop the finished `2.0 mm` clear acrylic
     jewel face-down into the `24.14 x 15.50 mm` plywood window, then lower the Cricut-cut
     N64 vinyl sticker into the same window so the sticker adheres to the back of the clear
     acrylic with `+-0.1 mm` edge registration.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402
from shared import n64_contours as C  # noqa: E402

PROCESS = "laser"
MANUFACTURE = "laser"
MATERIAL = "3.0mm Laser-Grade Birch Plywood"
SHEET_T = 3.0
LAYERS = (1.5,)
PRINT_NORMAL = (0, 0, 1)
VISIBLE_FACES = ("+Z",)

JIG_W = 50.0
JIG_D = 36.0
JIG_T = 3.0
JIG_CLAMP_DX = 40.0
JIG_CLAMP_DY = 26.0
JIG_HOLE_D = 3.2


def get_shape() -> cq.Shape:
    """Construct the 3.0 mm Birch Plywood diode-laser jig in flat XY orientation (`Z = 0..3`)."""
    # Outer 50 x 36 x 3 mm plywood plate with R = 3.0 mm rounded corners
    wp = (
        cq.Workplane("XY", origin=(0.0, 0.0, 0.0))
        .moveTo(-JIG_W / 2.0 + 3.0, -JIG_D / 2.0)
        .lineTo(JIG_W / 2.0 - 3.0, -JIG_D / 2.0)
        .threePointArc((JIG_W / 2.0 - 0.88, -JIG_D / 2.0 + 0.88), (JIG_W / 2.0, -JIG_D / 2.0 + 3.0))
        .lineTo(JIG_W / 2.0, JIG_D / 2.0 - 3.0)
        .threePointArc((JIG_W / 2.0 - 0.88, JIG_D / 2.0 - 0.88), (JIG_W / 2.0 - 3.0, JIG_D / 2.0))
        .lineTo(-JIG_W / 2.0 + 3.0, JIG_D / 2.0)
        .threePointArc((-JIG_W / 2.0 + 0.88, JIG_D / 2.0 - 0.88), (-JIG_W / 2.0, JIG_D / 2.0 - 3.0))
        .lineTo(-JIG_W / 2.0, -JIG_D / 2.0 + 3.0)
        .threePointArc(
            (-JIG_W / 2.0 + 0.88, -JIG_D / 2.0 + 0.88), (-JIG_W / 2.0 + 3.0, -JIG_D / 2.0)
        )
        .close()
        .extrude(JIG_T)
    )
    plate = wp.val()

    # Exact 24.14 x 15.50 mm N64 shield cutout window rotated from XZ into XY (Z = 0..3 mm)
    jewel_xz = C.n64_shield_prism(
        y0=-1.0,
        depth_y=JIG_T + 2.0,
        width_x=D.BEZEL_W,
        height_z=D.BEZEL_H,
        z_centre=0.0,
    )
    jewel_xy = jewel_xz.rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), -90.0).translate(
        (0.0, 0.0, JIG_T + 1.0)
    )

    cuts = [jewel_xy]
    # 4x Ø3.2 mm M3 clamping / two-layer registration dowel holes
    for sx in (-0.5 * JIG_CLAMP_DX, 0.5 * JIG_CLAMP_DX):
        for sy in (-0.5 * JIG_CLAMP_DY, 0.5 * JIG_CLAMP_DY):
            cuts.append(
                cq.Solid.makeCylinder(
                    JIG_HOLE_D / 2.0,
                    JIG_T + 1.0,
                    cq.Vector(sx, sy, -0.5),
                )
            )
    return plate.cut(*cuts)
