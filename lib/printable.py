"""Can the printer make this part?

Six questions, all hard pass/fail:

    manifold      BRepAlgoAPI_Check (NOT isValid() -- see lint_structure.py)
    single_body   len(Solids()) == 1, so no orphan floaters from a cut
    bed           fits 256 x 256 x 256 mm (Bambu X2D / P1S build volume)
    overhang      sliced in 0.2 mm layers: what each layer prints onto air must be a bridge held on
                  two sides (<= BRIDGE_MAX_MM across); a cantilever or a mid-air start fails
    wall          local wall thickness by ray test from face centroids
    footprint     first-layer contact on the bed + aspect ratio (G3)
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cadquery as cq  # noqa: E402
import shapely  # noqa: E402
from cadquery.occ_impl.shapes import check as bop_check  # noqa: E402
from OCP.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface  # noqa: E402
from OCP.BRepClass3d import BRepClass3d_SolidClassifier  # noqa: E402
from OCP.BRepGProp import BRepGProp_Face  # noqa: E402
from OCP.BRepTools import BRepTools_WireExplorer  # noqa: E402
from OCP.GeomAbs import GeomAbs_Torus  # noqa: E402
from OCP.gp import gp_Pnt, gp_Vec  # noqa: E402
from OCP.TopAbs import TopAbs_IN, TopAbs_ON, TopAbs_REVERSED  # noqa: E402
from shapely.affinity import rotate  # noqa: E402
from shapely.geometry import LineString, Polygon  # noqa: E402
from shapely.geometry.base import BaseGeometry  # noqa: E402
from shapely.ops import unary_union  # noqa: E402
from shapely.validation import make_valid  # noqa: E402

BED_MM = (256.0, 256.0, 256.0)
OVERHANG_DEG = 50.0  # past this from vertical, the slicer adds support
MIN_WALL_MM = 0.8  # two perimeters on a 0.4 mm nozzle
# Widest downward face printed with no support: a short bridge between walls. The tub's floating
# floor (93 mm across) passed for months while this row was advisory only (C9, 2026-11-13); the
# widest the flush tub keeps is the Ø6.5 counterbore ceilings.
BRIDGE_MAX_MM = 10.0
LAYER_MM = 0.20  # the layer height every part is sliced at (notes/PRINTING.md)
SECTION_STEP_MM = 0.1  # how finely a section's curved edges are followed
# A traced section must match OpenCASCADE's exact area: a dropped or doubled loop raises (a first
# version that rebuilt loops from loose edges filled the shell's holes: 8,685 mm^2 for 2,177).
SECTION_AREA_TOL = 0.01
ANCHOR_REACH_MM = 0.05  # an unheld region touching the layer below within this is held there
MIN_LOOSE_MM2 = 0.001  # numerical dust from the section boolean, skipped before measuring
LINE_W_MM = 0.42  # extrusion width on the 0.4 mm nozzle (notes/PRINTING.md)
# An overhang this close to the bed can only sag onto it. Coupon plate 1 (2026-11-14): the
# upright button's lever pocket roof, printed 0.8 mm up, came out clean; the cap end of the button
# printed on its side, 1.3 mm up, failed.
BED_CATCH_MM = 1.0
BRIDGE_ANGLES = tuple(range(0, 180, 15))  # directions a bridge is tried in, degrees
BRIDGE_PITCH_MM = 0.2  # spacing of the lines laid across a region when trying a bridge


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


def orient_to_bed(shape: cq.Shape, up: tuple[float, float, float]) -> cq.Shape:
    """Rotate `shape` so `up` points along `+Z` and shift `(xmin, ymin, zmin)` to `(0, 0, 0)`."""
    ux, uy, uz = (round(float(v), 4) for v in up)
    origin = cq.Vector(0.0, 0.0, 0.0)
    if (ux, uy, uz) == (0.0, 0.0, 1.0):
        rot = shape
    elif (ux, uy, uz) == (0.0, 0.0, -1.0):
        rot = shape.rotate(origin, cq.Vector(1.0, 0.0, 0.0), 180.0)
    elif (ux, uy, uz) == (0.0, -1.0, 0.0):
        rot = shape.rotate(origin, cq.Vector(1.0, 0.0, 0.0), -90.0)
    elif (ux, uy, uz) == (0.0, 1.0, 0.0):
        rot = shape.rotate(origin, cq.Vector(1.0, 0.0, 0.0), 90.0)
    elif (ux, uy, uz) == (1.0, 0.0, 0.0):
        rot = shape.rotate(origin, cq.Vector(0.0, 1.0, 0.0), -90.0)
    elif (ux, uy, uz) == (-1.0, 0.0, 0.0):
        rot = shape.rotate(origin, cq.Vector(0.0, 1.0, 0.0), 90.0)
    else:
        raise ValueError(f"unsupported non-axis PRINT_NORMAL: {up!r}")

    bb = rot.BoundingBox()
    return rot.moved(cq.Location(cq.Vector(-bb.xmin, -bb.ymin, -bb.zmin)))


def _ring(wire: cq.Wire, face: cq.Face) -> list[tuple[float, float]]:
    """The wire's points in order round the face, curved edges followed every SECTION_STEP_MM."""
    pts: list[tuple[float, float]] = []
    explorer = BRepTools_WireExplorer(wire.wrapped, face.wrapped)
    while explorer.More():
        edge = explorer.Current()
        curve = BRepAdaptor_Curve(edge)
        t0, t1 = curve.FirstParameter(), curve.LastParameter()
        n = max(2, math.ceil(cq.Edge(edge).Length() / SECTION_STEP_MM) + 1)
        ts = [t0 + (t1 - t0) * i / (n - 1) for i in range(n)]
        if edge.Orientation() == TopAbs_REVERSED:
            ts.reverse()
        for t in ts[:-1]:  # the next edge starts where this one ends
            p = curve.Value(t)
            pts.append((p.X(), p.Y()))
        explorer.Next()
    return pts


