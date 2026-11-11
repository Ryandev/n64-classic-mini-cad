"""usb_a_te_292303_7 -- unmodified TE Connectivity 292303-7 USB 2.0 Type-A horizontal STEP.

Orderable off-the-shelf right-angle USB 2.0 Type-A female receptacle (`15.13 x 15.36 x 7.76 mm`
body above PCB + `3.61 mm` through-hole tails/board-locks; Farnell `1240559` / Mouser
`571-292303-7`, source: KiCad `Connector_USB.3dshapes/USB_A_TE_292303-7_Horizontal.step`).
"""

import os

import cadquery as cq

_STEP_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "usb_a_te_292303_7.step",
)
_shape_cache: cq.Shape | None = None


def get_shape() -> cq.Shape:
    global _shape_cache
    if _shape_cache is None:
        _shape_cache = cq.importers.importStep(_STEP_PATH).val()
    return _shape_cache
