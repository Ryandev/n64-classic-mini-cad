"""Milled Low-Profile Finned Radxa X4 N100 Heatsink (`lib/variant/radxa_heatsink.py`, `REQ-04`).

Derives from `lib/step/radxa_heatsink.py` (`radxa_heatsink_for_x4_3d.stp`, `93.5 x 68.3 x 15.55 mm`
wrap-around aluminium case lid) and mills off the overhanging outer case skirt (`outer_case_wings`)
down to a `40.0 x 38.0 x 10.4 mm` finned aluminium SoC heatsink block seated directly on the
Intel Processor N100 (`Z = 11.7 .. 22.1 mm` in console coordinates), leaving `>= 12.0 mm` air
plenum inside the `36.5 mm` N64 central dome.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402
from step import radxa_heatsink as REFERENCE  # noqa: E402

PROCESS = "component"
MANUFACTURE = "component"

DEVIATIONS = {
    "outer_case_wings": {
        "kind": "removed",
        "why": "Mill overhanging Raspberry-Pi case skirt down to 40x38x10.4mm N100 fin block",
        "bbox": (-67.0, -36.0, -19.0, 27.5, 33.5, -3.0),
        "volume_mm3": 47835.06,
        "tolerance_mm3": 10.0,
    },
}

_local_cache: cq.Shape | None = None
_placed_cache: cq.Shape | None = None


def get_shape() -> cq.Shape:
    """Return the trimmed finned Radxa X4 heatsink in local Radxa PCB coordinates."""
    global _local_cache
    if _local_cache is None:
        raw = REFERENCE.get_shape()
        keep_box = cq.Solid.makeBox(40.0, 38.0, 10.4, cq.Vector(-19.0, -19.5, -13.5))
        _local_cache = raw.intersect(keep_box)
    return _local_cache


def placed() -> cq.Shape:
    """Return the finned heatsink seated on the inverted Intel N100 SoC in console coordinates."""
    global _placed_cache
    if _placed_cache is None:
        _placed_cache = (
            get_shape()
            .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 180.0)
            .translate((D.RADXA_X_CENTRE, D.RADXA_Y_CENTRE, D.RADXA_PCB_Z0))
        )
    return _placed_cache
