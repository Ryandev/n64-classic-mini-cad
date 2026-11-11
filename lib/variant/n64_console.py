"""Cleaned 1:1 Nintendo 64 Reference Console (`lib/variant/n64_console.py`).

Derives from `lib/step/n64_console_raw.py` (`DERIVES_FROM = "n64_console_raw"`) and strips:
  - External `NUS-002` AC power brick & trailing DC cord (`n64_power_brick`)
  - External AV Multi-Out plug & folded RCA stereo/composite cable (`n64_av_cable`)
  - Stray SolidWorks construction planes & micro-artefact sheets (`sw_construction_front`,
    `sw_construction_rear`, `sw_rear_micro_artifact`)

Verified mechanically against `DEVIATIONS` by `lib/testing/variant_manifest.py`.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform  # noqa: E402
from OCP.gp import gp_Pnt, gp_Trsf  # noqa: E402
from step import n64_console_raw as REFERENCE  # noqa: E402

PROCESS = "reference"
MANUFACTURE = "reference"
DERIVES_FROM = "n64_console_raw"

DEVIATIONS = {
    "n64_power_brick": {
        "kind": "removed",
        "why": "Remove external NUS-002 power supply brick & trailing cord (replaced by USB-C PD)",
        "bbox": (-195.0, 45.0, 0.0, 22.0, 305.0, 52.0),
        "area_mm2": 40986.08,
        "tolerance_mm2": 10.0,
    },
    "n64_av_cable": {
        "kind": "removed",
        "why": "Remove external AV Multi-Out plug & folded RCA cable (replaced by Micro-HDMI)",
        "bbox": (25.0, 62.0, 10.0, 162.0, 235.0, 2700.0),
        "area_mm2": 3167046.79,
        "tolerance_mm2": 25.0,
    },
    "sw_construction_rear": {
        "kind": "removed",
        "why": "Remove stray SolidWorks rear construction reference sheet from Console N64",
        "bbox": (-122.0, 95.0, 49.0, 122.0, 106.0, 61.0),
        "area_mm2": 1693.44,
        "tolerance_mm2": 5.0,
    },
    "sw_construction_front": {
        "kind": "removed",
        "why": "Remove stray SolidWorks front construction reference sheet from Console N64",
        "bbox": (-122.0, -100.0, 49.0, 122.0, -86.0, 68.0),
        "area_mm2": 2426.56,
        "tolerance_mm2": 5.0,
    },
}


def _inside_any_removed(sub: cq.Shape) -> bool:
    b = sub.BoundingBox()
    for d in DEVIATIONS.values():
        x0, y0, z0, x1, y1, z1 = d["bbox"]
        if (
            b.xmin >= x0 - 1e-4
            and b.xmax <= x1 + 1e-4
            and b.ymin >= y0 - 1e-4
            and b.ymax <= y1 + 1e-4
            and b.zmin >= z0 - 1e-4
            and b.zmax <= z1 + 1e-4
        ):
            return True
    return False


def get_shape() -> cq.Shape:
    """Return the cleaned 1:1 N64 console reference (console shell + Power + Reset + 2 flaps)."""
    raw = REFERENCE.get_shape()
    kept = [sub for sub in raw if not _inside_any_removed(sub)]
    return cq.Compound.makeCompound(kept)


def placed_50() -> cq.Shape:
    """Return the cleaned N64 reference uniformly scaled by 0.50 for visual comparison."""
    trsf = gp_Trsf()
    trsf.SetScale(gp_Pnt(0.0, 0.0, 0.0), 0.50)
    return cq.Shape.cast(BRepBuilderAPI_Transform(get_shape().wrapped, trsf, True).Shape())
