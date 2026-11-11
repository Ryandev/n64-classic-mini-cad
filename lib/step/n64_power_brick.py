"""n64_power_brick -- 1:1 downloaded N64 external power brick & cord reference STEP.

Removed from the clean N64 reference in `lib/variant/n64_console.py`.
"""

import os

import cadquery as cq

_STEP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "n64_power_brick.step")
_shape_cache: cq.Shape | None = None


def get_shape() -> cq.Shape:
    global _shape_cache
    if _shape_cache is None:
        _shape_cache = cq.importers.importStep(_STEP_PATH).val()
    return _shape_cache
