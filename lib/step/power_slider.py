"""power_slider -- 1:1 downloaded N64 Power switch cap reference STEP.

Sister file to `lib/part/power_slider.py`. Imports `power_slider.step` at local
tabletop Z-up origin with zero shape-construction operations.
"""

import os

import cadquery as cq

_STEP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "power_slider.step")
_shape_cache: cq.Shape | None = None


def get_shape() -> cq.Shape:
    global _shape_cache
    if _shape_cache is None:
        _shape_cache = cq.importers.importStep(_STEP_PATH).val()
    return _shape_cache
