"""Minimum wall: the closest approach between any two cut boundaries in a sheet part."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cadquery as cq  # noqa: E402
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common  # noqa: E402
from OCP.BRepExtrema import BRepExtrema_DistShapeShape  # noqa: E402


def layer_wires(shape, z0, t):
    """Every boundary wire of the part at this layer, outer and inner alike."""
    slab = (
        cq.Workplane("XY")
        .box(4000, 4000, t * 0.6, centered=(True, True, False))
        .translate((0, 0, z0 + t * 0.2))
        .val()
    )
    com = BRepAlgoAPI_Common(shape.wrapped, slab.wrapped)
    com.Build()
    if not com.IsDone():
        return []
    sec = cq.Shape.cast(com.Shape())
    return [
        [w for f in [max(sol.Faces(), key=lambda f: f.Center().z)] for w in f.Wires()]
        for sol in sec.Solids()
    ]


def all_gaps(shape, t):
    """Every boundary-pair distance, smallest first: (dist, (x, y), layer)."""
    b = shape.BoundingBox()
    n = max(1, int(round(b.zlen / t)))
    found = []
    for i in range(n):
        for ws in layer_wires(shape, b.zmin + i * t, t):
            for a in range(len(ws)):
                for c in range(a + 1, len(ws)):
                    d = BRepExtrema_DistShapeShape(ws[a].wrapped, ws[c].wrapped)
                    d.Perform()
                    if d.IsDone():
                        pt = d.PointOnShape1(1)
                        found.append((d.Value(), (round(pt.X(), 2), round(pt.Y(), 2)), i + 1))
    return sorted(found)


def min_wall(shape, t, z0=None):
    """Smallest distance between two distinct boundaries. (dist, (x, y), layer) or None."""
    b = shape.BoundingBox()
    n = max(1, int(round(b.zlen / t)))
    worst = None
    for i in range(n):
        zz = b.zmin + i * t if z0 is None else z0
        for ws in layer_wires(shape, zz, t):
            for a in range(len(ws)):
                for c in range(a + 1, len(ws)):
                    d = BRepExtrema_DistShapeShape(ws[a].wrapped, ws[c].wrapped)
                    d.Perform()
                    if not d.IsDone():
                        continue
                    v = d.Value()
                    if worst is None or v < worst[0]:
                        p = d.PointOnShape1(1)
                        worst = (v, (round(p.X(), 2), round(p.Y(), 2)), i + 1)
        if z0 is not None:
            break
    return worst
