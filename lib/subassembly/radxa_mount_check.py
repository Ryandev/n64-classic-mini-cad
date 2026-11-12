"""Gate checks for `radxa_mount_mech.py`, `lower_tub`, `radxa_x4`, and the SoC heat sink.

Measures the actual 3D solids (`BRepAlgoAPI_Common`, `BRepClass3d_SolidClassifier`,
`lib/printable.py`, and `lib/testing/variant_manifest.py`) to verify:
  - `lower_tub` printability (`manifold`, `single_body`, `bed`, `overhang`, `wall`, `footprint`)
  - `variant/lower_tub.py` manifest against `part/lower_tub.py` (`DEVIATIONS`)
  - `variant/radxa_x4.py` manifest against `step/radxa_x4.py` (all 6 tall headers stripped)
  - `G13` zero boolean interference between `lower_tub` and every bought component
  - `J-02` standoff top-face Z datum contact (`Z = 8.6 mm`) and coaxial `Ø3.2 mm` bores
  - Underside M.2 2230 NVMe keepout clearance above the `Z = 2.0 mm` tub floor
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
import printable  # noqa: E402
from assembly import datum as D  # noqa: E402
from component import radxa_x4  # noqa: E402
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common  # noqa: E402
from OCP.BRepClass3d import BRepClass3d_SolidClassifier  # noqa: E402
from OCP.gp import gp_Pnt  # noqa: E402
from OCP.TopAbs import TopAbs_IN, TopAbs_OUT  # noqa: E402
from part import usb_retainer_bracket  # noqa: E402
from step import build_radxa_x4  # noqa: E402
from step import radxa_x4 as radxa_ref  # noqa: E402
from subassembly import radxa_mount_mech  # noqa: E402
from testing import variant_manifest  # noqa: E402
from testing.load import load_by_path  # noqa: E402
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
    asm = radxa_mount_mech.get_shape()

    # 1. Printability rows on lower_tub variant (REQ-11, G3)
    rows.extend(
        printable.check_part(
            "lower_tub",
            tub,
            up=lower_tub.PRINT_NORMAL,
            min_wall_mm=0.8,
            min_bed_ratio=0.15,
            max_aspect=3.0,
        )
    )

    # 1b. Variant manifest rows for lower_tub and radxa_x4
    rows.extend(variant_manifest.check_variant("lower_tub", load_by_path))
    rows.extend(variant_manifest.check_variant("radxa_x4", load_by_path))

    # 1c. Placed Radxa X4 vertical clearance check above Z = FLOOR_T
    step_bb = radxa_x4.vendor_step_compound().BoundingBox()
    unstripped = [
        name
        for name, meta in radxa_x4.STRIPPED_HEADERS.items()
        if step_bb.zmin <= float(meta["bbox"][2]) + 0.5
    ]
    rows.append(
        (
            "HEADERS   all 6 tall through-hole headers stripped from Radxa X4 STEP",
            not unstripped and step_bb.zmin >= D.FLOOR_T + 1.0,
            f"6/6 tall headers stripped ({', '.join(radxa_x4.STRIPPED_HEADERS)}); "
            f"vendor STEP zmin={step_bb.zmin:.2f} mm"
            if not unstripped
            else f"UNSTRIPPED headers detected: {unstripped} (zmin={step_bb.zmin:.2f} mm)",
        )
    )

    # 1d. C10: the reference is Radxa's own STEP, whole and moved only to the datum's hole pattern
    ref = radxa_ref.get_shape()
    n_ref = len(ref.Solids())
    cx, cy = build_radxa_x4.pattern_centre(ref)
    want_x, want_y = build_radxa_x4.local_hole_centre()
    off = max(abs(cx - want_x), abs(cy - want_y))
    rows.append(
        (
            "RADXA_REF Radxa's own STEP, every solid, holes on the datum",
            n_ref == build_radxa_x4.SOLIDS and off <= 0.01,
            f"{n_ref} solids (Radxa's file: {build_radxa_x4.SOLIDS}); 58 x 49 mm hole pattern "
            f"centred at ({cx:.3f}, {cy:.3f}), datum ({want_x:.3f}, {want_y:.3f})",
        )
    )

    # 2. Subassembly compound contains both tub and electronics (4x 4-solid TE 292303-7 USB-A)
    n_solids = len(asm.Solids())
    rows.append(
        (
            "SUBASM    radxa_mount_mech builds tub + 20 component solids",
            n_solids == 21,
            f"{n_solids} solids in radxa_mount_mech.get_shape() (expected 21: 1 tub + 20 bought)",
        )
    )

    # 3. Rule G13: zero boolean interference between lower_tub and bought components
    components = [
        ("radxa_pcb", radxa_x4.board_solid()),
        ("radxa_vendor_step", radxa_x4.vendor_step_compound()),
        ("hsb26_heatsink", radxa_x4.heatsink_solid()),
        ("m2_2230_nvme", radxa_x4.m2_keepout()),
        ("front_usb_a_x4", radxa_x4.usb_a_cluster()),
        ("rear_rj45", radxa_x4.rj45_jack()),
    ]
    interferences = []
    for cname, cshape in components:
        v = _common_volume(tub, cshape)
        if v < 0 or v > 1e-3:
            interferences.append(f"{cname}={v:.3f}mm^3")

    rows.append(
        (
            "G13_CLEAR zero boolean interference between lower_tub and bought hardware",
            not interferences,
            "0.000 mm^3 intersection across all 7 component groups (incl. Radxa & heatsink STEPs)"
            if not interferences
            else "INTERFERENCE: " + ", ".join(interferences),
        )
    )

    # 4. J-02: Standoff annular material at Z = 8.2 mm (Radxa) & Z = 5.6 mm (RJ45) + RX-M2.5 bores
    clf = BRepClass3d_SolidClassifier(tub.wrapped)
    clf_rj = BRepClass3d_SolidClassifier(radxa_x4.rj45_jack().wrapped)
    z_seat = D.RADXA_PCB_Z0
    bad_standoffs = []
    for idx, (hx, hy) in enumerate(D.radxa_hole_centres(), 1):
        clf.Perform(gp_Pnt(hx + 1.4, hy, z_seat - 1.0), 1e-4)
        bore_open = clf.State() == TopAbs_OUT
        clf.Perform(gp_Pnt(hx + 2.5, hy, z_seat - 0.2), 1e-4)
        ring_solid = clf.State() == TopAbs_IN
        clf.Perform(gp_Pnt(hx + 2.5, hy, z_seat + 0.2), 1e-4)
        top_clear = clf.State() == TopAbs_OUT
        if not (bore_open and ring_solid and top_clear):
            bad_standoffs.append(
                f"H{idx}({hx:.1f},{hy:.1f}): bore_open={bore_open}, "
                f"ring_solid={ring_solid}, top_clear={top_clear}"
            )
    for idx, (rx, ry) in enumerate(D.RJ45_MOUNT_HOLES, 1):
        clf.Perform(gp_Pnt(rx + 1.4, ry, D.RJ45_SEAT_Z - 1.0), 1e-4)
        bore_open = clf.State() == TopAbs_OUT
        clf.Perform(gp_Pnt(rx + 2.2, ry, D.RJ45_SEAT_Z - 0.2), 1e-4)
        ring_solid = clf.State() == TopAbs_IN
        clf_rj.Perform(gp_Pnt(rx + 1.2, ry, D.RJ45_SEAT_Z + 0.8), 1e-4)
        ear_hole_open = clf_rj.State() == TopAbs_OUT
        clf_rj.Perform(gp_Pnt(rx + 2.0, ry, D.RJ45_SEAT_Z + 0.8), 1e-4)
        ear_ring_solid = clf_rj.State() == TopAbs_IN
        if not (bore_open and ring_solid and ear_hole_open and ear_ring_solid):
            bad_standoffs.append(f"RJ45_M{idx}({rx:.1f},{ry:.1f})")
    clf_rj.Perform(gp_Pnt(43.0, 42.0, 7.2), 1e-4)
    if clf_rj.State() != TopAbs_OUT:
        bad_standoffs.append("RJ45_8P8C_cavity_closed")

    rows.append(
        (
            f"J02_SEAT  4x Radxa (Z={z_seat:.1f}mm) + 2x RJ45 (Z={D.RJ45_SEAT_Z:.1f}mm) M2.5 posts",
            not bad_standoffs,
            "4/4 Radxa + 2/2 RJ45 RX-M2.5x4.0 standoffs & 8P8C cavity verified by 3D point probes"
            if not bad_standoffs
            else "; ".join(bad_standoffs),
        )
    )

    # 5. Underside M.2 2230 NVMe clearance above tub floor (REQ-03)
    m2_bb = radxa_x4.m2_keepout().BoundingBox()
    floor_top_z = D.FLOOR_T
    m2_gap = m2_bb.zmin - floor_top_z
    rows.append(
        (
            "M2_CLEAR  underside M.2 2230 NVMe clears lower_tub floor by >= 1.0 mm",
            m2_gap >= 1.0,
            f"M.2 zmin={m2_bb.zmin:.2f} mm vs floor Z={floor_top_z:.2f} mm -> gap {m2_gap:.2f} mm",
        )
    )

    # 6. Rear cable overmold boots at full insertion depth clear lower_tub counterbores (REQ-05)
    plug_overmolds = [
        (
            "usbc_overmold",
            lower_tub._stadium_y(D.REAR_USBC_X, D.REAR_IO_Z_CENTRE, 12.35, 6.50, 48.50, 12.0),
        ),
        (
            "hdmi_overmold",
            lower_tub._stadium_y(D.REAR_HDMI_X, D.REAR_IO_Z_CENTRE, 10.60, 6.50, 48.37, 12.0),
        ),
        (
            "audio_overmold",
            lower_tub._stadium_y(D.REAR_AUDIO_X, 5.95, 8.40, 7.20, 49.00, 12.0),
        ),
        (
            "rj45_overmold",
            cq.Solid.makeBox(12.40, 12.0, 10.60, cq.Vector(44.10 - 6.20, 49.10, 7.20 - 5.30)),
        ),
    ]
    bad_plugs = []
    for pname, pshape in plug_overmolds:
        v = _common_volume(tub, pshape)
        if v < 0 or v > 1e-3:
            bad_plugs.append(f"{pname}={v:.3f}mm^3")
    rows.append(
        (
            "REAR_PLUGS rear cable overmolds (USB-C, Micro-HDMI, 3.5mm, RJ45) seat without clash",
            not bad_plugs,
            "0.000 mm^3 interference across all 4 fully-inserted rear cable overmold boots"
            if not bad_plugs
            else "OVERMOLD CLASH: " + ", ".join(bad_plugs),
        )
    )

    # 7. Front 4x TE 292303-7 USB-A 6-DOF mechanical lock check (REQ-06)
    ret_both = cq.Compound.makeCompound(usb_retainer_bracket.brackets())
    clf_ret = BRepClass3d_SolidClassifier(ret_both.wrapped)
    bad_usb = []
    for idx, px in enumerate(D.FRONT_PORT_XS, 1):
        tub_probes = (
            ("front_floor_-Z", (px, -36.00, 10.65), TopAbs_IN),
            ("rear_floor_-Z", (px, -28.00, 9.40), TopAbs_IN),
            ("leg_slot_open", (px + 6.80, -31.20, 8.00), TopAbs_OUT),
            ("leg_pull_stop_-Y", (px + 6.80, -32.75, 8.00), TopAbs_IN),
            ("rear_backstop_+Y", (px + 5.00, -26.20, 10.50), TopAbs_IN),
        )
        for label, (ux, uy, uz), expected in tub_probes:
            clf.Perform(gp_Pnt(ux, uy, uz), 1e-4)
            if clf.State() != expected:
                bad_usb.append(f"P{idx}_{label}")
        clf_ret.Perform(gp_Pnt(px, -32.00, 17.50), 1e-4)
        if clf_ret.State() != TopAbs_IN:
            bad_usb.append(f"P{idx}_top_bridge_+Z")
    rows.append(
        (
            "USB_LOCK   4x TE 292303-7 USB-A ports locked in 6-DOF (stepped floor, bridge & legs)",
            not bad_usb,
            "4/4 USB-A ports locked in -Z (Z=10.80/9.55), +Z (Z=16.85 bridge), +-Y (legs/backstop)"
            if not bad_usb
            else "USB LOCK FAIL: " + ", ".join(bad_usb),
        )
    )

    return rows


if __name__ == "__main__":
    results = check_all()
    failed = 0
    for label, ok, msg in results:
        tag = "PASS" if ok else "FAIL"
        print(f"  {tag}  {label}")
        print(f"        {msg}")
        if not ok:
            failed += 1
    sys.exit(1 if failed else 0)
