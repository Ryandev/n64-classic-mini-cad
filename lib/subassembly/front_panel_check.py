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

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402
from component import radxa_x4  # noqa: E402
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common  # noqa: E402
from OCP.BRepExtrema import BRepExtrema_DistShapeShape  # noqa: E402
from part import (  # noqa: E402
    cooling_duct,
    front_io_carrier_l,
    front_io_carrier_r,
    front_port_cover,
    led_light_pipe,
    n64_port_insert,
    usb_retainer_bracket,
)
from process import printable  # noqa: E402
from subassembly import front_panel_mech  # noqa: E402
from testing import probe  # noqa: E402
from variant import lower_tub  # noqa: E402


def _common_volume(a: cq.Shape, b: cq.Shape) -> float:
    com = BRepAlgoAPI_Common(a.wrapped, b.wrapped)
    com.Build()
    if not com.IsDone():
        return -1.0
    return cq.Shape.cast(com.Shape()).Volume()


def _hinge_pins_row(tub: cq.Shape, carriers: cq.Shape, covers: list, usb: cq.Shape) -> tuple:
    """HINGE_PINS (J-05, owner 2026-11-17): each bay's continuous Ø1.5 x 31.4 mm steel hinge pin
    runs through both carrier cheeks and the door knuckle on the bench (through-bored at both ends
    so the pin can be pushed out for disassembly) and sits behind >= 0.8 mm walls."""
    from OCP.BRepClass3d import BRepClass3d_SolidClassifier
    from OCP.gp import gp_Pnt
    from OCP.TopAbs import TopAbs_IN, TopAbs_OUT

    def solid_round(shape: cq.Shape, x: float, r: float) -> bool:
        clf = BRepClass3d_SolidClassifier(shape.wrapped)
        for k in range(12):
            a = math.radians(30.0 * k)
            clf.Perform(gp_Pnt(x, D.HINGE_Y + r * math.cos(a), D.HINGE_Z + r * math.sin(a)), 1e-4)
            if clf.State() != TopAbs_IN:
                return False
        return True

    along = cq.Vector(1.0, 0.0, 0.0)
    wall = 0.8 - 0.01
    clf_car = BRepClass3d_SolidClassifier(carriers.wrapped)

    msgs, ok = [], True
    for bx, door in zip(D.FRONT_BAY_XS, covers):
        side = -1.0 if bx < 0.0 else 1.0  # towards the outer wall
        w_door = D.FRONT_BAY_W - 2.0 * D.FRONT_COVER_CLEAR
        half_door = w_door / 2.0
        inner_bar_c = bx - side * (half_door - D.HINGE_BARREL_W / 2.0)
        outer_bar_c = bx + side * (half_door - D.HINGE_BARREL_W / 2.0)
        length = D.HINGE_PIN_COUNT * D.HINGE_PIN_L
        x0 = bx - length / 2.0
        pin = cq.Solid.makeCylinder(
            D.HINGE_PIN_D / 2.0, length, cq.Vector(x0, D.HINGE_Y, D.HINGE_Z), along
        )
        clash = (
            _common_volume(pin, tub)
            + _common_volume(pin, door)
            + _common_volume(pin, carriers)
            + _common_volume(pin, usb)
        )
        # Verify the pin is retained 360-deg by the carrier barrels on the bench (pulling -Y
        # out the front must intersect the carrier barrels by >= 2.0 mm^3) and drops straight
        # down (-Z) into `lower_tub` with the carrier & door with 0.000 mm^3 collision.
        pin_front = pin.moved(cq.Location(cq.Vector(0.0, -0.50, 0.0)))
        bench_held = _common_volume(pin_front, carriers) >= 2.0
        drop_clash = max(
            _common_volume(pin.moved(cq.Location(cq.Vector(0.0, 0.0, dz))), tub)
            + _common_volume(door.moved(cq.Location(cq.Vector(0.0, 0.0, dz))), tub)
            + _common_volume(carriers.moved(cq.Location(cq.Vector(0.0, 0.0, dz))), tub)
            for dz in (0.5, 2.0, 5.0, 10.0)
        )
        # Both carrier barrels are through-bored along X so a pin punch pushes the pin out on bench
        through_open = True
        for px in (
            outer_bar_c,
            bx + side * (half_door + 0.5),
            inner_bar_c,
            bx - side * (half_door + 0.5),
        ):
            clf_car.Perform(gp_Pnt(px, D.HINGE_Y, D.HINGE_Z), 1e-4)
            if clf_car.State() != TopAbs_OUT:
                through_open = False
        walls = (
            solid_round(door, bx, D.HINGE_BORE_D / 2.0 + wall)
            and solid_round(carriers, outer_bar_c, D.HINGE_PRESS_D / 2.0 + wall)
            and solid_round(carriers, inner_bar_c, D.HINGE_INNER_BORE_D / 2.0 + wall)
        )
        bay_ok = (
            clash <= 0.01
            and walls
            and through_open
            and bench_held
            and drop_clash <= 1e-3
            and abs(length - w_door) <= 0.05
        )
        ok = ok and bay_ok
        msgs.append(
            f"bay {bx:+.0f}: pin clash {clash:.3f} mm^3, barrel {D.HINGE_BARREL_W:.2f} mm, "
            f"0.8 mm walls {walls}, bench held {bench_held}, drop clash {drop_clash:.3f} mm^3, "
            f"through-bored {through_open}"
        )
    return (
        f"HINGE_PINS {D.HINGE_PIN_COUNT}x Ø{D.HINGE_PIN_D:g} x {D.HINGE_PIN_L:g} steel pin fits "
        "knuckle & both carrier barrels (360-deg bench held & vertical drop-in)",
        ok,
        "; ".join(msgs),
    )


