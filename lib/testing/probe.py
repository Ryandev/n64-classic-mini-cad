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


def slice_gap(a: cq.Shape, b: cq.Shape, axis: str, at: float, half: float = 0.05) -> float:
    """Smallest gap between `a` and `b` within a thin slab across `axis` at `at`.

    For an in-plane fit (a door's edge in its bay, an insert in its pocket) where the parts also
    touch somewhere else (a seat, a glue face): the slab keeps only the edge gap. Raises if the
    slab misses either part, so a slab in the wrong place fails loud instead of reading as a gap.
    """
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape

    big = 400.0
    lo = {"x": (at - half, -big, -big), "y": (-big, at - half, -big), "z": (-big, -big, at - half)}
    size = {
        "x": (2 * half, 2 * big, 2 * big),
        "y": (2 * big, 2 * half, 2 * big),
        "z": (2 * big, 2 * big, 2 * half),
    }
    slab = cq.Solid.makeBox(*size[axis], cq.Vector(*lo[axis]))
    a_s, b_s = a.intersect(slab), b.intersect(slab)
    if not a_s.Solids() or not b_s.Solids():
        raise ValueError(
            f"slab {axis}={at:.2f} misses a part ({len(a_s.Solids())}, {len(b_s.Solids())})"
        )
    ext = BRepExtrema_DistShapeShape(a_s.wrapped, b_s.wrapped)
    ext.Perform()
    return ext.Value()
