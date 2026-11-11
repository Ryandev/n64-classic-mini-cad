"""Variant of `part/upper_shell.py` adding dome & rear active-cooler ventilation (`REQ-04`).

Imports the faithful 50%-scale N64 upper shell (`from part import upper_shell as FAITHFUL`)
and opens:
  - 13 vertical rear `+Y` exhaust louver slits (`1.425 x 4.60 mm` on `2.675 mm` centres across
    `X = -16.76 .. +16.76 mm`, `Z = 19.50 .. 24.10 mm`) aligned to the top louver array
  - 3 top-plenum louver vents through the central parabolic fan-arc slots (`X = -5.35, 0.0, +5.35`)
    directly above the upward-facing Radxa X4 Intel N100 finned heatsink

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
    "crescent_plenum_vent_l": {
        "kind": "removed",
        "why": "Open left-centre parabolic louver through dome roof above N100 heatsink",
        "bbox": (-6.5, -8.2, 24.0, -4.2, 3.8, 34.0),
        "volume_mm3": 27.89,
        "tolerance_mm3": 2.0,
    },
    "crescent_plenum_vent_c": {
        "kind": "removed",
        "why": "Open centre parabolic louver through dome roof above N100 heatsink",
        "bbox": (-1.2, -8.2, 24.0, 1.2, 3.8, 34.0),
        "volume_mm3": 28.24,
        "tolerance_mm3": 2.0,
    },
    "crescent_plenum_vent_r": {
        "kind": "removed",
        "why": "Open right-centre parabolic louver through dome roof above N100 heatsink",
        "bbox": (4.2, -8.2, 24.0, 6.5, 3.8, 34.0),
        "volume_mm3": 27.89,
        "tolerance_mm3": 2.0,
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
    # Open 3 central parabolic louver slots (indices 10, 12, 14) into the top heatsink plenum
    for idx in (10, 12, 14):
        x0, y0, x1, y1 = C.TOP_LOUVER_BOXES_50[idx]
        cuts.append(
            cq.Solid.makeBox(
                x1 - x0,
                y1 - y0,
                10.0,
                cq.Vector(x0, y0, 24.2),
            )
        )
    return base.cut(*cuts)
