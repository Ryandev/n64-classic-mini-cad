"""radxa_heatsink -- unmodified official Radxa X4 aluminium heatsink reference STEP.

Aligned to the local Radxa X4 SoC mounting pattern (`58.0 x 49.0 mm` holes) before
case-wing trimming in `lib/variant/radxa_heatsink.py`.
"""

import os

import cadquery as cq

_STEP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "radxa_heatsink.step")
_shape_cache: cq.Shape | None = None


def get_shape() -> cq.Shape:
    global _shape_cache
    if _shape_cache is None:
        _shape_cache = cq.importers.importStep(_STEP_PATH).val()
    return _shape_cache
