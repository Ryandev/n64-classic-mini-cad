"""n64_console_raw -- untouched 1:1 downloaded Nintendo 64 assembly reference STEP.

Extracted from `nintendo-64-1.snapshot.1.zip` (`N64.SLDASM`) and oriented into the
right-handed tabletop Z-up frame (`+X` right, `+Y` rear, `-Y` front, `+Z` up).
Includes the raw console shell, Power switch, Reset button, cartridge flaps,
SolidWorks construction planes, external `NUS-002` power brick/cord, and RCA AV cable.
"""

import os

import cadquery as cq

_STEP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "n64_console_raw.step")
_shape_cache: cq.Shape | None = None


def get_shape() -> cq.Shape:
    global _shape_cache
    if _shape_cache is None:
        _shape_cache = cq.importers.importStep(_STEP_PATH).val()
    return _shape_cache