def _section(shape: cq.Shape, z: float, bb) -> BaseGeometry:
    """The part's cross-section at height `z`, as a shapely region (holes and islands kept)."""
    plane = cq.Face.makePlane(
        bb.xlen + 10.0, bb.ylen + 10.0, cq.Vector(bb.center.x, bb.center.y, z), cq.Vector(0, 0, 1)
    )
    faces = shape.intersect(plane).Faces()
    regions = []
    for face in faces:
        poly = Polygon(_ring(face.outerWire(), face), [_ring(w, face) for w in face.innerWires()])
        regions.append(poly if poly.is_valid else make_valid(poly))
    out = unary_union(regions)
    exact = sum(f.Area() for f in faces)
    if abs(out.area - exact) > SECTION_AREA_TOL * max(exact, 1.0):
        raise ValueError(f"section at z={z:.2f}: {out.area:.1f} mm^2 traced vs {exact:.1f} exact")
    return out


def _bridges(region: Polygon, hold: BaseGeometry, max_bridge: float, angle: float) -> bool:
    """Do lines laid across `region` at `angle` all start and end on `hold`, within a bridge?"""
    c = region.centroid
    r = rotate(region, -angle, origin=c)
    h = rotate(hold, -angle, origin=c)
    x0, y0, x1, y1 = r.bounds
    y = y0 + BRIDGE_PITCH_MM / 2.0
    while y < y1:
        cut = LineString([(x0 - 1.0, y), (x1 + 1.0, y)]).intersection(r)
        for seg in getattr(cut, "geoms", [cut]):
            if seg.is_empty or seg.geom_type != "LineString" or seg.length < LINE_W_MM / 2.0:
                continue
            if seg.length > max_bridge:
                return False
            ends = seg.boundary.geoms
            if any(h.distance(e) > ANCHOR_REACH_MM for e in ends):
                return False
        y += BRIDGE_PITCH_MM
    return True


def _hold_kind(region: Polygon, held: BaseGeometry, max_bridge: float):
    """How `region`, printed past what the layer below holds up, is held: "line" or "bridge" if
    it prints, None if it needs support.

    "line": no point of it is more than half an extrusion line from a hold, so the line still
    sits mostly on the layer below. "bridge": in some direction every line laid across it starts
    and ends on a hold, no longer than `max_bridge` (a window in a wall, a pocket ceiling held on
    three sides, a hole closed over, the two-layer bridge over a counterbore). Otherwise it is a
    cantilever (a peg, a pin, a skin stepping out layer after layer, a ring round a hole) or held
    nowhere: it needs support.
    """
    touch = region.boundary.intersection(held.buffer(ANCHOR_REACH_MM))
    if touch.is_empty or touch.length < ANCHOR_REACH_MM:
        return None
    if shapely.hausdorff_distance(region, touch, densify=0.1) <= LINE_W_MM / 2.0:
        return "line"
    if any(_bridges(region, held, max_bridge, a) for a in BRIDGE_ANGLES):
        return "bridge"
    return None


def check_overhang(
    shape: cq.Shape,
    up=(0, 0, 1),
    limit_deg=OVERHANG_DEG,
    max_bridge=BRIDGE_MAX_MM,
    support_mm2: float = 0.0,
    layer_mm: float = LAYER_MM,
):
    """Slice the part as the printer does and find what each layer prints onto air.

    Each layer may step out past the one below by `layer * tan(limit)`; anything further out is
    unsupported. It still prints if it is within half a line of a hold, or bridges (`_bridges`:
    one direction in which every line across it is held at both ends, within `max_bridge`), or
    lies in the first BED_CATCH_MM, where it can only sag onto the bed. Anything else (a peg, a
    pin, a skin stepping out layer after layer, a ring round a hole, a start in mid-air) needs
    support.

    This replaced a face-by-face test (2026-11-14) that took one normal per face, so a cylinder's
    underside read as level, and called any narrow face a bridge without asking what held it up.
    It passed four coupons that failed on the printer (`print_outcome_check.py`).

    A part may declare `SUPPORT_MM2` (projected area, with why it is acceptable: hidden faces only,
    PETG body with a PLA interface, notes/PRINTING.md). The row fails when the part needs more
    support than it declares.
    """
    s = orient_to_bed(shape, up)
    bb = s.BoundingBox()
    step = layer_mm * math.tan(math.radians(limit_deg))
    below = None
    needs = 0.0
    worst, worst_at = 0.0, None
    n_layers = max(1, math.ceil(bb.zlen / layer_mm))
    for i in range(n_layers):
        z = min((i + 0.5) * layer_mm, bb.zlen - 1e-3)
        here = _section(s, z, bb)
        if below is not None and not here.is_empty:
            held = below.buffer(step)
            loose = here.difference(held)
            for r in getattr(loose, "geoms", [loose]):
                if r.is_empty or r.area < MIN_LOOSE_MM2:
                    continue
                if z <= BED_CATCH_MM or _hold_kind(r, held, max_bridge):
                    continue
                needs += r.area
                if r.area > worst:
                    c = r.representative_point()
                    worst, worst_at = r.area, (c.x, c.y, z)
        below = here
    if worst_at is None:
        return True, f"every layer is held from below or bridged (up={up})"
    where = f"({worst_at[0]:.1f},{worst_at[1]:.1f},z={worst_at[2]:.1f} as printed)"
    return (
        needs <= support_mm2,
        f"needs support under {needs:.0f} mm^2 (declared {support_mm2:.0f}); largest unheld "
        f"region {worst:.1f} mm^2 at {where} (up={up})",
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
