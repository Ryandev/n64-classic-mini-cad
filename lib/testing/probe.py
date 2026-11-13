"""Measure distances on the real solids by stepping along a line (C8: checks that measure).

A check that reads a wall's position from `datum.py` grades the design against itself; these
helpers find where the material actually is.
"""

import cadquery as cq
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Pnt
from OCP.TopAbs import TopAbs_IN


def first_hit(
    shape: cq.Shape,
    start: tuple[float, float, float],
    direction: tuple[float, float, float],
    max_len: float = 40.0,
    step: float = 0.02,
) -> float | None:
    """Distance from `start` along unit-axis `direction` to the first point inside `shape`.

    Returns `None` if nothing is hit within `max_len`, so a missing wall fails loud upstream
    instead of reading as a gap.
    """
    clf = BRepClass3d_SolidClassifier(shape.wrapped)
    x, y, z = start
    dx, dy, dz = direction
    n = int(max_len / step)
    for i in range(n + 1):
        t = i * step
        clf.Perform(gp_Pnt(x + dx * t, y + dy * t, z + dz * t), 1e-6)
        if clf.State() == TopAbs_IN:
            return t
    return None


def min_gap(
    shape: cq.Shape,
    starts: list[tuple[float, float, float]],
    direction: tuple[float, float, float],
    max_len: float = 40.0,
) -> float | None:
    """Smallest `first_hit` over several parallel start points (holes in a wall read larger)."""
    hits = [first_hit(shape, s, direction, max_len) for s in starts]
    found = [h for h in hits if h is not None]
    return min(found) if found else None
