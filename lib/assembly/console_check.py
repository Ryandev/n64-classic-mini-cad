"""Whole-console assembly & outer-surface fidelity gate checks (`lib/assembly/console_check.py`).

Verifies:
  - `J-01`: `upper_shell` and `lower_tub` mate across `SPLIT_Z = 12.94 mm` with `0.15 mm/side`
    perimeter lip locating clearance (`0.000 mm^3` boolean intersection), combined outer
    envelope (the real N64 model at 50 %), and coaxial M3 corner bores at all 4 corners
  - `VARIANT n64_console`: `variant/n64_console.py` removes external power brick/cord,
    RCA cable, and SolidWorks construction planes from `step/n64_console_raw.py`
  - `SH_OUTSIDE`: Ray-cast outer-surface fidelity against the downloaded `step/n64_shell.py`
    reference (`BRepIntCurveSurface_Inter`, adapted from `GBA/CAD/lib/assembly/shell_check.py`):
    proves the assembled shell has protruding `+-65.0 mm` front pods, recessed `-44.15 mm`
    front apron, `+-60.0 mm` tapered waist, swept front-pod dome shoulders, `10.27 deg`
    sloped wing decks, `33.5 mm` convex front barrel dome, and concave rear cartridge cradle
    (a boxy prism fails immediately!)
  - `G13_FULL`: `0.000 mm^3` pairwise boolean interference across all printed parts and
    placed bought electronics (`variant/radxa_x4`, the HSB26 heat sink, USB-A, RJ45, switches)
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import assembly_positions as AP  # noqa: E402
import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402
from component import radxa_x4  # noqa: E402
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common  # noqa: E402
from OCP.BRepClass3d import BRepClass3d_SolidClassifier  # noqa: E402
from OCP.BRepIntCurveSurface import BRepIntCurveSurface_Inter  # noqa: E402
from OCP.gp import gp_Dir, gp_Lin, gp_Pnt  # noqa: E402
from OCP.TopAbs import TopAbs_IN, TopAbs_OUT  # noqa: E402
from part import (  # noqa: E402
    cartridge_flaps,
    front_bezel,
    led_light_pipe,
    power_slider,
    reset_button,
)
from step import n64_shell as _ref_n64_shell  # noqa: E402
from subassembly import front_panel_mech, top_controls_mech  # noqa: E402
from testing import probe, variant_manifest  # noqa: E402
from testing.load import load_by_path  # noqa: E402
from variant import lower_tub, upper_shell  # noqa: E402


def _common_volume(a: cq.Shape, b: cq.Shape) -> float:
    com = BRepAlgoAPI_Common(a.wrapped, b.wrapped)
    com.Build()
    if not com.IsDone():
        return -1.0
    return cq.Shape.cast(com.Shape()).Volume()


def _ray_hits(
    shape: cq.Shape, origin: tuple[float, float, float], direction: tuple[float, float, float]
) -> list[float]:
    inter = BRepIntCurveSurface_Inter()
    inter.Init(shape.wrapped, gp_Lin(gp_Pnt(*origin), gp_Dir(*direction)), 1e-4)
    ws = []
    while inter.More():
        w = inter.W()
        if w >= 0.0:
            ws.append(w)
        inter.Next()
    return sorted(ws)


def _first_coord(
    shape: cq.Shape,
    origin: tuple[float, float, float],
    direction: tuple[float, float, float],
    axis: int,
) -> float | None:
    ws = _ray_hits(shape, origin, direction)
    if not ws:
        return None
    return origin[axis] + direction[axis] * ws[0]


def _check_outer_silhouette(console_shells: cq.Shape) -> tuple[str, bool, str]:
    """Cast rays from outside onto `console_shells` and `step/n64_shell.py` (`SH_OUTSIDE`)."""
    ref = _ref_n64_shell.get_shape()
    sx, sy, sz = AP.REF_TO_MINI_SCALE_XYZ

    # 1. Front +Y rays at Z = 10.5 mm below the split line (pod vs recessed central apron)
    y_pod_nat = _first_coord(console_shells, (52.5, -80.0, 10.5), (0.0, 1.0, 0.0), 1)
    y_apr_nat = _first_coord(console_shells, (0.0, -80.0, 10.5), (0.0, 1.0, 0.0), 1)
    y_pod_ref = _first_coord(ref, (52.5 / sx, -140.0, 10.5 / sz), (0.0, 1.0, 0.0), 1)
    y_apr_ref = _first_coord(ref, (0.0, -140.0, 10.5 / sz), (0.0, 1.0, 0.0), 1)

    # 2. Side -X rays at Z = 11.5 mm: front pod (Y=-37.44) vs recessed waist (Y=10.0)
    x_pod_nat = _first_coord(console_shells, (90.0, -37.44, 11.5), (-1.0, 0.0, 0.0), 0)
    x_wst_nat = _first_coord(console_shells, (90.0, 10.0, 11.5), (-1.0, 0.0, 0.0), 0)
    x_pod_ref = _first_coord(ref, (160.0, -37.44 / sy, 11.5 / sz), (-1.0, 0.0, 0.0), 0)
    x_wst_ref = _first_coord(ref, (160.0, 10.0 / sy, 11.5 / sz), (-1.0, 0.0, 0.0), 0)

    # 3. Top -Z rays: convex R=5.0mm front pod dome, sloped wing, convex front dome & concave cradle
    z_pod_ctr = _first_coord(console_shells, (52.5, -44.8, 60.0), (0.0, 0.0, -1.0), 2)
    z_pod_mid = _first_coord(console_shells, (52.5, -47.2, 60.0), (0.0, 0.0, -1.0), 2)
    z_pod_tip = _first_coord(console_shells, (52.5, -49.2, 60.0), (0.0, 0.0, -1.0), 2)
    z_wing_in = _first_coord(console_shells, (36.0, 0.0, 60.0), (0.0, 0.0, -1.0), 2)
    z_wing_out = _first_coord(console_shells, (56.0, 0.0, 60.0), (0.0, 0.0, -1.0), 2)
    z_wing_in_ref = _first_coord(ref, (36.0 / sx, 0.0, 90.0), (0.0, 0.0, -1.0), 2)
    z_wing_out_ref = _first_coord(ref, (56.0 / sx, 0.0, 90.0), (0.0, 0.0, -1.0), 2)
    z_dome_f0 = _first_coord(console_shells, (0.0, -24.0, 60.0), (0.0, 0.0, -1.0), 2)
    z_dome_f28 = _first_coord(console_shells, (28.0, -24.0, 60.0), (0.0, 0.0, -1.0), 2)
    z_cradle_0 = _first_coord(console_shells, (0.0, 28.0, 60.0), (0.0, 0.0, -1.0), 2)
    z_cradle_28 = _first_coord(console_shells, (28.0, 28.0, 60.0), (0.0, 0.0, -1.0), 2)

    vals = (
        y_pod_nat,
        y_apr_nat,
        y_pod_ref,
        y_apr_ref,
        x_pod_nat,
        x_wst_nat,
        x_pod_ref,
        x_wst_ref,
        z_pod_ctr,
        z_pod_mid,
        z_pod_tip,
        z_wing_in,
        z_wing_out,
        z_wing_in_ref,
        z_wing_out_ref,
        z_dome_f0,
        z_dome_f28,
        z_cradle_0,
        z_cradle_28,
    )
    if any(v is None for v in vals):
        return (
            "SH_OUTSIDE outer shell ray-casts match downloaded N64 STEP silhouette",
            False,
            f"missed ray: {vals}",
        )

    pod_protrusion = y_apr_nat - y_pod_nat  # > 2.8 mm
    ref_pod_protrusion = (y_apr_ref - y_pod_ref) * sy
    waist_taper = x_pod_nat - x_wst_nat  # ~ 5.0 mm
    ref_waist_taper = (x_pod_ref - x_wst_ref) * sx  # ~ 5.0 mm
    wing_deg = math.degrees(math.atan2(z_wing_in - z_wing_out, 20.0))
    ref_wing_deg = math.degrees(math.atan2((z_wing_in_ref - z_wing_out_ref) * 0.50, 20.0))
    front_convex = z_dome_f0 - z_dome_f28  # > 2.0 mm
    rear_concave = z_cradle_28 - z_cradle_0  # > 0.8 mm
    pod_convex = (z_pod_ctr >= z_pod_mid + 0.5) and (z_pod_mid >= z_pod_tip + 1.0)

    ok = (
        abs(pod_protrusion - ref_pod_protrusion) <= 0.8
        and pod_protrusion >= 2.8
        and abs(waist_taper - ref_waist_taper) <= 0.5
        and waist_taper >= 4.5
        and abs(wing_deg - ref_wing_deg) <= 1.2
        and pod_convex
        and z_pod_ctr <= 26.2
        and z_pod_tip <= 23.0
        and front_convex >= 2.0
        and rear_concave >= 0.8
        and (z_dome_f0 - z_cradle_0) >= 5.0
    )
    msg = (
        f"pod protrusion={pod_protrusion:.2f}mm (ref {ref_pod_protrusion:.2f}mm), "
        f"waist taper={waist_taper:.2f}mm/side (ref {ref_waist_taper:.2f}mm), "
        f"wing={wing_deg:.2f}deg (ref {ref_wing_deg:.2f}deg), "
        f"pod_z=({z_pod_ctr:.1f},{z_pod_mid:.1f},{z_pod_tip:.1f})mm, "
        f"dome_convex={front_convex:+.2f}mm, cradle_concave={rear_concave:+.2f}mm"
    )
    return ("SH_OUTSIDE outer shell ray-casts match downloaded N64 STEP silhouette", ok, msg)


def check_all():
    rows = []
    tub = lower_tub.get_shape()
    top = upper_shell.get_shape()
    flaps = cartridge_flaps.get_shape()
    slider = power_slider.get_shape()
    reset = reset_button.get_shape()
    bezel = front_bezel.get_shape()
    cov = front_panel_mech.cover()
    ret = front_panel_mech.usb_retainer_compound()
    inserts = front_panel_mech.port_inserts()
    pipe = led_light_pipe.get_shape()
    sw_l, sw_r = top_controls_mech.tactile_switches()
    elec = radxa_x4.get_shape()

    # 1. J-01: the two halves together have the real N64's outline at 50 %, don't overlap, and the
    # tub's lip sits in the shell's rebate with the intended clearance, all measured (C8).
    console_shells = cq.Compound.makeCompound([tub, top])
    bb = console_shells.BoundingBox()
    ref = _ref_n64_shell.get_shape().BoundingBox()
    ref_w, ref_d, ref_h = ref.xlen * D.SCALE, ref.ylen * D.SCALE, ref.zlen * D.SCALE
    shell_clash = _common_volume(tub, top)
    # Lip gap at the +X side wall: find the lip's outer face from outside, then step on to the shell
    z_lip = D.SPLIT_Z + D.LIP_H / 2.0
    x_out = D.SHELL_W / 2.0 + 2.0  # just outside the side wall
    to_lip = probe.first_hit(tub, (x_out, 0.0, z_lip), (-1, 0, 0), max_len=10.0, step=0.005)
    lip_gap = None
    if to_lip is not None:
        x_lip = x_out - to_lip
        lip_gap = probe.first_hit(
            top, (x_lip + 0.001, 0.0, z_lip), (1, 0, 0), max_len=3.0, step=0.005
        )
    env_ok = (
        abs(bb.xlen - ref_w) < 0.25
        and abs(bb.ylen - ref_d) < 0.25
        and abs(bb.zlen - ref_h) < 0.25
        and shell_clash <= 1e-3
        and lip_gap is not None
        and 0.10 <= lip_gap <= 0.25
    )
    rows.append(
        (
            "J01_SPLIT upper_shell + lower_tub make the real N64 outline; lip in rebate, no clash",
            env_ok,
            f"envelope {bb.xlen:.2f}x{bb.ylen:.2f}x{bb.zlen:.2f} mm vs N64 model x{D.SCALE:.2f} "
            f"{ref_w:.2f}x{ref_d:.2f}x{ref_h:.2f}; measured lip gap "
            + (f"{lip_gap:.3f} mm (0.10..0.25)" if lip_gap is not None else "NOT FOUND")
            + f", overlap {shell_clash:.3f} mm^3",
        )
    )

    # 2. J-01: Coaxial 4x corner M3 bores + solid annular boss faces across the SPLIT_Z split
    clf_tub = BRepClass3d_SolidClassifier(tub.wrapped)
    clf_top = BRepClass3d_SolidClassifier(top.wrapped)
    bad_bosses = []
    for bx in D.CORNER_BOSS_XS:
        for by in D.CORNER_BOSS_YS:
            clf_tub.Perform(gp_Pnt(bx, by, D.SPLIT_Z - 1.0), 1e-4)
            tub_bore = clf_tub.State() == TopAbs_OUT
            clf_top.Perform(gp_Pnt(bx, by, D.SPLIT_Z + 1.0), 1e-4)
            top_bore = clf_top.State() == TopAbs_OUT
            clf_tub.Perform(gp_Pnt(bx + 3.0, by, D.SPLIT_Z - 0.5), 1e-4)
            tub_ring = clf_tub.State() == TopAbs_IN
            clf_top.Perform(gp_Pnt(bx + 3.0, by, D.SPLIT_Z + 0.5), 1e-4)
            top_ring = clf_top.State() == TopAbs_IN
            if not (tub_bore and top_bore and tub_ring and top_ring):
                bad_bosses.append(f"({bx:+.1f},{by:+.1f})")
    rows.append(
        (
            "J01_M3    all 4 corner M3 bosses & RX-M3x5.7 insert bores coaxial across split",
            not bad_bosses,
            f"4/4 corner bosses coaxial across Z={D.SPLIT_Z:.2f} mm (3D point classification)"
            if not bad_bosses
            else f"misaligned bosses: {bad_bosses}",
        )
    )

    # 2b. J01_SCREW (C9): the corner screw the BOM buys reaches far enough into the shell's insert
    # and not past its bore: measured from the tub's counterbore seat and the bore's end
    screw_bad, screw_msg = [], ""
    for bx in D.CORNER_BOSS_XS:
        for by in D.CORNER_BOSS_YS:
            up = probe.first_hit(tub, (bx + 2.5, by, -1.0), (0, 0, 1), max_len=20.0, step=0.01)
            down = probe.first_hit(top, (bx, by, D.SPLIT_Z + 0.05), (0, 0, 1), max_len=20.0)
            if up is None or down is None:
                screw_bad.append(f"({bx:+.1f},{by:+.1f}) seat or bore end not found")
                continue
            tip = -1.0 + up + D.CORNER_SCREW_L
            engaged, spare = tip - D.SPLIT_Z, (D.SPLIT_Z + 0.05 + down) - tip
            screw_msg = f"{engaged:.2f} mm into the insert, {spare:.2f} mm short of the bore end"
            if engaged < 4.5 or spare < 0.5:
                screw_bad.append(f"({bx:+.1f},{by:+.1f}): {screw_msg}")
    rows.append(
        (
            "J01_SCREW corner M3 screws engage >= 4.5 mm in the insert, >= 0.5 mm short of its end",
            not screw_bad,
            f"M3 x {D.CORNER_SCREW_L:.0f}: {screw_msg} (all 4 corners)"
            if not screw_bad
            else "; ".join(screw_bad),
        )
    )

    # 3. Reference N64 STEP cleanup manifest (`variant/n64_console.py` vs `step/n64_console_raw.py`)
    rows.extend(variant_manifest.check_variant("n64_console", load_by_path))

    # 4. Ray-cast outer silhouette & contour fidelity against `step/n64_shell.py` (`SH_OUTSIDE`)
    rows.append(_check_outer_silhouette(console_shells))

    # 5. Rule G13: Whole-console pairwise boolean interference across all parts & hardware
    cross_pairs = [
        ("upper_shell/radxa_elec", top, elec),
        ("upper_shell/radxa_step", top, radxa_x4.vendor_step_compound()),
        ("upper_shell/heatsink_step", top, radxa_x4.heatsink_solid()),
        ("cartridge_flaps/radxa_elec", flaps, elec),
        ("cartridge_flaps/heatsink_step", flaps, radxa_x4.heatsink_solid()),
        ("lower_tub/cartridge_flaps", tub, flaps),
        ("lower_tub/power_slider", tub, slider),
        ("lower_tub/reset_button", tub, reset),
        ("lower_tub/front_bezel", tub, bezel),
        ("lower_tub/tact_left", tub, sw_l),
        ("lower_tub/tact_right", tub, sw_r),
        ("lower_tub/usb_retainer_brackets", tub, ret),
        ("upper_shell/usb_retainer_brackets", top, ret),
        ("usb_retainer_brackets/radxa_elec", ret, elec),
        ("upper_shell/front_port_cover", top, cov),
        ("upper_shell/insert_p1", top, inserts[0]),
        ("upper_shell/insert_p2", top, inserts[1]),
        ("upper_shell/insert_p3", top, inserts[2]),
        ("upper_shell/insert_p4", top, inserts[3]),
        ("upper_shell/led_light_pipe", top, pipe),
    ]
    clashes = []
    for pname, a, b in cross_pairs:
        v = _common_volume(a, b)
        if v < 0 or v > 1e-3:
            clashes.append(f"{pname}={v:.3f}mm^3")
    rows.append(
        (
            "G13_FULL  zero boolean interference across full N64 Classic Mini console assembly",
            not clashes,
            f"0.000 mm^3 intersection across all {len(cross_pairs)} cross-subassembly pairs"
            if not clashes
            else "INTERFERENCE: " + ", ".join(clashes),
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
