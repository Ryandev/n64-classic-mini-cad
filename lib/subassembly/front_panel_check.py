"""Gate checks for `front_panel_mech.py`, `front_port_cover.py`, `n64_port_insert.py` & LED.

Verifies:
  - Printability (`manifold`, `single_body`, `bed`, `overhang`, `wall`, `footprint`) for
    `front_port_cover`, `n64_port_insert`, and `led_light_pipe` (Clear PETG)
  - `G13` zero boolean interference across `lower_tub`, Left & Right twin-port covers,
    all 4x `n64_port_insert` parts, `led_light_pipe`, `wired_led_3mm`, magnets, and the 4x
    `usb_a_cluster` (`TE Connectivity 292303-7`) receptacles
  - `J-05` Twin-port hinged front covers (`P1+P2` left, `P3+P4` right) seated at `Z = 13.19 mm`
    with `0.20 mm/side` XZ clearance, coaxial bottom pivot pins (`0.30 mm/side` radial clearance
    in sockets), top fingernail slits, rear magnet pockets, and clash-free `0..80 deg` swing
  - `J-07` Clear PETG `led_light_pipe` (`6.36 x 1.76 mm` N64 lenticular front lens) seated in
    `lower_tub`'s front aperture (`0.10 mm/side` clearance) & internal LED holder cradle with
    coaxial `3 mm` red through-hole LED
  - `J-08` Separately-printed shallow `n64_port_insert` (`Ø10.88 x 2.00 mm`) seated in `Ø8.2 x 0.45`
    pockets on `front_port_cover` with `0.20 mm/side` clearance
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
import printable  # noqa: E402
from assembly import datum as D  # noqa: E402
from component import led_l819, radxa_x4  # noqa: E402
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common  # noqa: E402
from OCP.BRepExtrema import BRepExtrema_DistShapeShape  # noqa: E402
from part import (  # noqa: E402
    front_port_cover,
    led_light_pipe,
    n64_port_insert,
    usb_retainer_bracket,
)
from subassembly import front_panel_mech  # noqa: E402
from variant import lower_tub  # noqa: E402


def _common_volume(a: cq.Shape, b: cq.Shape) -> float:
    com = BRepAlgoAPI_Common(a.wrapped, b.wrapped)
    com.Build()
    if not com.IsDone():
        return -1.0
    return cq.Shape.cast(com.Shape()).Volume()


def check_all():
    rows = []
    tub = lower_tub.get_shape()
    cov_single = front_port_cover.get_shape()
    cov = front_panel_mech.cover()
    inserts = front_panel_mech.port_inserts()
    pipe = led_light_pipe.get_shape()
    led3 = front_panel_mech.wired_led_3mm()
    mags = front_panel_mech.magnets()
    usb = radxa_x4.usb_a_cluster()
    ret_single = usb_retainer_bracket.get_shape()
    ret_both = front_panel_mech.usb_retainer_compound()

    # 1. Printability rows on front_port_cover, n64_port_insert, led_light_pipe & usb_retainer
    for name, shape, mod in (
        ("front_port_cover", cov_single, front_port_cover),
        ("n64_port_insert", inserts[0], n64_port_insert),
        ("led_light_pipe", pipe, led_light_pipe),
        ("usb_retainer_bracket", ret_single, usb_retainer_bracket),
    ):
        rows.extend(
            printable.check_part(
                name,
                shape,
                up=mod.PRINT_NORMAL,
                min_wall_mm=0.8,
                min_bed_ratio=0.15,
                max_aspect=3.0,
            )
        )

    # 2. Rule G13: zero boolean interference across all front panel parts
    pairs = [
        ("lower_tub/front_port_cover", tub, cov),
        ("front_port_cover/led_light_pipe", cov, pipe),
        ("lower_tub/led_light_pipe", tub, pipe),
        ("lower_tub/wired_led_3mm", tub, led3),
        ("led_light_pipe/wired_led_3mm", pipe, led3),
        ("front_port_cover/usb_a", cov, usb),
        ("lower_tub/usb_a", tub, usb),
        ("led_light_pipe/usb_a", pipe, usb),
        ("front_port_cover/insert_p1", cov, inserts[0]),
        ("front_port_cover/insert_p2", cov, inserts[1]),
        ("front_port_cover/insert_p3", cov, inserts[2]),
        ("front_port_cover/insert_p4", cov, inserts[3]),
        ("lower_tub/insert_p1", tub, inserts[0]),
        ("lower_tub/insert_p2", tub, inserts[1]),
        ("lower_tub/insert_p3", tub, inserts[2]),
        ("lower_tub/insert_p4", tub, inserts[3]),
        ("lower_tub/magnets", tub, mags),
        ("front_port_cover/magnets", cov, mags),
        ("lower_tub/usb_retainer_brackets", tub, ret_both),
        ("usb_retainer_brackets/usb_a", ret_both, usb),
        ("usb_retainer_brackets/front_port_cover", ret_both, cov),
    ]
    bad = []
    for pname, a, b in pairs:
        v = _common_volume(a, b)
        if v < 0 or v > 1e-3:
            bad.append(f"{pname}={v:.3f}mm^3")
    rows.append(
        (
            "G13_FRONT zero interference across lower_tub, twin covers, N64 inserts & LED",
            not bad,
            f"0.000 mm^3 intersection across all {len(pairs)} front-panel pairs"
            if not bad
            else "INTERFERENCE: " + ", ".join(bad),
        )
    )

    # 3. J-05: Twin hinged covers seat with 0.20mm/side XZ & swing open clash-free
    cov_bb = cov_single.BoundingBox()
    usb_bb = usb.BoundingBox()
    plate_w = cov_bb.xlen - 2.0 * D.HINGE_PIN_EXT
    xz_clear_w = (D.FRONT_BAY_W - plate_w) / 2.0
    xz_clear_h = (D.FRONT_BAY_H - cov_bb.zlen) / 2.0
    hinge_rad_clear = (D.HINGE_SOCKET_D - D.HINGE_PIN_D) / 2.0
    usb_y_gap = usb_bb.ymin - cov_bb.ymax
    pair_span = abs(D.FRONT_PORT_XS[0] - D.FRONT_PORT_XS[1]) + D.PORT_INSERT_OD
    # The doors swing with their glued port bezels (which stand proud of the hinge axis): the
    # whole 0..90 deg arc in 5 deg steps, not a couple of poses (C1: the bezels hit the sill from
    # 13 deg while the bare doors passed at 30 and 80).
    pivot = cq.Vector(0.0, D.HINGE_Y, D.HINGE_Z)
    door_and_bezels = cq.Compound.makeCompound([*front_panel_mech.covers(), *inserts])
    swing_clash = max(
        _common_volume(tub, opened) + _common_volume(pipe, opened)
        for deg in range(5, 91, 5)
        for opened in [door_and_bezels.rotate(pivot, pivot + cq.Vector(1.0, 0.0, 0.0), deg)]
    )
    flat = BRepExtrema_DistShapeShape(
        tub.wrapped,
        cq.Compound.makeCompound(inserts)
        .rotate(pivot, pivot + cq.Vector(1.0, 0.0, 0.0), 90.0)
        .wrapped,
    )
    flat.Perform()
    bezel_gap = flat.Value()
    j05_ok = (
        len(front_panel_mech.covers()) == 2
        and plate_w >= pair_span
        and 0.15 <= xz_clear_w <= 0.30
        and 0.15 <= xz_clear_h <= 0.30
        and 0.20 <= hinge_rad_clear <= 0.40
        and D.FINGER_SLIT_W >= 6.0
        and D.FINGER_SLIT_H >= 0.8
        and usb_y_gap >= 1.0
        and len(usb.Solids()) == 16
        and len(mags.Solids()) == 8
        and swing_clash <= 1e-3
        and bezel_gap >= 0.3
    )
    rows.append(
        (
            "J05_COVER twin front_port_cover doors + bezels seat & swing open 0..90 deg clash-free",
            j05_ok,
            f"covers=2x{plate_w:.1f} mm, XZ clear=({xz_clear_w:.2f},{xz_clear_h:.2f}) mm/side, "
            f"hinge radial={hinge_rad_clear:.2f} mm, USB gap={usb_y_gap:.2f} mm, "
            f"swing clash={swing_clash:.3f} mm^3 (doors + bezels, 0..90 deg), "
            f"bezel gap open flat={bezel_gap:.2f} mm (min 0.3)",
        )
    )

    # 4. J-07: Clear PETG lenticular light-pipe + 3-lead bi-colour Red/Green LED in holder cradle
    rad_clear = (D.LED_BORE_D - D.LED_SHAFT_D) / 2.0
    pipe_bb = pipe.BoundingBox()
    led3_bb = led3.BoundingBox()
    j07_ok = (
        abs(rad_clear - 0.10) < 1e-6
        and abs(pipe_bb.xlen - D.LED_FLANGE_W) < 0.05
        and abs(pipe_bb.zlen - D.LED_FLANGE_D) < 0.05
        and abs(pipe_bb.ymin - D.LED_PIPE_Y0) < 0.05
        and 0.10 <= (led3_bb.ymin - pipe_bb.ymax) <= 0.50
        and len(led_l819.LEAD_XS) == 3
        and abs(led_l819.LENS_DIA - 3.0) < 1e-6
        and abs(led3_bb.xlen - led_l819.RIM_DIA) < 0.05
        and _common_volume(tub, pipe) <= 1e-3
        and _common_volume(tub, led3) <= 1e-3
    )
    rows.append(
        (
            "J07_PIPE  Clear PETG lenticular led_light_pipe & 3-lead Red/Green LED seat in holder",
            j07_ok,
            f"lens clear={rad_clear:.2f} mm/side, collar={pipe_bb.xlen:.2f}x{pipe_bb.zlen:.2f} mm, "
            f"bi-colour 3-lead gap={led3_bb.ymin - pipe_bb.ymax:.2f} mm",
        )
    )

    # 5. J-08: Separately-printed shallow N64 port inserts seat in cover pockets (0.20 mm/side)
    ins_bb = inserts[0].BoundingBox()
    port_rad_clear = (D.PORT_POCKET_D - D.PORT_INSERT_BOSS_D) / 2.0
    total_depth = D.PORT_INSERT_BOSS_H + D.PORT_INSERT_BEZEL_H
    j08_ok = (
        len(inserts) == 4
        and 0.15 <= port_rad_clear <= 0.30
        and abs(ins_bb.xlen - D.PORT_INSERT_OD) < 0.05
        and abs(ins_bb.ylen - total_depth) < 0.05
        and 1.5 <= ins_bb.ylen <= 2.5
        and all(_common_volume(cov, ins) <= 1e-3 for ins in inserts)
    )
    rows.append(
        (
            "J08_PORT  4x shallow n64_port_insert (Ø10.88x2.0mm) seat in pockets (0.20mm/side)",
            j08_ok,
            f"radial clearance={port_rad_clear:.2f} mm/side, "
            f"insert OD={ins_bb.xlen:.2f} mm, shallow depth={ins_bb.ylen:.2f} mm",
        )
    )

    return rows


if __name__ == "__main__":
    results = check_all()
    failed = 0
    for label, ok, msg in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
        print(f"        {msg}")
        if not ok:
            failed += 1
    sys.exit(1 if failed else 0)
