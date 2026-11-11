"""radxa_x4 -- unmodified 29-solid Radxa X4 v1.11 vendor reference STEP.

Aligned to local PCB origin (`58.0 x 49.0 mm` mounting holes at `(-39/+19, +-24.5) mm`)
with all 6 tall through-hole headers (`usb3_dual_stack`, `usb2_dual_stack`,
`rj45_ethernet_tower`, `poe_4pin_header`, `fan_2pin_header`, `gpio_40pin_header`) intact.
Stripped in `lib/variant/radxa_x4.py` and verified by `lib/testing/variant_manifest.py`.
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
