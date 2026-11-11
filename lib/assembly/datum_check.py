"""Assembly-level gate checks for `lib/assembly/datum.py` (`REQ-01..REQ-10`).

Verifies scale proportions, coordinate frame handedness, Radxa X4 fitment inside
the lower tub, thermal stackup inside the 36.5 mm dome, rear I/O bay allocation,
front 4-port grouping (`P1/P2` left, `P3/P4` right), front black emblem bezel,
top deck controls (`AC-T18`), and the Joint Register in `notes/TOLERANCES.md`.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from assembly import datum as D  # noqa: E402
from assembly import n64_scan_profiles as S  # noqa: E402
from component import radxa_x4  # noqa: E402
from part import lower_tub  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOLERANCES_MD = os.path.join(REPO, "notes", "TOLERANCES.md")
EXPECTED_JOINTS = ("J-01", "J-02", "J-03", "J-04", "J-05", "J-06", "J-07", "J-08", "J-09")


def check_all():
    rows = []
    tub = lower_tub.get_shape()
    tub_bb = tub.BoundingBox()
    pcb_bb = radxa_x4.board_solid().BoundingBox()

    # 1. REQ-01: 50% scale envelope & lower_tub outer dimensions
    scale_ok = (
        abs(D.SHELL_W / D.N64_ORIG_W - 0.50) < 1e-6
        and abs(D.SHELL_D / D.N64_ORIG_D - 0.50) < 1e-6
        and abs(D.SHELL_H / D.N64_ORIG_H - 0.50) < 1e-6
        and abs(tub_bb.xlen - D.SHELL_W) < 0.05
        and abs(tub_bb.ylen - D.SHELL_D) < 0.05
        and abs(tub_bb.zlen - (D.SPLIT_Z + D.LIP_H)) < 0.05
    )
    rows.append(
        (
            "SCALE     50% N64 proportions (130.0 x 95.0 x 36.5 mm) matched by lower_tub",
            scale_ok,
            f"tub {tub_bb.xlen:.2f} x {tub_bb.ylen:.2f} x {tub_bb.zlen:.2f} mm "
            f"(target {D.SHELL_W:.1f} x {D.SHELL_D:.1f} x {D.SPLIT_Z + D.LIP_H:.1f} mm)",
        )
    )

    # 1b. SCAN_50: 50%-scaled OEM N64 3D scan meshes match SHELL_W x SHELL_D x SHELL_H
    top_w, top_d, _ = S.SCAN_SPANS_50_MM["Top.stl"]
    bot_w, bot_d, bot_h = S.SCAN_SPANS_50_MM["Bottom.stl"]
    max_plan_w = 2.0 * max(hw for _, hw in S.TOP_PLAN_HALF_WIDTH_50)
    max_dome_z = max(zd for _, zd, _ in S.TOP_ELEVATION_PROFILE_50)
    scan_ok = (
        abs(top_w - D.SHELL_W) < 0.25
        and abs(top_d - D.SHELL_D) < 0.25
        and abs(bot_w - D.SHELL_W) < 0.25
        and abs(bot_d - D.SHELL_D) < 0.25
        and abs(bot_h - D.SPLIT_Z) < 0.60
        and abs(max_plan_w - D.SHELL_W) < 0.25
        and abs(max_dome_z - D.SHELL_H) < 0.05
    )
    rows.append(
        (
            "SCAN_50   OEM N64 3D scans at 50% scale match 130.0 x 95.0 x 36.5 mm envelope",
            scan_ok,
            f"Top.stl={top_w:.2f}x{top_d:.2f} mm, "
            f"Bottom.stl={bot_w:.2f}x{bot_d:.2f}x{bot_h:.2f} mm, "
            f"dome Z={max_dome_z:.2f} mm",
        )
    )

    # 2. REQ-02: Right-handed tabletop coordinate frame (det == +1)
    det = D.determinant_3x3(D.FRAME_BASIS)
    rows.append(
        (
            "HANDED    coordinate frame basis has determinant +1.0 (no reflection)",
            abs(det - 1.0) < 1e-9,
            f"det(FRAME_BASIS) = {det:+.6f}",
        )
    )

    # 3. REQ-03: Radxa X4 board clears -X/+X/-Y walls by >= 2.0 mm & sits flush with +Y rear wall
    inner_xmin = -D.WAIST_HALF_W + D.SHELL_WALL_T
    inner_xmax = D.WAIST_HALF_W - D.SHELL_WALL_T
    inner_ymin = D.FRONT_APRON_Y0 + D.SHELL_WALL_T
    inner_ymax = D.REAR_WALL_Y1 - D.SHELL_WALL_T

    gaps = {
        "-X": pcb_bb.xmin - inner_xmin,
        "+X": inner_xmax - pcb_bb.xmax,
        "-Y": pcb_bb.ymin - inner_ymin,
        "+Y": inner_ymax - pcb_bb.ymax,
    }
    min_side_gap = min(gaps["-X"], gaps["+X"], gaps["-Y"])
    rear_flush = 0.10 <= gaps["+Y"] <= 1.25
    rows.append(
        (
            "RADXA_FIT Radxa X4 (85x56 mm) flush with +Y rear wall & clears sides >= 2.0 mm",
            min_side_gap >= 2.0 and rear_flush and D.SHELL_WALL_T >= 1.5,
            f"rear +Y gap {gaps['+Y']:.2f} mm, min side gap {min_side_gap:.2f} mm "
            f"(-X:{gaps['-X']:.1f}, +X:{gaps['+X']:.1f}, "
            f"-Y:{gaps['-Y']:.1f}, +Y:{gaps['+Y']:.2f}), "
            f"wall={D.SHELL_WALL_T:.1f} mm",
        )
    )

    # 4. REQ-04 (cooling) is measured in subassembly/cooling_check.py.

    # 5. REQ-05: Rear-right RJ45 bay beside shifted Radxa X4
    rj45_bay_avail = inner_xmax - pcb_bb.xmax
    rj45_bb = radxa_x4.rj45_jack().BoundingBox()
    rj45_gap_to_pcb = rj45_bb.xmin - pcb_bb.xmax
    rows.append(
        (
            "REAR_IO   shifted Radxa X4 opens >= 24.0 mm rear-right bay for RJ45 jack",
            rj45_bay_avail >= D.REAR_RJ45_BAY_W and rj45_gap_to_pcb >= 1.0,
            f"rear-right bay width={rj45_bay_avail:.1f} mm (min {D.REAR_RJ45_BAY_W:.1f} mm), "
            f"RJ45-to-PCB gap={rj45_gap_to_pcb:.1f} mm",
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
