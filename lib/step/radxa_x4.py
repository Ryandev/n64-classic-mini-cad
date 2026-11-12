"""radxa_x4 -- Radxa's own Radxa X4 v1.11 STEP, unedited: all 363 solids (C10).

Built by `step/build_radxa_x4.py` from Radxa's download (SHA-256 checked), moved by translation
only so its four mounting holes sit on the local PCB frame (`58.0 x 49.0 mm` at x -39/+19,
y ±24.5). The six tall headers the console desolders are removed, by identity, in
`lib/variant/radxa_x4.py` and verified by `lib/testing/variant_manifest.py`.
"""

import os

import cadquery as cq

_STEP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "radxa_x4.step")
_shape_cache: cq.Shape | None = None


def get_shape() -> cq.Shape:
    global _shape_cache
    if _shape_cache is None:
        _shape_cache = cq.importers.importStep(_STEP_PATH).val()
    return _shape_cache