def check_all():
    rows = []
    tub = lower_tub.get_shape()
    car_l, car_r = front_panel_mech.front_carriers()
    carriers = front_panel_mech.front_carriers_compound()
    cov_single = front_port_cover.get_shape()
    cov = front_panel_mech.cover()
    inserts = front_panel_mech.port_inserts()
    pipe = led_light_pipe.get_shape()
    led3 = front_panel_mech.wired_led_3mm()
    mags = front_panel_mech.magnets()
    usb = radxa_x4.usb_a_cluster()
    ret_single = usb_retainer_bracket.get_shape()
    ret_both = front_panel_mech.usb_retainer_compound()

    # 1. Printability rows on front_io_carrier_l/_r, front_port_cover, insert, LED & usb_retainer
    for name, shape, mod in (
        ("front_io_carrier_l", car_l, front_io_carrier_l),
        ("front_io_carrier_r", car_r, front_io_carrier_r),
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
                support_mm2=getattr(mod, "SUPPORT_MM2", 0.0),
            )
        )

    # 2. Rule G13: zero boolean interference across all front panel parts
    pairs = [
        ("lower_tub/front_carriers", tub, carriers),
        ("front_carriers/front_port_cover", carriers, cov),
        ("front_carriers/usb_a", carriers, usb),
        ("front_carriers/usb_retainer_brackets", carriers, ret_both),
        ("front_carriers/led_light_pipe", carriers, pipe),
        ("front_carriers/magnets", carriers, mags),
        ("front_carriers/insert_p1", carriers, inserts[0]),
        ("front_carriers/insert_p2", carriers, inserts[1]),
        ("front_carriers/insert_p3", carriers, inserts[2]),
        ("front_carriers/insert_p4", carriers, inserts[3]),
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
    plate_w = cov_bb.xlen
    xz_clear_w = (D.FRONT_BAY_W - plate_w) / 2.0
    xz_clear_h = (D.FRONT_BAY_H - cov_bb.zlen) / 2.0
    hinge_rad_clear = (D.HINGE_BORE_D - D.HINGE_PIN_D) / 2.0
    usb_y_gap = usb_bb.ymin - cov_bb.ymax
    pair_span = abs(D.FRONT_PORT_XS[0] - D.FRONT_PORT_XS[1]) + D.PORT_INSERT_OD
    # The doors swing with their glued port bezels (which stand proud of the hinge axis): the
    # whole 0..90 deg arc in 5 deg steps, not a couple of poses (C1: the bezels hit the sill from
    # 13 deg while the bare doors passed at 30 and 80).
    pivot = cq.Vector(0.0, D.HINGE_Y, D.HINGE_Z)
    door_and_bezels = cq.Compound.makeCompound([*front_panel_mech.covers(), *inserts])
    swing_clash = max(
        _common_volume(tub, opened)
        + _common_volume(carriers, opened)
        + _common_volume(pipe, opened)
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
        # the locating band applies once paint has closed the gap (2 painted faces, PAINT_FIT)
        and 0.15 <= xz_clear_w - 2.0 * D.PAINT_T <= 0.30
        and 0.15 <= xz_clear_h - 2.0 * D.PAINT_T <= 0.30
        and 0.10 <= hinge_rad_clear <= 0.25
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

    rows.append(_hinge_pins_row(tub, carriers, front_panel_mech.covers(), usb))

    # 4. J-07: the light pipe sits in the tub's lens bore with a real clearance, flush with the
    # front, and the LED sits just behind it: measured on the solids (C8), not from the datums.
    dist = BRepExtrema_DistShapeShape(tub.wrapped, pipe.wrapped)
    dist.Perform()
    pipe_clear = dist.Value()
    pipe_bb = pipe.BoundingBox()
    led3_bb = led3.BoundingBox()
    led_gap = led3_bb.ymin - pipe_bb.ymax
    # the tub's front face beside the bore, found by stepping in from outside
    z_face = pipe_bb.zmax + 1.5
    to_front = probe.first_hit(tub, (0.0, pipe_bb.ymin - 3.0, z_face), (0, 1, 0), max_len=6.0)
    flush = None if to_front is None else pipe_bb.ymin - (pipe_bb.ymin - 3.0 + to_front)
    j07_ok = (
        0.05 <= pipe_clear <= 0.20
        and flush is not None
        and abs(flush) <= 0.30
        and 0.10 <= led_gap <= 0.50
        and _common_volume(tub, pipe) <= 1e-3
        and _common_volume(tub, led3) <= 1e-3
    )
    rows.append(
        (
            "J07_PIPE  light pipe in the lens bore (measured gap), flush at the front, LED behind",
            j07_ok,
            f"pipe-to-tub gap {pipe_clear:.3f} mm (0.05..0.20), pipe face "
            + (
                f"{flush:+.2f} mm from the front (±0.30)"
                if flush is not None
                else "FRONT NOT FOUND"
            )
            + f", LED {led_gap:.2f} mm behind the pipe (0.10..0.50)",
        )
    )

    # 5. J-08: Separately-printed shallow N64 port inserts seat in cover pockets (0.20 mm/side)
    ins_bb = inserts[0].BoundingBox()
    port_rad_clear = (D.PORT_POCKET_D - D.PORT_INSERT_BOSS_D) / 2.0
    total_depth = D.PORT_INSERT_BOSS_H + D.PORT_INSERT_BEZEL_H
    j08_ok = (
        len(inserts) == 4
        and 0.15 <= port_rad_clear - 2.0 * D.PAINT_T <= 0.30  # the fit once both are painted
        and abs(ins_bb.xlen - D.PORT_INSERT_OD) < 0.05
        and abs(ins_bb.ylen - total_depth) < 0.05
        and 1.5 <= ins_bb.ylen <= 2.5
        and all(_common_volume(cov, ins) <= 1e-3 for ins in inserts)
    )
    rows.append(
        (
            "J08_PORT  4x n64_port_insert (Ø10.88x2.0mm) seat in pockets (0.20mm/side painted)",
            j08_ok,
            f"radial clearance={port_rad_clear:.2f} mm/side, "
            f"insert OD={ins_bb.xlen:.2f} mm, shallow depth={ins_bb.ylen:.2f} mm",
        )
    )

    # 6. SUBASM_CLEAR: minimum 3D Euclidean clearance from front_carriers + 6x M2.5 screw heads
    #    to surrounding internal components (Radxa PCB, Radxa STEP, wired LED, cooling duct)
    ear_z_tops = (18.45, 7.30, 7.30)
    screw_heads = [
        cq.Solid.makeCylinder(
            D.BOARD_SCREW_HEAD_D / 2.0,
            D.BOARD_SCREW_HEAD_H,
            cq.Vector(side * mx, my, z_top),
        )
        for side in (-1.0, 1.0)
        for (mx, my), z_top in zip(D.FRONT_SUBASM_MOUNT_PTS, ear_z_tops)
    ]
    screw_comp = cq.Compound.makeCompound(screw_heads)
    carriers_and_screws = cq.Compound.makeCompound([*carriers.Solids(), *screw_heads])
    clear_targets = (
        ("radxa_pcb", carriers_and_screws, radxa_x4.board_solid(), 1.50),
        ("radxa_step", carriers_and_screws, radxa_x4.vendor_step_compound(), 0.75),
        ("wired_led_3mm", carriers_and_screws, led3, 1.00),
        ("duct_floor", carriers_and_screws, cooling_duct.floor_plate(), 1.00),
        ("screws_to_duct", screw_comp, cooling_duct.get_shape(), 1.50),
    )
    clear_msgs, clear_bad = [], []
    for tname, src_shape, tshape, min_mm in clear_targets:
        ext = BRepExtrema_DistShapeShape(src_shape.wrapped, tshape.wrapped)
        ext.Perform()
        gap_mm = ext.Value()
        clear_msgs.append(f"{tname}={gap_mm:.2f}mm(>={min_mm:.2f})")
        if gap_mm < min_mm - 1e-4:
            clear_bad.append(f"{tname}={gap_mm:.2f}mm<{min_mm:.2f}mm")
    rows.append(
        (
            "SUBASM_CLEAR front_carriers + 6x M2.5 screw heads clear Radxa, LED & cooling duct",
            not clear_bad,
            ", ".join(clear_msgs)
            if not clear_bad
            else "TOO CLOSE: " + ", ".join(clear_bad) + " (" + ", ".join(clear_msgs) + ")",
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
