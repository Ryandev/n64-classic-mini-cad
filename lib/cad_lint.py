"""Design-rule check across every part in `lib/part/`.

Findings are reported as advice with the rule that raised them; `lib/gate.py`
is the pass/fail authority.
"""

import importlib
import os
import pkgutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import laser_spec as L  # noqa: E402
import part as P  # noqa: E402
from min_wall import all_gaps  # noqa: E402
from OCP.BRepAdaptor import BRepAdaptor_Curve  # noqa: E402
from OCP.GeomAbs import GeomAbs_Circle  # noqa: E402

BED = (256.0, 256.0)
LASER_WALL = 1.5
FDM_WALL = 0.8
MIN_INTERNAL_R = L.KERF / 2
PUBLISHED_FILLET = 0.2


def _process(mod, name):
    m = getattr(mod, "MANUFACTURE", None)
    if m in ("laser", "fdm"):
        return m, None
    return None, f"DECLARE    no MANUFACTURE = 'laser' | 'fdm' at the top of {name}.py"


def _internal_corners(shape):
    tight = []
    for e in shape.Edges():
        a = BRepAdaptor_Curve(e.wrapped)
        if a.GetType() == GeomAbs_Circle:
            r = a.Circle().Radius()
            if r <= PUBLISHED_FILLET + 1e-6:
                tight.append(round(r, 3))
    return tight


def check(name, shape, mod):
    proc, undeclared = _process(mod, name)
    notes = []
    if undeclared:
        return "?", [undeclared]
    b = shape.BoundingBox()

    if proc == "fdm" and (b.xlen > BED[0] or b.ylen > BED[1]):
        notes.append(
            f"BED        {b.xlen:.0f}x{b.ylen:.0f} exceeds the {BED[0]:.0f}x{BED[1]:.0f} bed"
        )

    if proc == "laser" and b.zlen <= 20:
        gaps = all_gaps(shape, L.SHEET_T)
        thin = [g for g in gaps if g[0] < LASER_WALL]
        if thin:
            notes.append(
                f"WALL       {len(thin)} boundary pair(s) under the laser floor of "
                f"{LASER_WALL}mm, closest {thin[0][0]:.3f}mm at {thin[0][1]}"
            )
        tight = _internal_corners(shape)
        at_floor = [r for r in tight if r <= MIN_INTERNAL_R + 1e-6]
        if at_floor:
            notes.append(
                f"CORNER     {len(at_floor)} internal radius/radii at or below "
                f"kerf/2 ({MIN_INTERNAL_R:.3f}mm)"
            )
    return proc, notes


def main() -> int:
    print("CAD LINT -- notes/DESIGN_RULES.md applied to every part")
    print("advice, not a gate; lib/gate.py remains the pass/fail authority\n")
    total = 0
    for n in sorted(m.name for m in pkgutil.iter_modules(P.__path__)):
        if n.startswith("_") or n == "shared":
            continue
        try:
            m = importlib.import_module(f"part.{n}")
            if not hasattr(m, "get_shape"):
                continue
            proc, notes = check(n, m.get_shape(), m)
        except Exception as e:
            print(f"  {n:34s} skipped: {type(e).__name__}")
            continue
        if notes:
            total += len(notes)
            print(f"  {n}  [{proc}]")
            for t in notes:
                print(f"      {t}")
    print(f"\n  {total} note(s). None of these fail a build -- read them and decide.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
