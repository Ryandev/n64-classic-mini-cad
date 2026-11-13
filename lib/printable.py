"""Can the printer make this part?

Six questions, all hard pass/fail:

    manifold      BRepAlgoAPI_Check (NOT isValid() -- see lint_structure.py)
    single_body   len(Solids()) == 1, so no orphan floaters from a cut
    bed           fits 256 x 256 x 256 mm (Bambu X2D / P1S build volume)
    overhang      downward faces past 50 deg from vertical: each must be a bridge the printer
                  spans without support (<= BRIDGE_MAX_MM across); a wider one fails, and WHERE
    wall          local wall thickness by ray test from face centroids
    footprint     first-layer contact on the bed + aspect ratio (G3)
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cadquery as cq  # noqa: E402
from cadquery.occ_impl.shapes import check as bop_check  # noqa: E402
from OCP.BRepAdaptor import BRepAdaptor_Surface  # noqa: E402
from OCP.BRepClass3d import BRepClass3d_SolidClassifier  # noqa: E402
from OCP.BRepGProp import BRepGProp_Face  # noqa: E402
from OCP.GeomAbs import GeomAbs_Torus  # noqa: E402
from OCP.gp import gp_Pnt, gp_Vec  # noqa: E402
from OCP.TopAbs import TopAbs_IN, TopAbs_ON  # noqa: E402

BED_MM = (256.0, 256.0, 256.0)
OVERHANG_DEG = 50.0  # past this from vertical, the slicer adds support
MIN_WALL_MM = 0.8  # two perimeters on a 0.4 mm nozzle
# Widest downward face printed with no support: a short bridge between walls. The tub's floating
# floor (93 mm across) passed for months while this row was advisory only (C9, 2026-11-13); the
# widest the flush tub keeps is the Ø6.5 counterbore ceilings.
BRIDGE_MAX_MM = 10.0


def check_manifold(shape: cq.Shape):
    if not bool(bop_check(shape)):
        return False, "self-intersection or bad topology"
    for f in shape.Faces():
        ad = BRepAdaptor_Surface(f.wrapped)
        if ad.GetType() == GeomAbs_Torus:
            t = ad.Torus()
            if t.MinorRadius() > t.MajorRadius() + 1e-6:
                return (
                    False,
                    f"self-intersecting spindle torus (R1={t.MajorRadius():.2f} < "
                    f"R2={t.MinorRadius():.2f})",
                )
    return True, "BRepAlgoAPI_Check clean"


def check_single_body(shape: cq.Shape):
    n = len(shape.Solids())
    return n == 1, f"{n} solid(s)" + (" -- disjoint piece in the part" if n != 1 else "")


def check_bed(shape: cq.Shape, bed=BED_MM):
    bb = shape.BoundingBox()
    dims = sorted((bb.xlen, bb.ylen, bb.zlen))
    b = sorted(bed)
    ok = all(d <= lim for d, lim in zip(dims, b))
    return ok, f"{bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm (limit {bed[0]:.0f}^3)"


def _span_across(face: cq.Face) -> float:
    """How wide a bridge `face` is: the short side of the rectangle with its area and perimeter.

    Exact for a rectangle; a ring comes out near its radial width, not its diameter (the bounding
    box called a thin ring as wide as its diameter), and a round face near 0.8 x its diameter.
    """
    perimeter = sum(e.Length() for e in face.Edges())
    half = perimeter / 2.0
    disc = max(half * half - 4.0 * face.Area(), 0.0)
    return (half - math.sqrt(disc)) / 2.0


def check_overhang(
    shape: cq.Shape,
    up=(0, 0, 1),
    limit_deg=OVERHANG_DEG,
    max_bridge=BRIDGE_MAX_MM,
    support_mm2: float = 0.0,
):
    """Faces pointing down past `limit_deg` from vertical and wider than a bridge need support.

    A part may declare `SUPPORT_MM2` (area, with why it is acceptable: hidden faces only, PETG
    body with a PLA interface, notes/PRINTING.md). The row fails when the part needs more support
    than it declares, so new overhangs fail instead of being printed as an advisory.
    """
    ux, uy, uz = up
    ul = math.sqrt(ux * ux + uy * uy + uz * uz)
    ux, uy, uz = ux / ul, uy / ul, uz / ul
    cos_lim = -math.sin(math.radians(limit_deg))

    bb = shape.BoundingBox()
    corners = [
        (x, y, z)
        for x in (bb.xmin, bb.xmax)
        for y in (bb.ymin, bb.ymax)
        for z in (bb.zmin, bb.zmax)
    ]
    z_floor = min(x * ux + y * uy + z * uz for x, y, z in corners)
    needs = 0.0
    widest = 0.0
    widest_at = None
    for f in shape.Faces():
        n = f.normalAt()
        c = f.Center()
        dot = n.x * ux + n.y * uy + n.z * uz
        h = c.x * ux + c.y * uy + c.z * uz
        if h - z_floor < 0.2 or dot >= cos_lim:
            continue  # on the build plate, or steep enough to print unsupported
        span = _span_across(f)
        if span > max_bridge:
            needs += f.Area()
        if span > widest:
            widest, widest_at = span, (c.x, c.y, c.z)
    if widest_at is None:
        return True, f"nothing past {limit_deg:.0f} deg from vertical (up={up})"
    where = f"({widest_at[0]:.1f},{widest_at[1]:.1f},{widest_at[2]:.1f})"
    return (
        needs <= support_mm2,
        f"needs support under {needs:.0f} mm^2 (declared {support_mm2:.0f}); widest "
        f"{widest:.1f} mm across at {where} (bridge limit {max_bridge:.0f} mm, up={up})",
    )


def check_wall(shape: cq.Shape, min_mm=MIN_WALL_MM):
    """For each face's UV midpoint on the surface, step inward along -normal;
    if already outside the solid before `min_mm`, the wall there is thinner than `min_mm`."""
    clf = BRepClass3d_SolidClassifier(shape.wrapped)
    probe = min_mm * 0.85
    thin = 0
    thinnest_at = None
    checked = 0
    for f in shape.Faces():
        if f.Area() < 1.0:
            continue  # chamfer/fillet sliver, not a wall
        try:
            u0, u1, v0, v1 = f._uvBounds()
            u, v = 0.5 * (u0 + u1), 0.5 * (v0 + v1)
            p, vn = gp_Pnt(), gp_Vec()
            BRepGProp_Face(f.wrapped).Normal(u, v, p, vn)
            if vn.Magnitude() < 1e-9:
                continue
            vn.Normalize()
            # Skip if (u_mid, v_mid) falls inside an interior hole of a perforated face
            clf.Perform(p, 1e-3)
            if clf.State() != TopAbs_ON:
                continue
        except Exception:
            continue
        checked += 1
        pin = gp_Pnt(
            p.X() - vn.X() * probe,
            p.Y() - vn.Y() * probe,
            p.Z() - vn.Z() * probe,
        )
        clf.Perform(pin, 1e-4)
        if clf.State() != TopAbs_IN:
            thin += 1
            if thinnest_at is None:
                thinnest_at = (p.X(), p.Y(), p.Z())
    ok = thin == 0 and checked > 0
    msg = f"{checked} faces >=1 mm^2 probed at {probe:.2f} mm, {thin} thin"
    if thinnest_at:
        msg += f" (first at ({thinnest_at[0]:.1f},{thinnest_at[1]:.1f},{thinnest_at[2]:.1f}))"
    return ok, msg


def check_footprint(
    shape: cq.Shape,
    up=(0, 0, 1),
    min_bed_ratio: float = 0.15,
    max_aspect: float = 3.0,
):
    """Rule G3: bed contact & footprint stability under `PRINT_NORMAL` (`up`)."""
    ux, uy, uz = up
    ul = math.sqrt(ux * ux + uy * uy + uz * uz)
    ux, uy, uz = ux / ul, uy / ul, uz / ul

    bb = shape.BoundingBox()
    corners = [
        (x, y, z)
        for x in (bb.xmin, bb.xmax)
        for y in (bb.ymin, bb.ymax)
        for z in (bb.zmin, bb.zmax)
    ]
    hs = [x * ux + y * uy + z * uz for x, y, z in corners]
    h_min, h_max = min(hs), max(hs)
    height = h_max - h_min

    axis_spans = [bb.xlen, bb.ylen, bb.zlen]
    up_idx = max(range(3), key=lambda i: abs((ux, uy, uz)[i]))
    lateral_spans = [axis_spans[i] for i in range(3) if i != up_idx]
    footprint_area = lateral_spans[0] * lateral_spans[1]
    min_base_span = min(lateral_spans)

    bed_area = 0.0
    for f in shape.Faces():
        try:
            n = f.normalAt()
            c = f.Center()
        except Exception:
            continue
        dot = n.x * ux + n.y * uy + n.z * uz
        h = c.x * ux + c.y * uy + c.z * uz
        if dot < -0.95 and abs(h - h_min) < 0.25:
            bed_area += f.Area()

    bed_ratio = bed_area / max(footprint_area, 1e-6)
    aspect = height / max(min_base_span, 1e-6)
    ok = bed_ratio >= min_bed_ratio and aspect <= max_aspect
    msg = (
        f"bed contact {bed_area:.0f}/{footprint_area:.0f} mm^2 ({bed_ratio * 100:.1f}%, "
        f"min {min_bed_ratio * 100:.0f}%), H/base {height:.1f}/{min_base_span:.1f} = "
        f"{aspect:.2f} (max {max_aspect:.1f})"
    )
    return ok, msg


def check_part(
    name: str,
    shape: cq.Shape,
    up=(0, 0, 1),
    min_wall_mm: float = MIN_WALL_MM,
    min_bed_ratio: float | None = None,
    max_aspect: float = 3.0,
    support_mm2: float = 0.0,
):
    """Returns a list of (check_name, passed, message) for `gate.py`."""
    rows = [
        (f"{name}:manifold", *check_manifold(shape)),
        (f"{name}:single_body", *check_single_body(shape)),
        (f"{name}:bed", *check_bed(shape)),
        (f"{name}:overhang", *check_overhang(shape, up=up, support_mm2=support_mm2)),
        (f"{name}:wall", *check_wall(shape, min_mm=min_wall_mm)),
    ]
    if min_bed_ratio is not None:
        rows.append(
            (
                f"{name}:footprint",
                *check_footprint(
                    shape,
                    up=up,
                    min_bed_ratio=min_bed_ratio,
                    max_aspect=max_aspect,
                ),
            )
        )
    return rows
