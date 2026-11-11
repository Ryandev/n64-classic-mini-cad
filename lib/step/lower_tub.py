"""lower_tub -- 50%-scale N64 lower tub reference STEP.

Sister file to `lib/part/lower_tub.py`. Imports `lower_tub.step` with zero
shape-construction operations (enforced by `lib/testing/lint_structure.py`).
"""

import os

import cadquery as cq

_STEP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lower_tub.step")
_shape_cache: cq.Shape | None = None


def get_shape() -> cq.Shape:
    global _shape_cache
    if _shape_cache is None:
        _shape_cache = cq.importers.importStep(_STEP_PATH).val()
    return _shape_cache
