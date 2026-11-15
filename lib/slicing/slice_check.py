"""The slicing stage refuses a print file that doesn't carry its parts' manufacturing profile.

Ground truth is a real sliced file: the settings header of coupon plate 3 (2026-11-15), sliced
before profiles existed, with no compensation (`xy_hole_compensation = 0`). That is the plate on
which the button's lip rubbed its PETG pocket. `bambu.check_sliced` must refuse it as an
`fdm_petg_x2d` plate, accept the same file once the profile's compensation (and the 8 mm brim)
is in it, and refuse tree supports where a visible face needs the continuous PLA interface.
These run without Bambu Studio, so they hold in CI.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from process.profiles import PROFILES  # noqa: E402
from slicing import bambu  # noqa: E402

FIXTURE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "fixtures", "coupon_plate3_header.txt"
)


def check_all():
    rows = []
    with open(FIXTURE, encoding="utf-8") as fh:
        real = bambu.header_settings(fh.read())
    petg = PROFILES["fdm_petg_x2d"]

    problems = bambu.check_sliced(real, petg, bambu.SUPPORT_HIDDEN)
    caught = [p for p in problems if p.startswith(("xy_hole_compensation", "xy_contour"))]
    rows.append(
        (
            "SLICE_REFUSES coupon plate 3 as sliced: no PETG compensation",
            len(caught) == 2,
            "; ".join(problems) or "accepted -- the check can't see missing compensation",
        )
    )

    fixed = {**real, **bambu.compensation(petg), "brim_width": f"{bambu.BRIM_MM:g}"}
    problems = bambu.check_sliced(fixed, petg, bambu.SUPPORT_HIDDEN)
    rows.append(
        (
            "SLICE_ACCEPTS the same plate with fdm_petg_x2d compensation and an 8 mm brim",
            not problems,
            "; ".join(problems)
            or f"holes +{petg.hole_shrink:.2f}, outside faces -{petg.contour_growth:.2f} mm",
        )
    )

    problems = bambu.check_sliced(fixed, petg, bambu.SUPPORT_VISIBLE)
    rows.append(
        (
            "SLICE_REFUSES tree supports under a visible face (normal + full PLA interface)",
            any(p.startswith("support_type") for p in problems),
            "; ".join(problems) or "accepted tree supports for a visible face",
        )
    )

    try:
        bambu.compensation(PROFILES["resin_mars"])
        ok, msg = False, "sliced with an unproven profile"
    except bambu.SliceError as e:
        ok, msg = True, str(e)
    rows.append(("SLICE_REFUSES a profile with no measured print", ok, msg))
    return rows


def main():
    rows = check_all()
    for label, ok, msg in rows:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
        print(f"        {msg}")
    return 0 if all(ok for _l, ok, _m in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
