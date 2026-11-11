"""De-ported Radxa X4 v1.11 SBC (`lib/variant/radxa_x4.py`, `REQ-03`, `REQ-05`).

Derives from `lib/step/radxa_x4.py` (the full 29-solid Radxa X4 STEP) and strips all 6
tall through-hole connector headers so the inverted board fits inside the `36.5 mm`-tall
50%-scale N64 Classic Mini enclosure:
  - `usb3_dual_stack` (dual stacked USB 3.0 Type-A tower)
  - `usb2_dual_stack` (dual stacked USB 2.0 Type-A tower)
  - `rj45_ethernet_tower` (2.5GbE RJ45 + transformer MagJack tower, relocated to rear bay)
  - `poe_4pin_header` (4-pin PoE header)
  - `fan_2pin_header` (tall vertical 2-pin fan header)
  - `gpio_40pin_header` (40-pin 2.54 mm GPIO header)

Exposes:
  - `get_shape()` in local PCB coordinates (verified against `step/radxa_x4.py` by
    `lib/testing/variant_manifest.py`)
  - `placed()` rotated `180 deg` about `+X` (Intel N100 SoC facing `+Z` up into the dome,
    M.2 2230 NVMe facing `-Z` down) at `(RADXA_X_CENTRE, RADXA_Y_CENTRE, RADXA_PCB_Z0)`
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402
from step import radxa_x4 as REFERENCE  # noqa: E402

PROCESS = "component"
MANUFACTURE = "component"

DEVIATIONS = {
    "usb3_dual_stack": {
        "kind": "removed",
        "why": "Desolder tall dual-stack USB 3.0 Type-A tower (routed to front controller bays)",
        "bbox": (27.50, -27.50, -3.50, 45.50, -11.30, 16.50),
        "volume_mm3": 2445.58,
        "tolerance_mm3": 1.5,
    },
    "usb2_dual_stack": {
        "kind": "removed",
        "why": "Desolder tall dual-stack USB 2.0 Type-A tower (routed to front controller bays)",
        "bbox": (27.50, -9.00, -3.50, 45.50, 7.20, 16.50),
        "volume_mm3": 2445.58,
        "tolerance_mm3": 1.5,
    },
    "rj45_ethernet_tower": {
        "kind": "removed",
        "why": "Desolder tall onboard RJ45 MagJack tower (relocated to +X rear-right 24mm bay)",
        "bbox": (24.20, 9.50, -4.00, 46.00, 26.20, 13.90),
        "volume_mm3": 3612.18,
        "tolerance_mm3": 2.0,
    },
    "poe_4pin_header": {
        "kind": "removed",
        "why": "Desolder 4-pin PoE through-hole header (unused; USB-C PD powers console)",
        "bbox": (16.10, 15.50, -2.20, 21.80, 21.20, 7.80),
        "volume_mm3": 65.37,
        "tolerance_mm3": 0.5,
    },
    "fan_2pin_header": {
        "kind": "removed",
        "why": "Desolder tall vertical 2-pin fan header (wire soldered directly to pads)",
        "bbox": (-26.30, -27.30, -2.20, -20.60, -24.20, 7.80),
        "volume_mm3": 32.69,
        "tolerance_mm3": 0.5,
    },
    "gpio_40pin_header": {
        "kind": "removed",
        "why": "Omit/desolder 9.65mm 40-pin GPIO header (Power/Reset wired to RP2040 pads)",
        "bbox": (-35.90, 20.40, -0.30, 15.50, 28.60, 9.90),
        "volume_mm3": 676.92,
        "tolerance_mm3": 1.5,
    },
}

_local_cache: cq.Shape | None = None
_placed_cache: cq.Shape | None = None


def _is_stripped_header(sol: cq.Solid) -> bool:
    b = sol.BoundingBox()
    if b.xlen > 70.0:  # Never strip the 85 x 56 mm main PCB
        return False
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
    """Return the de-ported 23-solid Radxa X4 in local PCB coordinates."""
    global _local_cache
    if _local_cache is None:
        raw = REFERENCE.get_shape()
        kept = [s for s in raw.Solids() if not _is_stripped_header(s)]
        _local_cache = cq.Compound.makeCompound(kept)
    return _local_cache


def placed() -> cq.Shape:
    """Return the de-ported 23-solid Radxa X4 inverted and placed in console coordinates."""
    global _placed_cache
    if _placed_cache is None:
        _placed_cache = (
            get_shape()
            .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 180.0)
            .translate((D.RADXA_X_CENTRE, D.RADXA_Y_CENTRE, D.RADXA_PCB_Z0))
        )
    return _placed_cache
