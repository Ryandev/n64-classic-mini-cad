"""Gate checks for `top_controls_mech.py`, `variant/upper_shell.py`, and top-deck parts.

Verifies:
  - Printability (`manifold`, `single_body`, `bed`, `overhang`, `wall`, `footprint`) for
    `upper_shell`, `cartridge_flaps`, `power_slider`, `reset_button`, `front_bezel`, and
    `bezel_laser_jig`
  - `variant/upper_shell.py` manifest against `part/upper_shell.py` (`DEVIATIONS`)
  - `G13` zero boolean interference across `upper_shell`, `cartridge_flaps`, `power_slider`,
    `reset_button`, `front_bezel`, and the 2x `Omron SS-5GL` microswitches
  - `J-03` Momentary `POWER` button (`0.22 mm/side` radial clearance, identical smooth stadium
    button profile to `RESET` with transverse nub removed, `1.90 mm` Z stroke actuating left
    `Omron SS-5GL`)
  - `J-04` Momentary `RESET` button (`0.22 mm/side` radial clearance and `1.90 mm` Z press
    stroke actuating right `Omron SS-5GL`, `AC-T18`)
  - `OMRON_ACT` `Omron SS-5GL` activation tolerance budget across `OP = 8.8 +/- 0.8 mm`
    (`8.0 .. 9.6 mm`), `overtravel >= 1.2 mm`, `MD <= 0.8 mm`, and `Ø2.20 mm` in `Ø2.35 mm` fit
  - `J-06` Front Clear Acrylic shield emblem jewel seated in nose pocket (`0.15 mm/side`)
  - `J-09` Separately-printed Light Cool Grey `cartridge_flaps` insert in pocket (`0.15 mm/side`)
  - `DOME_TOP` Closed cartridge slot roof & recessed Expansion Pak cover on the barrel dome
  - `PLAQUE` The published plaque lettering (`PLAQUE_TEXT`) lies wholly inside the rear oval ring
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402
from assembly import n64_scan_profiles as S  # noqa: E402
from component import omron_ss5gl, radxa_x4  # noqa: E402
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common  # noqa: E402
from OCP.BRepClass3d import BRepClass3d_SolidClassifier  # noqa: E402
from OCP.BRepExtrema import BRepExtrema_DistShapeShape  # noqa: E402
from OCP.gp import gp_Pnt  # noqa: E402
from OCP.TopAbs import TopAbs_IN, TopAbs_OUT  # noqa: E402
from part import (  # noqa: E402
    bezel_laser_jig,
    cartridge_flaps,
    front_bezel,
    front_port_cover,
    led_light_pipe,
    power_slider,
    reset_button,
    usb_retainer_bracket,
)
from part.shared import n64_text as T  # noqa: E402
from process import printable  # noqa: E402
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


def check_all():
    rows = []
    shell = upper_shell.get_shape()
    tub = lower_tub.get_shape()
    flaps = cartridge_flaps.get_shape()
    slider = power_slider.get_shape()
    reset = reset_button.get_shape()
    bezel = front_bezel.get_shape()
    jig = bezel_laser_jig.get_shape()
    sw_left, sw_right = top_controls_mech.omron_switches()
    ret_both = cq.Compound.makeCompound(usb_retainer_bracket.brackets())
    carriers = front_panel_mech.front_carriers_compound()

    # 1. Printability rows on all top-deck printed & laser-cut parts
    for name, shape, mod in (
        ("upper_shell", shell, upper_shell),
        ("cartridge_flaps", flaps, cartridge_flaps),
        ("power_slider", slider, power_slider),
        ("reset_button", reset, reset_button),
        ("front_bezel", bezel, front_bezel),
        ("bezel_laser_jig", jig, bezel_laser_jig),
    ):
        rows.extend(
            printable.check_part(
                name,
                shape,
                up=mod.PRINT_NORMAL,
                min_wall_mm=0.8,
                min_bed_ratio=getattr(mod, "MIN_BED_RATIO", 0.15),
                max_aspect=3.0,
                # Parts that declare no SUPPORT_MM2 must print without support.
                support_mm2=getattr(mod, "SUPPORT_MM2", 0.0),
            )
        )

    # 2. Variant manifest rows for variant/upper_shell.py vs part/upper_shell.py
    rows.extend(variant_manifest.check_variant("upper_shell", load_by_path))

    # 3. Rule G13: zero boolean interference at rest
    pairs = [
        ("upper_shell/cartridge_flaps", shell, flaps),
        ("upper_shell/power_slider", shell, slider),
        ("upper_shell/reset_button", shell, reset),
        ("upper_shell/front_bezel", shell, bezel),
        ("upper_shell/omron_left", shell, sw_left),
        ("upper_shell/omron_right", shell, sw_right),
        ("power_slider/omron_left", slider, sw_left),
        ("reset_button/omron_right", reset, sw_right),
        ("upper_shell/usb_retainer_brackets", shell, ret_both),
        ("power_slider/usb_retainer_brackets", slider, ret_both),
        ("reset_button/usb_retainer_brackets", reset, ret_both),
        ("usb_retainer_brackets/omron_left", ret_both, sw_left),
        ("usb_retainer_brackets/omron_right", ret_both, sw_right),
        ("upper_shell/front_carriers", shell, carriers),
        ("power_slider/front_carriers", slider, carriers),
        ("reset_button/front_carriers", reset, carriers),
        ("front_carriers/omron_left", carriers, sw_left),
        ("front_carriers/omron_right", carriers, sw_right),
    ]
    bad_pairs = []
    for pname, a, b in pairs:
        v = _common_volume(a, b)
        if v < 0 or v > 1e-3:
            bad_pairs.append(f"{pname}={v:.3f}mm^3")
    rows.append(
        (
            "G13_TOP   zero boolean interference across upper_shell and top controls",
            not bad_pairs,
            f"0.000 mm^3 intersection across all {len(pairs)} upper-deck pairs"
            if not bad_pairs
            else "INTERFERENCE: " + ", ".join(bad_pairs),
        )
    )

    # 4. J-03: Momentary Power button matches Reset profile, guided in chimney & actuates Omron
    clf_shell = BRepClass3d_SolidClassifier(shell.wrapped)
    clf_car = BRepClass3d_SolidClassifier(carriers.wrapped)
    clf_ret = BRepClass3d_SolidClassifier(ret_both.wrapped)
    clf_slider = BRepClass3d_SolidClassifier(slider.wrapped)
    clf_reset = BRepClass3d_SolidClassifier(reset.wrapped)

    def _chimney_guided(cx: float) -> bool:
        x_out = cx - 6.30 if cx < 0.0 else cx + 6.30
        pts_in = (
            (cx, -38.30, 24.00),  # front stadium chimney wall (upper_shell)
            (cx, -19.30, 24.00),  # rear stadium chimney wall (upper_shell)
            (x_out, D.CONTROLS_Y, 24.00),  # outboard stadium chimney wall (upper_shell)
        )
        for px, py, pz in pts_in:
            clf_shell.Perform(gp_Pnt(px, py, pz), 1e-4)
            if clf_shell.State() != TopAbs_IN:
                return False
        # Front travel stop (SLEEVE_STOP_Z) on usb_retainer_bracket, under the button's sleeve
        for stop_y in (-35.00, -28.20):
            clf_ret.Perform(gp_Pnt(cx, stop_y, D.SLEEVE_STOP_Z - 0.15), 1e-4)
            if clf_ret.State() != TopAbs_IN:
                return False
        # Ø2.80 guide pole on usb_retainer_bracket engaged inside the button's sleeve
        clf_ret.Perform(gp_Pnt(cx, -32.20, 26.20), 1e-4)
        if clf_ret.State() != TopAbs_IN:
            return False
        clf_btn = clf_slider if cx < 0.0 else clf_reset
        clf_btn.Perform(gp_Pnt(cx, -32.20, 26.20), 1e-4)
        if clf_btn.State() != TopAbs_OUT:
            return False
        clf_btn.Perform(gp_Pnt(cx + 2.20, -32.20, 26.20), 1e-4)
        if clf_btn.State() != TopAbs_IN:
            return False
        # Rear travel-stop post on front_io_carrier (Y = -20.80 .. -16.80 mm)
        clf_car.Perform(gp_Pnt(cx, -20.50, D.BUTTON_STOP_Z - 0.15), 1e-4)
        if clf_car.State() != TopAbs_IN:
            return False
        clf_shell.Perform(gp_Pnt(cx, -31.00, 24.00), 1e-4)
        return clf_shell.State() == TopAbs_OUT

    slider_bb = slider.BoundingBox()
    reset_bb = reset.BoundingBox()
    slider_pressed = slider.moved(cq.Location(cq.Vector(0.0, 0.0, -D.SLIDER_STROKE_Z)))
    v_p_shell = (
        _common_volume(shell, slider_pressed)
        + _common_volume(tub, slider_pressed)
        + _common_volume(carriers, slider_pressed)
        + _common_volume(ret_both, slider_pressed)
    )
    v_p_sw = _common_volume(sw_left, slider_pressed)
    x_clear = (D.SLIDER_SLOT_W - D.SLIDER_NECK_W) / 2.0
    same_profile = (
        abs(slider_bb.xlen - reset_bb.xlen) < 0.05
        and abs(slider_bb.ylen - reset_bb.ylen) < 0.05
        and abs(slider_bb.zmax - reset_bb.zmax) < 0.05
    )
    j03_ok = (
        0.20 <= x_clear <= 0.35
        and same_profile
        and _chimney_guided(D.POWER_SLIDER_X)
        and v_p_shell <= 1e-3
        and v_p_sw > 1.0
    )
    rows.append(
        (
            "J03_SLIDE momentary power_slider guided in chimney, matches reset & actuates Omron",
            j03_ok,
            f"radial clear={x_clear:.2f} mm/side, "
            f"chimney guided={_chimney_guided(D.POWER_SLIDER_X)}, "
            f"same profile={same_profile}, pressed clash={v_p_shell:.3f} mm^3, "
            f"zmax={slider_bb.zmax:.2f} mm, Omron overlap={v_p_sw:.2f} mm^3",
        )
    )

    # 5. J-04: Momentary Reset button guided in chimney & 1.90 mm stroke actuating Omron SS-5GL
    r_clear = (D.RESET_BORE_W - D.RESET_SHAFT_W) / 2.0
    reset_pressed = reset.moved(cq.Location(cq.Vector(0.0, 0.0, -D.RESET_STROKE_Z)))
    v_shell_press = (
        _common_volume(shell, reset_pressed)
        + _common_volume(tub, reset_pressed)
        + _common_volume(carriers, reset_pressed)
        + _common_volume(ret_both, reset_pressed)
    )
    v_sw_press = _common_volume(sw_right, reset_pressed)
    j04_ok = (
        0.20 <= r_clear <= 0.35
        and _chimney_guided(D.RESET_BTN_X)
        and v_shell_press <= 1e-3
        and v_sw_press > 1.0
    )
    rows.append(
        (
            "J04_RESET reset_button guided in chimney by 0.22mm/side & actuates Omron SS-5GL",
            j04_ok,
            f"radial clearance={r_clear:.2f} mm/side, "
            f"chimney guided={_chimney_guided(D.RESET_BTN_X)}, "
            f"pressed clash={v_shell_press:.3f} mm^3, Omron lever overlap={v_sw_press:.2f} mm^3",
        )
    )

    # 5a. Two guides per button (owner, coupon plate 4 2026-11-16: "it wobbles as it goes down"):
    # the chimney at the top, a sleeve on the bracket's guide pole below.
    rows.extend(_button_guide_rows(shell, carriers, ret_both, slider, reset))

    # 5b. OMRON_ACT (C3): move each real button down the real switch lever. For a button offset
    # `dz`, the lever tip sits at the highest height where the two don't overlap; that is where
    # the button holds it. Omron SS-5GL datasheet (hinge lever): OP 8.8 +-0.8, MD <= 0.8,
    # OT >= 1.2, all at the tip, above the mounting holes.
    def _tip_height(button: cq.Shape, cx: float, dz: float) -> tuple[float, float]:
        pressed = button.moved(cq.Location(cq.Vector(0.0, 0.0, -dz)))
        lo, hi = 5.0, omron_ss5gl.FREE_POSITION_MAX
        for _ in range(14):
            mid = (lo + hi) / 2.0
            sw = omron_ss5gl.placed_at(cx, lever_deflection=omron_ss5gl.FREE_POSITION_MAX - mid)
            lo, hi = (mid, hi) if _common_volume(sw, pressed) <= 1e-4 else (lo, mid)
        touch = cq.Shape.cast(
            BRepAlgoAPI_Common(
                omron_ss5gl.placed_at(
                    cx, lever_deflection=omron_ss5gl.FREE_POSITION_MAX - (lo + 0.05)
                ).wrapped,
                pressed.wrapped,
            ).Shape()
        )
        return lo, touch.Center().x if touch.Volume() > 0 else float("nan")

    op_lo = omron_ss5gl.OPERATING_POSITION - omron_ss5gl.OPERATING_POSITION_TOL
    op_hi = omron_ss5gl.OPERATING_POSITION + omron_ss5gl.OPERATING_POSITION_TOL
    act_msgs, act_ok = [], True
    for name, button, cx in (
        ("POWER", slider, D.POWER_SLIDER_X),
        ("RESET", reset, D.RESET_BTN_X),
    ):
        h_rest, x_touch = _tip_height(button, cx, 0.0)
        h_stop, _ = _tip_height(button, cx, D.RESET_STROKE_Z)
        release = h_rest - (op_hi + omron_ss5gl.MOVEMENT_DIFF_MAX)
        click = op_lo - h_stop
        overtravel_lo = h_stop - (op_lo - omron_ss5gl.OVERTRAVEL_MIN)
        centred = abs(x_touch - cx) <= 1.5
        datum_ok = abs(h_stop - D.OMRON_TIP_AT_STOP) <= 0.02  # the FEM's stop-flex limit uses it
        act_ok = (
            act_ok
            and release >= 0.10
            and click >= 0.10
            and overtravel_lo >= 0
            and centred
            and datum_ok
        )
        act_msgs.append(
            f"{name}: tip {h_rest:.2f} -> {h_stop:.2f} mm, release margin {release:.2f}, "
            f"click margin {click:.2f} (OP {op_lo:.1f}), presses at x {x_touch - cx:+.2f} from "
            f"centre; earliest switch {op_hi - h_stop:.2f} mm past OP (OT >= "
            f"{omron_ss5gl.OVERTRAVEL_MIN}); stop datum {D.OMRON_TIP_AT_STOP:.2f}"
        )
    rows.append(
        (
            "OMRON_ACT every SS-5GL (OP 8.0..9.6) clicks before the stop & releases at rest",
            act_ok,
            "; ".join(act_msgs),
        )
    )

    # 5b2. OMRON_INSTALL (coupon plate 2, 2026-11-15): a switch on a horizontal pin had no way
    # in. It could only slide along the pin, and its legs, down in the tower's slots, hit the slot
    # wall after 1 mm. Each switch must now drop in from above: lifted 0.5 mm at a time up to its
    # own height clear of everything, it touches nothing in the carrier or tub.
    install_bad = []
    for name, sw in (("POWER", sw_left), ("RESET", sw_right)):
        lift = omron_ss5gl.BODY_HEIGHT + omron_ss5gl.TERMINAL_DROP
        steps = int(lift / 0.5)
        hits = [
            (k * 0.5, v)
            for k in range(1, steps + 1)
            if (
                v := _common_volume(carriers, sw.moved(cq.Location(cq.Vector(0, 0, k * 0.5))))
                + _common_volume(tub, sw.moved(cq.Location(cq.Vector(0, 0, k * 0.5))))
            )
            > 1e-3
        ]
        if hits:
            install_bad.append(
                f"{name}: hits carrier/tub {hits[0][1]:.2f} mm^3 at {hits[0][0]:.1f} mm up"
            )
    rows.append(
        (
            "OMRON_INSTALL each switch drops into its tower from above, touching nothing",
            not install_bad,
            "; ".join(install_bad)
            or f"lifted to {omron_ss5gl.BODY_HEIGHT + omron_ss5gl.TERMINAL_DROP:.1f} mm in 0.5 mm "
            "steps: clear of the carrier & tub all the way",
        )
    )

    # 5c. OMRON_SCREW (C2; both holes since coupon plate 2, 2026-11-15): each switch is held by a
    # screw in each of its two holes, driven from behind the tower (the USB-A socket leaves no room
    # in front). The screw bites into the switch's hole and stops short of its front face; in the
    # tower it is a close fit, so the switch is located without play and pulled back against it.
    screws = top_controls_mech.omron_screws()
    usb = radxa_x4.usb_a_cluster()
    bracket = front_panel_mech.usb_retainer_compound()
    screw_bad = []
    if len(screws) != 4:
        screw_bad.append(f"{len(screws)} switch screws, want 4 (both holes of both switches)")
    fits = []
    for screw in screws:
        sb = screw.BoundingBox()
        x = (sb.xmin + sb.xmax) / 2.0
        name, sw = ("POWER", sw_left) if x < 0 else ("RESET", sw_right)
        wb = sw.BoundingBox()
        engaged = (D.OMRON_Y + omron_ss5gl.BODY_WIDTH / 2.0) - sb.ymin
        tip_margin = sb.ymin - wb.ymin
        clashes = {
            k: _common_volume(v, screw)
            for k, v in (
                ("tub", tub),
                ("carriers", carriers),
                ("switch", sw),
                ("usb", usb),
                ("bracket", bracket),
            )
        }
        # the tower hole's fit: gap from the shank, inside the tower, to the carrier round it
        shank = cq.Solid.makeCylinder(
            D.OMRON_SCREW_D / 2.0,
            D.OMRON_TOWER_Y1 - (-20.80) - 0.2,
            cq.Vector(x, -20.70, D.OMRON_HOLE_Z),
            cq.Vector(0.0, 1.0, 0.0),
        )
        ext = BRepExtrema_DistShapeShape(shank.wrapped, carriers.wrapped)
        ext.Perform()
        fit = ext.Value()
        fits.append(fit)
        driver = cq.Solid.makeCylinder(
            D.OMRON_SCREW_HEAD_D / 2.0,
            40.0,
            cq.Vector(x, D.OMRON_TOWER_Y1 + D.OMRON_SCREW_HEAD_H + 0.05, D.OMRON_HOLE_Z),
            cq.Vector(0.0, 1.0, 0.0),
        )
        path = _common_volume(tub, driver) + _common_volume(carriers, driver)
        if (
            any(v > 1e-3 for v in clashes.values())
            or tip_margin < 0.3
            or engaged < 4.0
            or path > 1e-3
            # nominal close fit; rounded so 0.05 drawn isn't lost to float noise
            or not 0.05 <= round(fit, 3) <= 0.10
        ):
            screw_bad.append(
                f"{name} x {x:+.2f}: tip {tip_margin:.2f} mm inside the switch front, "
                f"{engaged:.2f} mm engaged, tower fit {fit:.3f} mm/side, "
                f"clash { ({k: round(v, 3) for k, v in clashes.items() if v > 1e-3}) }, "
                f"driver path {path:.3f} mm^3"
            )
    rows.append(
        (
            "OMRON_SCREW 2 screws per switch from behind: close fit in tower, bite in switch",
            not screw_bad,
            f"4 x M{D.OMRON_SCREW_D:g} x {D.OMRON_SCREW_L:.0f} mm: tip "
            f"{screws[0].BoundingBox().ymin - sw_left.BoundingBox().ymin:.2f} mm short of the "
            f"switch front (min 0.3), >= 4 mm in the switch, tower fit "
            f"{min(fits):.3f}..{max(fits):.3f} mm/side (0.05..0.10 nominal), 0 mm^3 with "
            "tub/switch/USB/bracket, 40 mm driver path clear"
            if not screw_bad
            else "; ".join(screw_bad),
        )
    )

    # 6. J-06: Front black shield emblem bezel seated inside upper_shell front nose pocket
    bezel_bb = bezel.BoundingBox()
    j06_ok = (
        abs(bezel_bb.xlen - D.BEZEL_W) < 0.05
        and abs(bezel_bb.zlen - D.BEZEL_H) < 0.05
        and abs(bezel_bb.ymin - D.BEZEL_Y0) < 0.05
        and _common_volume(shell, bezel) <= 1e-3
    )
    rows.append(
        (
            "J06_BEZEL front_bezel shield seats flush in upper_shell curved front nose pocket",
            j06_ok,
            f"bezel {bezel_bb.xlen:.1f}x{bezel_bb.zlen:.1f}x{bezel_bb.ylen:.1f} mm "
            f"at Y={bezel_bb.ymin:.2f} mm",
        )
    )

    # 6b. J-09: Separately-printed Light Cool Grey cartridge_flaps insert seated in pocket
    flaps_bb = flaps.BoundingBox()
    z_gap = D.CARTRIDGE_FLAP_Z0 - D.CARTRIDGE_POCKET_Z0
    # The XY fit measured on the solids (a slab through the flaps), less the paint both faces
    # gain: comparing CARTRIDGE_FLAP_FIT to a band graded the datum, not the parts (Gemini #1).
    flap_gap = probe.slice_gap(flaps, shell, "z", (flaps_bb.zmin + flaps_bb.zmax) / 2.0)
    flap_fit = flap_gap - 2.0 * D.PAINT_T
    j09_ok = (
        abs(flaps_bb.xlen - D.CARTRIDGE_FLAP_W) < 0.05
        and abs(flaps_bb.ylen - D.CARTRIDGE_FLAP_D) < 0.05
        and abs(flaps_bb.zmax - D.CARTRIDGE_FLAP_Z) < 0.05
        and 0.10 <= flap_fit <= 0.25
        and 0.02 <= z_gap <= 0.15
        and _common_volume(shell, flaps) <= 1e-3
    )
    rows.append(
        (
            "J09_FLAPS cartridge_flaps seat in upper_shell pocket, 0.15 mm/side after paint",
            j09_ok,
            f"flaps {flaps_bb.xlen:.2f}x{flaps_bb.ylen:.2f}x{flaps_bb.zlen:.2f} mm at "
            f"Z={flaps_bb.zmax:.2f} mm, XY gap {flap_gap:.2f} mm/side measured, "
            f"{flap_fit:.2f} after paint (fit 0.10..0.25)",
        )
    )

    # 7. DOME_TOP: Cartridge slot roof is solid/closed in cradle; Expansion Pak recess is present
    clf = BRepClass3d_SolidClassifier(shell.wrapped)
    clf_flaps = BRepClass3d_SolidClassifier(flaps.wrapped)
    cart_y = float(S.CARTRIDGE_SLOT_OPENING_50["y_centre"])
    exp_y = -20.50
    z_cart_probe = D.CARTRIDGE_FLAP_Z - 0.65
    z_floor_probe = D.CARTRIDGE_POCKET_Z0 - 0.50
    z_exp_probe = D.SHELL_H - 0.15
    clf_flaps.Perform(gp_Pnt(0.0, cart_y, z_cart_probe), 1e-4)
    flaps_solid = clf_flaps.State() == TopAbs_IN
    clf.Perform(gp_Pnt(0.0, cart_y, z_floor_probe), 1e-4)
    floor_solid = clf.State() == TopAbs_IN
    cart_covered = flaps_solid and floor_solid
    clf.Perform(gp_Pnt(0.0, exp_y, z_exp_probe), 1e-4)
    exp_recessed = clf.State() == TopAbs_OUT
    rows.append(
        (
            "DOME_TOP  upper_shell closes cartridge dust flaps & recesses Expansion Pak cover",
            cart_covered and exp_recessed,
            f"cartridge roof (Y={cart_y:+.2f}, Z={z_cart_probe:.2f}) solid={cart_covered}, "
            f"Expansion Pak recess (Y={exp_y:+.2f}, Z={z_exp_probe:.2f}) open={exp_recessed}",
        )
    )

    # PLAQUE: always the public lettering, so the row holds even where the owner's local glyphs
    # replace it in their own build.
    ring_in = T.loop_to_prism(T.NINTENDO_PLAQUE_LOOP[1][0], (), 24.0, 10.0)
    letters = T.plaque_text_prisms(24.0, 10.0)
    spill = sum(letter.cut(ring_in).Volume() for letter in letters)
    rows.append(
        (
            f"PLAQUE    public lettering {T.PLAQUE_TEXT!r} sits inside the rear oval ring",
            bool(letters) and spill <= 1e-6,
            f"{len(letters)} letter solid(s), volume outside the inner ring={spill:.4f} mm^3",
        )
    )

    rows.append(_paint_fit(shell, tub, flaps, bezel))
    return rows


# BTN_TILT limit: half the free tilt of the plate 4 buttons (4.8 deg, the pole then only a
# backstop in a Ø4.0 hole), which the owner reported as wobbling.
BTN_TILT_MAX_DEG = 2.4


def _button_guide_rows(shell, tub, ret_both, slider, reset):
    """BTN_TILT, BTN_STACK and BTN_STOP: the two guides hold the button straight, never fight,
    and the stops take the stroke."""

    def near(shape: cq.Shape, cx: float) -> cq.Shape:
        return shape.intersect(
            cq.Solid.makeBox(16, 22, 16, cq.Vector(cx - 8, D.CONTROLS_Y - 11, 16))
        )

    def gap(a: cq.Shape, b: cq.Shape) -> float:
        ext = BRepExtrema_DistShapeShape(a.wrapped, b.wrapped)
        ext.Perform()
        return ext.Value()

    def overlap(a: cq.Shape, b: cq.Shape) -> bool:
        return gap(a, b) < 1e-4

    def down(shape: cq.Shape, dz: float) -> cq.Shape:
        return shape.moved(cq.Location(cq.Vector(0.0, 0.0, -dz)))

    rows = []
    tilt_msgs, tilt_ok = [], True
    stack_msgs, stack_ok = [], True
    stop_msgs, stop_ok = [], True
    offset = D.LIP_CLEAR + D.BRACKET_PLACE_TOL  # how far the pole can sit off the chimney's axis
    # The button moves toward the pole until both guides have the same play left
    shift = (offset + D.RESET_CLEAR - D.SLEEVE_CLEAR) / 2.0
    for name, button, cx in (("POWER", slider, D.POWER_SLIDER_X), ("RESET", reset, D.RESET_BTN_X)):
        shell_n, ret_n, tub_n = near(shell, cx), near(ret_both, cx), near(tub, cx)
        guides = cq.Compound.makeCompound([shell_n, ret_n])
        # The lettered crown sits above the chimney and can't touch it; leaving it out keeps
        # the distance queries fast
        body = button.intersect(
            cq.Solid.makeBox(20, 26, 10.2, cq.Vector(cx - 10, D.CONTROLS_Y - 13, 20))
        )

        # BTN_TILT: at mid-stroke, tipping the button BTN_TILT_MAX_DEG about any horizontal axis
        # must make it touch a guide. Moving the pivot sideways only adds an up/down slide, which
        # the button is free to make, so pivots up the axis cover every tilt.
        mid = down(body, D.RESET_STROKE_Z / 2.0)
        free = []
        for zp in (21.0, 23.0, 25.0, 27.0, 29.0):
            pivot = cq.Vector(cx, D.CONTROLS_Y, zp)
            for axis in (cq.Vector(1, 0, 0), cq.Vector(0, 1, 0)):
                for sign in (1.0, -1.0):
                    tipped = mid.rotate(pivot, pivot + axis, sign * BTN_TILT_MAX_DEG)
                    if not overlap(tipped, guides):
                        free.append(f"z {zp:g} about {'X' if axis.x else 'Y'}{sign:+.0f}")
        # Also verify Z-axis anti-rotation on the oblong guide pole alone (with upper_shell off):
        pole_pivot = cq.Vector(cx, D.BUTTON_POLE_Y, 24.0)
        for sign in (1.0, -1.0):
            yawed = mid.rotate(pole_pivot, pole_pivot + cq.Vector(0, 0, 1), sign * 20.0)
            if not overlap(yawed, ret_n):
                free.append(f"yaw about Z{sign:+.0f} on pole")
        tilt_ok = tilt_ok and not free
        tilt_msgs.append(
            f"{name}: " + (f"free past the limit at {', '.join(free)}" if free else "held")
        )

        # BTN_STACK: with the pole as far off the chimney's axis as the lip play and the glued
        # bracket's placement allow, in any direction, the button still slides in both guides
        worst = float("inf")
        for k in range(8):
            ang = math.radians(45.0 * k)
            ux, uy = math.cos(ang), math.sin(ang)
            ret_off = ret_n.moved(cq.Location(cq.Vector(offset * ux, offset * uy, 0.0)))
            for dz in (0.0, D.RESET_STROKE_Z - 0.05):
                moved = body.moved(cq.Location(cq.Vector(shift * ux, shift * uy, -dz)))
                worst = min(worst, gap(moved, shell_n), gap(moved, ret_off))
        stack_ok = stack_ok and worst >= 1e-4
        stack_msgs.append(f"{name} {worst:.3f} mm")

        # BTN_STOP: 0.05 mm past the stroke the sleeve's foot is on the bracket's stop and the
        # underside on the tub's post
        past = down(body, D.RESET_STROKE_Z + 0.05)
        on_front, on_rear = overlap(past, ret_n), overlap(past, tub_n)
        stop_ok = stop_ok and on_front and on_rear
        stop_msgs.append(f"{name}: front stop {on_front}, rear post {on_rear}")

    rows.append(
        (
            f"BTN_TILT chimney + sleeve hold each button within {BTN_TILT_MAX_DEG} deg (was 4.8)",
            tilt_ok,
            "; ".join(tilt_msgs),
        )
    )
    rows.append(
        (
            "BTN_STACK chimney and sleeve never fight with the pole off-axis by lip + bracket",
            stack_ok,
            f"pole off by {offset:.2f} (lip {D.LIP_CLEAR:.2f} + bracket {D.BRACKET_PLACE_TOL:.2f}),"
            f" button follows {shift:.3f}: least gap left "
            + ", ".join(stack_msgs)
            + f" (chimney {D.RESET_CLEAR:.2f} + sleeve {D.SLEEVE_CLEAR:.2f} a side)",
        )
    )
    rows.append(
        (
            "BTN_STOP sleeve lands on the bracket stop, underside on the tub post",
            stop_ok,
            "; ".join(stop_msgs),
        )
    )
    return rows


def _paint_fit(shell: cq.Shape, tub: cq.Shape, flaps: cq.Shape, bezel: cq.Shape) -> tuple:
    """PAINT_FIT: every painted fit, measured on the solids, still has its working clearance
    once paint closes it (owner 2026-11-13: everything visible painted, no masking).

    Each gap is measured in a thin slab through the fit, so a seat or glue face the parts also
    touch doesn't hide the edge gap. Paint lands on both faces (door, flaps) or one (the clear
    jewel and lens); `D.PAINT_T` per face.
    """
    case = shell.fuse(tub, *front_panel_mech.front_carriers())
    w_door = D.FRONT_BAY_W - 2.0 * D.FRONT_COVER_CLEAR
    door = front_port_cover.cover_at(D.FRONT_BAY_X)
    db = door.BoundingBox()
    door_body = door.intersect(  # without the hinge pins that run past its ends
        cq.Solid.makeBox(
            w_door,
            db.ylen + 2.0,
            db.zlen + 2.0,
            cq.Vector(D.FRONT_BAY_X - w_door / 2.0, db.ymin - 1.0, db.zmin - 1.0),
        )
    )
    pipe = led_light_pipe.get_shape()
    insert = front_panel_mech.port_inserts()[0]  # P1, in the left door's pocket
    ib = insert.BoundingBox()
    y_boss = D.FRONT_BAY_Y0 - D.PORT_INSERT_GAP_Y + D.PORT_INSERT_BOSS_H / 2.0  # boss mid-depth
    fb, bb, pb = flaps.BoundingBox(), bezel.BoundingBox(), pipe.BoundingBox()
    assert ib.ymin < y_boss < ib.ymax, "the slab must cut the insert's boss"
    fits = (
        (
            "door in bay",
            probe.slice_gap(door_body, case, "y", (db.ymin + db.ymax) / 2.0),
            2,
            D.FRONT_COVER_FIT,
        ),
        (
            "flaps in pocket",
            probe.slice_gap(flaps, shell, "z", (fb.zmin + fb.zmax) / 2.0),
            2,
            D.CARTRIDGE_FLAP_FIT,
        ),
        (
            "jewel in pocket",
            probe.slice_gap(bezel, case, "y", (bb.ymin + bb.ymax) / 2.0),
            1,
            D.BEZEL_POCKET_FIT,
        ),
        ("LED lens in wall", probe.slice_gap(pipe, case, "y", pb.ymin + 0.3), 1, D.LED_FIT),
        ("port insert in door", probe.slice_gap(insert, door, "y", y_boss), 2, D.PORT_POCKET_FIT),
    )
    msgs, ok = [], True
    for name, gap, faces, fit in fits:
        after = gap - faces * D.PAINT_T
        # within 0.05 of the fit both ways: too tight jams, too loose rattles (Gemini #10)
        ok = ok and abs(after - fit) <= 0.05
        msgs.append(f"{name} {gap:.2f} -> {after:.2f} after paint (fit {fit:.2f} +-0.05)")
    return (
        "PAINT_FIT painted fits keep their working clearance after paint (PAINT_T per face)",
        ok,
        f"PAINT_T {D.PAINT_T:.2f}: " + "; ".join(msgs),
    )


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
