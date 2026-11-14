"""The printability check must agree with what the printer actually did.

Ground truth (MFIC rung 1, a real system): coupon plate 1, printed 2026-11-14 on the X2D in black
PETG at 0.20 mm with NO supports, judged by the owner. Each piece is rebuilt exactly as it was
printed (crop + `PRINT_NORMAL`, `coupons.build`) and given to `printable.check_overhang` with no
support declared, as it was sliced. A piece that failed on the bed must fail the check, and one
that printed clean must pass it. A row fails when the two disagree.

What failed, and where (owner's FreeCAD selection):
  - tub_tower: the switch V-pin, a horizontal pin whose underside starts ~13.5 mm up
  - bracket: the side peg (Ø2.8 x 4.3), sticking out ~3 mm above the bed
  - power_button_on_side: the rounded cap end, 1-4 mm above the bed
  - shell_chimney: the skin, 4.5-7.6 mm above the bed, held only by the chimney; it drooped and
    its free edge curled up
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
import coupons  # noqa: E402
import printable  # noqa: E402

# piece name -> printed clean on plate 1 (owner, 2026-11-14)
PLATE1 = {
    "1_button_chimney_shell_chimney": False,
    "1_button_chimney_power_button": True,
    "1_button_chimney_power_button_on_side": False,
    "1_button_chimney_bracket": False,
    "2_switch_tower_tub_tower": False,
    "6_hole_gauge_wall_sideways": True,
    "6_hole_gauge_plate_downward": True,
}


def _wall_with_opening(width: float) -> cq.Shape:
    """A 2.2 mm wall, 14 mm tall, with a `width` x 5 mm window through it 4 mm up."""
    wall = cq.Solid.makeBox(width + 10.0, 2.2, 14.0)
    window = cq.Solid.makeBox(width, 2.2, 5.0, cq.Vector(5.0, 0.0, 4.0))
    return wall.cut(window)


def _wall_with_pin(length: float) -> cq.Shape:
    """A wall with a Ø2.8 pin sticking `length` out of its side, 5 mm up."""
    wall = cq.Solid.makeBox(10.0, 3.0, 10.0)
    pin = cq.Solid.makeCylinder(1.4, length, cq.Vector(5.0, 3.0, 5.0), cq.Vector(0, 1, 0))
    return wall.fuse(pin)


# Shapes whose answer is known from how FDM works (lower rung than the print: the author's own
# picks), one per kind of overhang, so each branch of the rule can fail on its own.
RULES = (
    ("a 6 mm window in a wall bridges (held at both ends)", _wall_with_opening(6.0), True),
    ("a 12 mm window needs support (bridge over 10 mm)", _wall_with_opening(12.0), False),
    ("a sideways pin needs support (held at one end)", _wall_with_pin(4.0), False),
)


def check_all():
    rows = []
    for label, shape, printable_ok in RULES:
        ok, msg = printable.check_overhang(shape, up=(0, 0, 1), support_mm2=0.0)
        rows.append((f"PRINT_RULE {label}", ok == printable_ok, msg))
    built = {}
    for c in coupons.COUPONS:
        if any(k.startswith(c.name + "_") for k in PLATE1):
            for name, shape, _msg in coupons.build(c):
                built[name] = shape
    for name, printed_ok in PLATE1.items():
        if name not in built:
            rows.append((f"PRINT_OUTCOME {name}", False, "piece no longer built by coupons.py"))
            continue
        # The bedded shape sits on z=0 with its print-up along +Z.
        ok, msg = printable.check_overhang(built[name], up=(0, 0, 1), support_mm2=0.0)
        said = "printable" if ok else "needs support"
        real = "printed clean" if printed_ok else "FAILED on the bed"
        rows.append(
            (f"PRINT_OUTCOME {name}", ok == printed_ok, f"check: {said}; real: {real}; {msg}")
        )
    return rows


def main():
    rows = check_all()
    for label, ok, msg in rows:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
        print(f"        {msg}")
    return 0 if all(ok for _l, ok, _m in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
