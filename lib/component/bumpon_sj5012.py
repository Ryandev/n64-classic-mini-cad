"""3M Bumpon SJ5012 rubber feet (bought): 12.7 mm cylindrical, flat top, 3.5 mm tall.

One on each of the 4 corner M3 counterbores (covering the 6.5 mm bore). They lift the floor
3.5 mm off the desk, which is the gap the floor vents breathe through.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402

PART = "3M Bumpon SJ5012"


def centres() -> list[tuple[float, float]]:
    return [(x, y) for x in D.CORNER_BOSS_XS for y in D.CORNER_BOSS_YS]


def placed() -> cq.Shape:
    """The 4 feet below the floor (Z = -FOOT_H .. 0)."""
    feet = [
        cq.Solid.makeCylinder(D.FOOT_D / 2.0, D.FOOT_H, cq.Vector(x, y, -D.FOOT_H))
        for x, y in centres()
    ]
    return cq.Compound.makeCompound(feet)
