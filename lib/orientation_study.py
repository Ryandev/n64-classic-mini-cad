"""How each visible part's outer skin prints in each of the six ways it can sit on the bed.

The owner paints every visible face and wants the fewest layer lines to sand (2026-11-13). How a
face prints depends on its angle to the bed (GBA `lib/slicing/PRINTING.md`, DECISIONS 10-30):

    wall       within 15 deg of vertical: even layer lines, the best painted finish
    top        flat and facing up: a top skin (iron it)
    bed        on the build plate: smooth
    terraced   a slope facing up, 15..84 deg off vertical: stair-steps ~layer / tan(slope) wide,
               the face that needs sanding
    underside  facing down but steep enough to print unsupported: a rougher down-skin
    support    facing down past 50 deg from vertical: printed on support, the worst finish

Only what shows on the assembled console counts: a face is visible if a ray from just outside
it, along its normal, leaves the whole closed case (`n64_mini`, printed parts only) without
hitting anything. A button's stem in its chimney, or a wall inside the tub, hits the case and
doesn't count. The skin is tessellated so a curved face (a dome) is judged triangle by triangle.
"""

import argparse
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cadquery as cq  # noqa: E402
from assembly import n64_mini  # noqa: E402
from OCP.gp import gp_Dir, gp_Lin, gp_Pnt  # noqa: E402
from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector  # noqa: E402
from part import (  # noqa: E402
    cartridge_flaps,
    front_bezel,
    front_port_cover,
    n64_port_insert,
    power_slider,
)
from printable import OVERHANG_DEG  # noqa: E402
from variant import lower_tub, upper_shell  # noqa: E402

PARTS = (
    ("upper_shell", upper_shell),
    ("lower_tub", lower_tub),
    ("power_slider", power_slider),  # reset_button is the same shape
    ("front_port_cover", front_port_cover),
    ("front_bezel", front_bezel),
    ("cartridge_flaps", cartridge_flaps),
    ("n64_port_insert", n64_port_insert),
)
UPS = ((0, 0, 1), (0, 0, -1), (0, 1, 0), (0, -1, 0), (1, 0, 0), (-1, 0, 0))
WALL_DEG = 15.0  # within this of vertical: prints as a wall
TOP_COS = math.cos(math.radians(6.0))  # within 6 deg of flat: a top skin, not a terrace
CLASSES = ("wall", "top", "bed", "terraced", "underside", "support")
TESS_TOL = 0.1


def _face_triangles(f: cq.Face) -> list[tuple[cq.Vector, float, cq.Vector]]:
    """(outward unit normal, area, centroid) of each triangle of one face."""
    verts, idx = f.tessellate(TESS_TOL)
    fn = f.normalAt()  # at the face's own (u, v) centre, honouring its orientation
    tris = []
    for a, b, c in idx:
        pa, pb, pc = verts[a], verts[b], verts[c]
        cross = (pb - pa).cross(pc - pa)
        area = cross.Length / 2.0
        if area < 1e-6:
            continue
        n = cross.normalized()
        if n.dot(fn) < 0:  # tessellation winding isn't guaranteed: point it outward
            n = -n
        tris.append((n, area, (pa + pb + pc) * (1.0 / 3.0)))
    return tris


def skin(
    shape: cq.Shape, it: IntCurvesFace_ShapeIntersector
) -> list[tuple[cq.Vector, float, cq.Vector]]:
    """Triangles of the visible skin: faces whose outward ray, from their largest triangle, leaves
    the assembled case (`it`, loaded with it) without hitting anything."""
    out = []
    for f in shape.Faces():
        tris = _face_triangles(f)
        if not tris:
            continue
        n, _, c = max(tris, key=lambda t: t[1])
        start = c + n * 0.05
        it.Perform(gp_Lin(gp_Pnt(start.x, start.y, start.z), gp_Dir(n.x, n.y, n.z)), 0.0, 1e4)
        if it.NbPnt() == 0:
            out.extend(tris)
    return out


def classify(
    shape: cq.Shape, tris: list[tuple[cq.Vector, float, cq.Vector]], up: tuple[float, float, float]
) -> dict[str, float]:
    """Skin area (mm^2) in each class when the part prints with `up` pointing up."""
    u = cq.Vector(*up)
    bb = shape.BoundingBox()
    corners = [
        cq.Vector(x, y, z)
        for x in (bb.xmin, bb.xmax)
        for y in (bb.ymin, bb.ymax)
        for z in (bb.zmin, bb.zmax)
    ]
    floor = min(p.dot(u) for p in corners)
    sin_wall = math.sin(math.radians(WALL_DEG))
    cos_support = -math.sin(math.radians(OVERHANG_DEG))
    out = dict.fromkeys(CLASSES, 0.0)
    for n, area, centre in tris:
        d = n.dot(u)
        if abs(d) <= sin_wall:
            out["wall"] += area
        elif d >= TOP_COS:
            out["top"] += area
        elif d > 0:
            out["terraced"] += area
        elif centre.dot(u) - floor < 0.2:
            out["bed"] += area
        elif d < cos_support:
            out["support"] += area
        else:
            out["underside"] += area
    return out


def main(argv: list[str] | None = None) -> int:
    """Print the table for every visible part (or the named ones)."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("names", nargs="*")
    args = ap.parse_args(argv)
    chosen = [(n, m) for n, m in PARTS if not args.names or n in args.names]
    if not chosen:
        print(f"no part matches {args.names}; have {[n for n, _ in PARTS]}")
        return 2
    case = IntCurvesFace_ShapeIntersector()
    case.Load(n64_mini.get_shape(include_electronics=False).wrapped, 1e-4)
    for name, mod in chosen:
        shape = mod.get_shape()
        tris = skin(shape, case)
        current = tuple(mod.PRINT_NORMAL)
        print(f"\n== {name} (now prints up={current})", flush=True)
        print("   up          " + "  ".join(f"{c:>9}" for c in CLASSES) + "   (% of visible skin)")
        for up in UPS:
            got = classify(shape, tris, up)
            total = sum(got.values()) or 1.0
            mark = " <- now" if up == current else ""
            row = "  ".join(f"{100 * got[c] / total:8.1f}%" for c in CLASSES)
            print(f"   {str(up):<12}{row}{mark}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
