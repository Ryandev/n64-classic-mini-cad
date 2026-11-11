"""Parametric cylindrical mounting standoffs with coaxial heat-set insert or clearance bores."""

import cadquery as cq


def standoff(
    bore_dia: float,
    height: float,
    outer_dia: float = 7.0,
    bore_depth: float | None = None,
) -> cq.Shape:
    """Build a cylindrical standoff post on XY (`Z = 0 .. height`) without string selectors.

    Parameters
    ----------
    bore_dia:
        Coaxial bore diameter (e.g. `3.2` for Ruthex `RX-M2.5x4.0` heat-set insert).
    height:
        Total standoff height in `mm`.
    outer_dia:
        Outer post diameter in `mm` (default `7.0 mm` -> `1.9 mm` wall around `Ø3.2 mm` bore).
    bore_depth:
        Blind bore depth from the top face (`+Z`), or `None` for a through-bore.
    """
    post = cq.Solid.makeCylinder(outer_dia / 2.0, height)
    if bore_depth is None or bore_depth >= height:
        hole = cq.Solid.makeCylinder(bore_dia / 2.0, height + 0.2, cq.Vector(0, 0, -0.1))
    else:
        z0 = height - bore_depth
        hole = cq.Solid.makeCylinder(bore_dia / 2.0, bore_depth + 0.1, cq.Vector(0, 0, z0))
    return post.cut(hole)
