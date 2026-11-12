"""Variant of `part/upper_shell.py` adding dome & rear active-cooler ventilation (`REQ-04`).

Imports the faithful 50%-scale N64 upper shell (`from part import upper_shell as FAITHFUL`)
and opens:
  - 13 vertical rear `+Y` exhaust louver slits (`1.425 x 4.60 mm` on `2.675 mm` centres across
    `X = -16.76 .. +16.76 mm`, `Z = 19.50 .. 24.10 mm`) aligned to the top louver array
  - all 25 top louvers through the roof: the fan's intake, sealed to it by `part/cooling_hood.py`
  - a 0.4 mm relief inside the rear wall over a tall part on the Radxa X4 (C10)

Verified against `DEVIATIONS` by `lib/testing/variant_manifest.py`.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from part import upper_shell as FAITHFUL  # noqa: E402
from part.shared import n64_contours as C  # noqa: E402

PROCESS = "fdm"
MANUFACTURE = "fdm"
PRINT_NORMAL = (0, 0, 1)
VISIBLE_FACES = ("-X", "+X", "-Y", "+Y", "+Z")

DEVIATIONS = {
    "rear_dome_exhaust_l": {
        "kind": "removed",
        "why": "Left 4 vertical rear +Y exhaust louver slits (1.425x4.60mm, idx 6..9, REQ-04)",
        "bbox": (-17.5, 46.0, 19.0, -6.8, 50.5, 24.6),
        "volume_mm3": 52.45,
        "tolerance_mm3": 2.0,
    },
    "rear_dome_exhaust_c": {
        "kind": "removed",
        "why": "Centre 5 vertical rear +Y exhaust louver slits (1.425x4.60mm, idx 10..14, REQ-04)",
        "bbox": (-6.7, 46.0, 19.0, 6.7, 50.5, 24.6),
        "volume_mm3": 65.55,
        "tolerance_mm3": 2.0,
    },
    "rear_dome_exhaust_r": {
        "kind": "removed",
        "why": "Right 4 vertical rear +Y exhaust louver slits (1.425x4.60mm, idx 15..18, REQ-04)",
        "bbox": (6.8, 46.0, 19.0, 17.5, 50.5, 24.6),
        "volume_mm3": 52.45,
        "tolerance_mm3": 2.0,
    },
    "radxa_part_relief": {
        "kind": "removed",
        "why": "0.4 mm pocket inside the rear wall over a 4 mm part on the Radxa X4 (solid 354 "
        "of Radxa's own STEP), which the hand-edited board model lacked (C10)",
        "bbox": (31.4, 42.7, 12.8, 37.4, 43.5, 13.8),
        "volume_mm3": 1.93,
        "tolerance_mm3": 0.2,
    },
    "top_louvers_intake": {
        "kind": "removed",
        "why": "Open all 25 top louvers through the roof: the cooling intake, sealed to the fan by "
        "part/cooling_hood.py (REQ-04)",
        "bbox": (-33.5, -8.5, 24.0, 33.5, 4.2, 34.0),
        "volume_mm3": 495.7,
        "tolerance_mm3": 5.0,
    },
}


def get_shape() -> cq.Shape:
    """Build the N64 Classic Mini Upper Shell variant from `part/upper_shell.py`."""
    base = FAITHFUL.get_shape()
    slit_h = 4.60
    slit_z0 = 19.50
    cuts = [
        cq.Solid.makeBox(
            x1 - x0,
            5.5,
            slit_h,
            cq.Vector(x0, 46.0, slit_z0),
        )
        for (x0, _, x1, _) in C.TOP_LOUVER_BOXES_50[6:19]
    ]
    # Open all 25 top louvers through the roof: the cooling intake (REQ-04)
    for x0, y0, x1, y1 in C.TOP_LOUVER_BOXES_50:
        cuts.append(
            cq.Solid.makeBox(
                x1 - x0,
                y1 - y0,
                10.0,
                cq.Vector(x0, y0, 24.2),
            )
        )
    # Radxa part relief (C10): x 31.47..37.27, y 42.8..43.4, z 12.84..13.67 (the part, +0.2)
    cuts.append(cq.Solid.makeBox(5.8, 0.6, 0.83, cq.Vector(31.47, 42.8, 12.84)))
    return base.cut(*cuts)
