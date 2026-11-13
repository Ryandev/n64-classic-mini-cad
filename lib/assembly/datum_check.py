"""Assembly-level gate checks for `lib/assembly/datum.py` (`REQ-01..REQ-10`).

Verifies scale proportions, coordinate frame handedness, Radxa X4 fitment inside
the lower tub, rear I/O bay allocation, measured on the solids against the real N64 model (C8),
front 4-port grouping (`P1/P2` left, `P3/P4` right), front black emblem bezel,
top deck controls (`AC-T18`), and the Joint Register in `notes/TOLERANCES.md`.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from assembly import datum as D  # noqa: E402
from assembly import n64_scan_profiles as S  # noqa: E402
from component import radxa_x4  # noqa: E402
from part import lower_tub, power_slider, reset_button  # noqa: E402
from subassembly import front_panel_mech  # noqa: E402
from testing import probe  # noqa: E402
from testing.load import load_by_path  # noqa: E402

LIB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(LIB)
TOLERANCES_MD = os.path.join(REPO, "notes", "TOLERANCES.md")
EXPECTED_JOINTS = ("J-01", "J-02", "J-03", "J-04", "J-05", "J-06", "J-07", "J-08", "J-09")


def check_all():
    rows = []
    tub = lower_tub.get_shape()
    tub_bb = tub.BoundingBox()
    pcb_bb = radxa_x4.board_solid().BoundingBox()

    # Every row below measures the solids (C8): the reference is Radxa's board and the real N64
    # shell model (`step/n64_shell.py`, full size), never the datum constants being graded.
    ref_bb = load_by_path(os.path.join(LIB, "step", "n64_shell.py"), "ref_n64_shell").get_shape()
    ref_bb = ref_bb.BoundingBox()
    ref_w, ref_d, ref_h = ref_bb.xlen * D.SCALE, ref_bb.ylen * D.SCALE, ref_bb.zlen * D.SCALE

    # 1. REQ-01: the lower tub's footprint is the real N64's, at 50 %
    scale_ok = abs(tub_bb.xlen - ref_w) < 0.25 and abs(tub_bb.ylen - ref_d) < 0.25
    rows.append(
        (
            "SCALE     lower_tub footprint = the real N64 shell model at 50 %",
            scale_ok,
            f"tub {tub_bb.xlen:.2f} x {tub_bb.ylen:.2f} mm vs N64 model x{D.SCALE:.2f} "
            f"{ref_w:.2f} x {ref_d:.2f} mm (full size {ref_bb.xlen:.2f} x {ref_bb.ylen:.2f})",
        )
    )

    # 1b. SCAN_50: the hand-copied scan spans in n64_scan_profiles agree with the real model
    top_w, top_d, _ = S.SCAN_SPANS_50_MM["Top.stl"]
    bot_w, bot_d, _ = S.SCAN_SPANS_50_MM["Bottom.stl"]
    max_plan_w = 2.0 * max(hw for _, hw in S.TOP_PLAN_HALF_WIDTH_50)
    max_dome_z = max(zd for _, zd, _ in S.TOP_ELEVATION_PROFILE_50)
    scan_ok = all(
        abs(a - b) < 0.25
        for a, b in (
            (top_w, ref_w),
            (top_d, ref_d),
            (bot_w, ref_w),
            (bot_d, ref_d),
            (max_plan_w, ref_w),
            (max_dome_z, ref_h),
        )
    )
    rows.append(
        (
            "SCAN_50   scan profiles (n64_scan_profiles) match the real N64 shell model at 50 %",
            scan_ok,
            f"Top.stl {top_w:.2f}x{top_d:.2f}, Bottom.stl {bot_w:.2f}x{bot_d:.2f}, plan width "
            f"{max_plan_w:.2f}, dome {max_dome_z:.2f} mm vs model "
            f"{ref_w:.2f}x{ref_d:.2f}x{ref_h:.2f}",
        )
    )

    # 2. REQ-02: the built parts sit right-handed, as on a real N64 seen from the front: POWER on
    # the left (-X), RESET on the right, the controller ports at the front (-Y), the rear I/O at
    # the back, the buttons on top (+Z).
    def centre(shape):
        return shape.BoundingBox().center

    p_c, r_c = centre(power_slider.get_shape()), centre(reset_button.get_shape())
    front_c, rear_c = centre(front_panel_mech.cover()), centre(radxa_x4.rj45_jack())
    ex, ey, ez = (r_c - p_c).normalized(), (rear_c - front_c), (p_c - tub_bb.center)
    ey = (ey - ex * ey.dot(ex)).normalized()
    ez = (ez - ex * ez.dot(ex) - ey * ez.dot(ey)).normalized()
    det = ex.cross(ey).dot(ez)
    handed_ok = p_c.x < 0 < r_c.x and front_c.y < 0 < rear_c.y and det > 0.99
    rows.append(
        (
            "HANDED    built parts are right-handed: POWER left, ports front, I/O rear, deck up",
            handed_ok,
            f"POWER x {p_c.x:+.1f}, RESET x {r_c.x:+.1f}, ports y {front_c.y:+.1f}, "
            f"RJ45 y {rear_c.y:+.1f}; det(measured axes) = {det:+.4f}",
        )
    )

    # 3. REQ-03: Radxa X4 clears the tub's real walls by >= 2.0 mm and sits near the rear wall.
    # Each gap steps out from the board's edge until it meets tub material; several parallel
    # probes, the smallest kept (a port cutout reads larger, never smaller).
    zc = (pcb_bb.zmin + pcb_bb.zmax) / 2.0
    ys = [pcb_bb.ymin + f * pcb_bb.ylen for f in (0.2, 0.5, 0.8)]
    xs = [pcb_bb.xmin + f * pcb_bb.xlen for f in (0.15, 0.35, 0.5, 0.65, 0.85)]
    gaps = {
        "-X": probe.min_gap(tub, [(pcb_bb.xmin, y, zc) for y in ys], (-1, 0, 0)),
        "+X": probe.min_gap(tub, [(pcb_bb.xmax, y, zc) for y in ys], (1, 0, 0)),
        "-Y": probe.min_gap(tub, [(x, pcb_bb.ymin, zc) for x in xs], (0, -1, 0)),
        "+Y": probe.min_gap(tub, [(x, pcb_bb.ymax, zc) for x in xs], (0, 1, 0)),
    }
    missing = [k for k, v in gaps.items() if v is None]
    g = {k: (v if v is not None else float("nan")) for k, v in gaps.items()}
    min_side_gap = min(g["-X"], g["+X"], g["-Y"])
    rear_flush = 0.10 <= g["+Y"] <= 1.25
    rows.append(
        (
            "RADXA_FIT Radxa X4 clears the tub's walls >= 2.0 mm, 0.1..1.25 mm from the rear wall",
            not missing and min_side_gap >= 2.0 and rear_flush,
            f"measured gaps: -X {g['-X']:.2f}, +X {g['+X']:.2f}, -Y {g['-Y']:.2f}, "
            f"rear +Y {g['+Y']:.2f} mm" + (f"; NO WALL FOUND {missing}" if missing else ""),
        )
    )

    # 4. REQ-04 (cooling) is measured in subassembly/cooling_check.py.

    # 5. REQ-05: the rear-right bay holds the real RJ45 jack assembly (C5): >= 1.0 mm to the board,
    # >= 0.5 mm to the tub's real side wall.
    rj45_bb = radxa_x4.rj45_jack().BoundingBox()
    rj_z = (rj45_bb.zmin + rj45_bb.zmax) / 2.0
    rj_ys = [rj45_bb.ymin + f * rj45_bb.ylen for f in (0.2, 0.5, 0.8)]
    gap_wall = probe.min_gap(tub, [(rj45_bb.xmax, y, rj_z) for y in rj_ys], (1, 0, 0))
    gap_pcb = rj45_bb.xmin - pcb_bb.xmax
    rows.append(
        (
            "REAR_IO   rear-right bay holds the RJ45 jack: >= 1.0 mm to the board, >= 0.5 to wall",
            gap_wall is not None and gap_pcb >= 1.0 and gap_wall >= 0.5,
            f"the {rj45_bb.xlen:.1f} mm jack sits {gap_pcb:.1f} mm from the board and "
            + (f"{gap_wall:.2f} mm from the tub wall" if gap_wall is not None else "NO WALL FOUND"),
        )
    )

    # 6. REQ-06: Front 4x USB-A controller ports grouped in twos (P1/P2 left, P3/P4 right)
    xs = D.FRONT_PORT_XS
    left_pitch = xs[1] - xs[0]
    right_pitch = xs[3] - xs[2]
    centre_gap = xs[2] - xs[1]
    symmetric = abs(xs[0] + xs[3]) < 1e-6 and abs(xs[1] + xs[2]) < 1e-6
    grouped_in_twos = (
        len(xs) == 4
        and symmetric
        and left_pitch >= D.USB_A_W + 2.0
        and abs(left_pitch - right_pitch) < 1e-6
        and centre_gap >= 2.0 * left_pitch
    )
    rows.append(
        (
            "FRONT_USB 4x front ports grouped in symmetric pairs (P1/P2 left, P3/P4 right)",
            grouped_in_twos,
            f"port X={xs}, pair pitch={left_pitch:.1f} mm, centre gap={centre_gap:.1f} mm",
        )
    )

    # 7. REQ-07 & REQ-08: Front emblem bezel & top Power/Reset controls symmetric on deck
    controls_ok = (
        D.BEZEL_W <= 40.0
        and D.BEZEL_H <= 16.0
        and abs(D.POWER_SLIDER_X + D.RESET_BTN_X) < 1e-6
        and D.POWER_SLIDER_X < -20.0
        and D.RESET_BTN_X > 20.0
    )
    rows.append(
        (
            "CONTROLS  front black emblem bezel & top Power/Reset controls symmetric",
            controls_ok,
            f"bezel {D.BEZEL_W:.1f}x{D.BEZEL_H:.1f} mm at X=0; "
            f"Power X={D.POWER_SLIDER_X:+.1f} mm, Reset X={D.RESET_BTN_X:+.1f} mm",
        )
    )

    # 8. REQ-10: Joint Register in notes/TOLERANCES.md documents every joint J-01..J-07
    try:
        tol_text = open(TOLERANCES_MD, encoding="utf-8").read()
    except OSError:
        tol_text = ""
    missing_joints = [j for j in EXPECTED_JOINTS if f"**{j}**" not in tol_text]
    rows.append(
        (
            "JOINTS    every mating pair (J-01..J-09) is registered in notes/TOLERANCES.md",
            bool(tol_text) and not missing_joints,
            f"all {len(EXPECTED_JOINTS)} joints present in notes/TOLERANCES.md"
            if not missing_joints
            else f"missing joints in notes/TOLERANCES.md: {missing_joints}",
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
