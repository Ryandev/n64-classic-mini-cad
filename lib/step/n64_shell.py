"""n64_shell -- 1:1 downloaded Nintendo 64 outer shell & cartridge flaps reference STEP.

Oriented in the right-handed tabletop Z-up frame (`X in [-130.0, +130.0]`,
`Y in [-99.88, +99.88]`, `Z in [0.0, +67.0]`). Imports `n64_shell.step` with zero
shape-construction operations (enforced by `lib/testing/lint_structure.py`).
"""

import os

import cadquery as cq

_STEP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "n64_shell.step")
_shape_cache: cq.Shape | None = None


def get_shape() -> cq.Shape:
    global _shape_cache
    if _shape_cache is None:
        _shape_cache = cq.importers.importStep(_STEP_PATH).val()
    return _shape_cache
