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


def check_all():
    rows = []
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
