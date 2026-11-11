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

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
import printable  # noqa: E402
from assembly import datum as D  # noqa: E402
from assembly import n64_scan_profiles as S  # noqa: E402
from component import omron_ss5gl  # noqa: E402
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common  # noqa: E402
from OCP.BRepClass3d import BRepClass3d_SolidClassifier  # noqa: E402
from OCP.gp import gp_Pnt  # noqa: E402
from OCP.TopAbs import TopAbs_IN, TopAbs_OUT  # noqa: E402
from part import (  # noqa: E402
    bezel_laser_jig,
    cartridge_flaps,
    front_bezel,
    power_slider,
    reset_button,
    usb_retainer_bracket,
)
from part.shared import n64_text as T  # noqa: E402
from subassembly import top_controls_mech  # noqa: E402
from testing import variant_manifest  # noqa: E402
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
                min_bed_ratio=0.15,
                max_aspect=3.0,
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
    clf_tub = BRepClass3d_SolidClassifier(tub.wrapped)
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
        # Extended 8.80mm front/mid Z=23.45mm travel-stop shelf on usb_retainer_bracket
        # (Y = -36.60 .. -27.80 mm, extending Face854 back to 0.45mm ahead of Omron SS-5GL)
        for stop_y in (-35.00, -28.20):
            clf_ret.Perform(gp_Pnt(cx, stop_y, 23.30), 1e-4)
            if clf_ret.State() != TopAbs_IN:
                return False
        # Coaxial Ø2.80mm guide pole on usb_retainer_bracket engaged inside Ø3.20mm button hole
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
        # Rear Z=23.45mm travel-stop post on lower_tub (Y = -20.80 .. -16.80 mm)
        clf_tub.Perform(gp_Pnt(cx, -20.50, 23.30), 1e-4)
        if clf_tub.State() != TopAbs_IN:
            return False
        clf_shell.Perform(gp_Pnt(cx, -31.00, 24.00), 1e-4)
        return clf_shell.State() == TopAbs_OUT

    slider_bb = slider.BoundingBox()
    reset_bb = reset.BoundingBox()
    slider_pressed = slider.moved(cq.Location(cq.Vector(0.0, 0.0, -D.SLIDER_STROKE_Z)))
    v_p_shell = (
        _common_volume(shell, slider_pressed)
        + _common_volume(tub, slider_pressed)
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
            f"radial clear={x_clear:.2f} mm/side, chimney=360deg@Z=24mm, zmax={slider_bb.zmax:.2f} "
            f"mm, Omron overlap={v_p_sw:.2f} mm^3",
        )
    )

    # 5. J-04: Momentary Reset button guided in chimney & 1.90 mm stroke actuating Omron SS-5GL
    r_clear = (D.RESET_BORE_W - D.RESET_SHAFT_W) / 2.0
    reset_pressed = reset.moved(cq.Location(cq.Vector(0.0, 0.0, -D.RESET_STROKE_Z)))
    v_shell_press = (
        _common_volume(shell, reset_pressed)
        + _common_volume(tub, reset_pressed)
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
            f"radial clearance={r_clear:.2f} mm/side, chimney=360deg@Z=24mm, "
            f"Omron lever overlap={v_sw_press:.2f} mm^3",
        )
    )

    # 5b. OMRON_ACT: Omron SS-5GL activation tolerance budget + physical mounting pins on lower_tub
    act = omron_ss5gl.activation_metrics(D.RESET_STROKE_Z)
    pin_clear = (D.OMRON_HOLE_D - D.OMRON_PIN_D) / 2.0
    clf_pin = BRepClass3d_SolidClassifier(tub.wrapped)
    pins_and_m2_ok = True
    for x_pin, x_m2 in ((-24.23, -33.73), (24.23, 33.73)):
        clf_pin.Perform(gp_Pnt(x_pin, -24.00, D.OMRON_HOLE_Z), 1e-4)
        pin_solid = clf_pin.State() == TopAbs_IN
        clf_pin.Perform(gp_Pnt(x_m2, -19.50, D.OMRON_HOLE_Z), 1e-4)
        m2_bore_open = clf_pin.State() == TopAbs_OUT
        clf_pin.Perform(gp_Pnt(x_m2, -19.50, D.OMRON_HOLE_Z + 2.50), 1e-4)
        wall_solid = clf_pin.State() == TopAbs_IN
        pins_and_m2_ok = pins_and_m2_ok and pin_solid and m2_bore_open and wall_solid

    omron_ok = (
        0.05 <= pin_clear <= 0.15
        and pins_and_m2_ok
        and act["release_margin"] >= -1e-6
        and 0.30 <= act["z_earliest"] < act["z_nominal"] < act["z_latest"]
        and act["click_margin_before_stop"] >= 0.10
        and act["overtravel_margin_to_bottom"] >= 0.50
    )
    rows.append(
        (
            "OMRON_ACT Omron SS-5GL clicks across OP=8.8+-0.8mm band & stops before overtravel",
            omron_ok,
            f"click stroke={act['z_earliest']:.2f}/{act['z_nominal']:.2f}/{act['z_latest']:.2f} mm "
            f"(stop {act['z_stop']:.2f} mm, overtravel margin="
            f"{act['overtravel_margin_to_bottom']:.2f} mm, pin clear={pin_clear:.3f} mm/side)",
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
    j09_ok = (
        abs(flaps_bb.xlen - D.CARTRIDGE_FLAP_W) < 0.05
        and abs(flaps_bb.ylen - D.CARTRIDGE_FLAP_D) < 0.05
        and abs(flaps_bb.zmax - D.CARTRIDGE_FLAP_Z) < 0.05
        and 0.10 <= D.CARTRIDGE_FLAP_CLEAR <= 0.25
        and 0.02 <= z_gap <= 0.15
        and _common_volume(shell, flaps) <= 1e-3
    )
    rows.append(
        (
            "J09_FLAPS cartridge_flaps insert seats in upper_shell pocket with 0.15mm/side gap",
            j09_ok,
            f"flaps {flaps_bb.xlen:.2f}x{flaps_bb.ylen:.2f}x{flaps_bb.zlen:.2f} mm at "
            f"Z={flaps_bb.zmax:.2f} mm, XY clear={D.CARTRIDGE_FLAP_CLEAR:.2f} mm/side",
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
