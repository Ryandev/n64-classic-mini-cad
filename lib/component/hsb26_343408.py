"""Same Sky HSB26-343408 BGA heat sink (bought): reference solid and datasheet figures.

Datasheet rev 1.03 (2026-01-26): 33.5 x 33.5 mm, 2.0 mm base, 14 x 14 square pin fins
1.0 x 1.0 x 8.0 mm, AL6063-T5, 15.6 g. Seated on the Intel N100 with paste (no pad) and clamped by
the printed `cooling_duct` cover resting on the pin tips.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402

PART = "Same Sky HSB26-343408"
MASS_KG = 15.6e-3
# Measured heat-sink rise above ambient at 10 W (datasheet table), as K/W, by free-stream
# approach velocity in m/s (0, 200 and 400 LFM).
R_BY_VELOCITY = {0.0: 138.7 / 10.0, 1.016: 57.4 / 10.0, 2.032: 36.8 / 10.0}

_cache: cq.Shape | None = None


def pitch() -> float:
    """Pin centre spacing: edge pins flush with the 33.5 mm base."""
    return (D.HS_W - D.HS_PIN) / (D.HS_ROWS - 1)


def placed() -> cq.Shape:
    """Heat sink seated on the N100 in console coordinates (base down on the die)."""
    global _cache
    if _cache is None:
        base = cq.Workplane("XY").box(D.HS_W, D.HS_W, D.HS_BASE_T, centered=False)
        offset = D.HS_PIN / 2.0
        pts = [
            (offset + i * pitch(), offset + j * pitch())
            for i in range(D.HS_ROWS)
            for j in range(D.HS_ROWS)
        ]
        pins = (
            cq.Workplane("XY", origin=(0, 0, D.HS_BASE_T))
            .pushPoints(pts)
            .rect(D.HS_PIN, D.HS_PIN)
            .extrude(D.HS_FIN_H)
        )
        shape = base.union(pins).val()
        _cache = shape.moved(cq.Location(cq.Vector(D.HS_X0, D.HS_Y0, D.HS_Z0)))
    return _cache
