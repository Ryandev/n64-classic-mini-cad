"""No printed part has a feature hanging on a joint thinner than the minimum wall.

Coupon plate 3 (2026-11-15) lost the upper shell's inner rim on both shell coupons: it hung on the
wall by one 0.2 mm layer above the lip groove. `printable.check_necks` slices each part across X
and across Y and finds any piece that comes away when the slice is shrunk by half the minimum
wall (0.8 mm, two perimeters).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from part import (  # noqa: E402
    cartridge_flaps,
    cooling_duct,
    cooling_hood,
    duct_floor,
    front_bezel,
    front_port_cover,
    led_light_pipe,
    n64_port_insert,
    power_slider,
    reset_button,
    usb_retainer_bracket,
)
from process import printable  # noqa: E402
from variant import lower_tub, upper_shell  # noqa: E402

PARTS = (
    ("upper_shell", upper_shell),
    ("lower_tub", lower_tub),
    ("cooling_duct", cooling_duct),
    ("cooling_hood", cooling_hood),
    ("duct_floor", duct_floor),
    ("usb_retainer_bracket", usb_retainer_bracket),
    ("front_port_cover", front_port_cover),
    ("n64_port_insert", n64_port_insert),
    ("led_light_pipe", led_light_pipe),
    ("power_slider", power_slider),
    ("reset_button", reset_button),
    ("cartridge_flaps", cartridge_flaps),
    ("front_bezel", front_bezel),
)


# Spots where a slice shows a piece hanging but the part, in 3D, does not: (across, at, why)
ACCEPTED = {
    "cooling_duct": (
        (
            "y",
            9.0,
            "the left fan wall, cut where it meets the plate ledge: in this slice its only link is "
            "the 0.8 mm ledge, but it is a continuous wall joined along its length "
            "(FreeCAD section, 2026-11-15)",
        ),
    ),
}


def check_all():
    rows = []
    for name, mod in PARTS:
        ok, msg = printable.check_necks(mod.get_shape(), accepted=ACCEPTED.get(name, ()))
        rows.append((f"NECK {name}", ok, msg))
    return rows


def main():
    rows = check_all()
    for label, ok, msg in rows:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
        print(f"        {msg}")
    return 0 if all(ok for _l, ok, _m in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
