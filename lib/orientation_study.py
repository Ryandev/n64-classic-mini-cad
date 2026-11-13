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

Only the outer skin counts: a face is visible if a ray from just outside it, along its normal,
leaves the part without hitting it again (an internal wall's ray hits the opposite wall). The
skin is tessellated so a curved face (a dome) is judged triangle by triangle, not by one normal.
"""

import argparse
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cadquery as cq  # noqa: E402
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


def _visible_faces(shape: cq.Shape) -> list[cq.Face]:
    """Faces whose outward ray leaves the part: its outer skin."""
    it = IntCurvesFace_ShapeIntersector()
    it.Load(shape.wrapped, 1e-4)
    out = []
    for f in shape.Faces():
        c = f.Center()
        n = f.normalAt(c)
        start = c + n * 0.05
        it.Perform(gp_Lin(gp_Pnt(start.x, start.y, start.z), gp_Dir(n.x, n.y, n.z)), 0.0, 1e4)
        if it.NbPnt() == 0:
            out.append(f)
    return out


def _triangles(faces: list[cq.Face]) -> list[tuple[cq.Vector, float, float]]:
    """(unit normal, area, height-reference z) of every skin triangle, normals facing out."""
    tris = []
    for f in faces:
        verts, idx = f.tessellate(TESS_TOL)
        fn = f.normalAt(f.Center())
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


def classify(shape: cq.Shape, up: tuple[float, float, float]) -> dict[str, float]:
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
    for n, area, centre in _triangles(_visible_faces(shape)):
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
    for name, mod in chosen:
        shape = mod.get_shape()
        current = tuple(mod.PRINT_NORMAL)
        print(f"\n== {name} (now prints up={current})", flush=True)
        print("   up          " + "  ".join(f"{c:>9}" for c in CLASSES) + "   (% of visible skin)")
        for up in UPS:
            got = classify(shape, up)
            total = sum(got.values()) or 1.0
            mark = " <- now" if up == current else ""
            row = "  ".join(f"{100 * got[c] / total:8.1f}%" for c in CLASSES)
            print(f"   {str(up):<12}{row}{mark}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
