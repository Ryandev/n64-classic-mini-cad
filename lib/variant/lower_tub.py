"""Variant of `part/lower_tub.py` adding Radxa X4 M2.5 standoffs, LED holder & I/O apertures.

Imports the faithful 50%-scale N64 lower tub (`from part import lower_tub as FAITHFUL`)
and applies 13 declared changes:
  - 4x additive M2.5 standoffs (`Z = 8.20 mm` datum, `RX-M2.5x4.0`) for the inverted Radxa X4
  - 1x additive internal **Wired-LED & Clear PETG Light-Pipe Holder Cradle** (`led_holder_cradle`)
    behind the central front apron (`Y = -42.50 .. -35.50 mm`), holding the rear optical barrel
    of `part/led_light_pipe.py` and snapping a wired `3 mm` red through-hole LED coaxially at
    `(0.0, -39.50, 8.24)`
  - 1x subtractive through-wall lenticular front Power LED lens aperture + collar seat
    (`front_led_bore`, `J-07`)
  - 4x subtractive rear `+Y` I/O apertures (`Micro-HDMI #1`, `USB-C + Micro-HDMI #2`, `3.5mm Audio`,
    and relocated `RJ45 Ethernet`)
  - Cooling exhaust (REQ-04): 9 floor vents behind the Bumpon feet gap, and the 28 waist louvers
    cut through

Verified against `DEVIATIONS` by `lib/testing/variant_manifest.py`.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402
from part import lower_tub as FAITHFUL  # noqa: E402
from part.shared import n64_contours as C  # noqa: E402
from standoffs import standoff  # noqa: E402

PROCESS = "fdm"
MANUFACTURE = "fdm"
PROFILE = "fdm_petg_x2d"  # process/profiles.py: allowances added at print time
PRINT_NORMAL = (0, 0, 1)
# 33 mm^2 measured by layers (2026-11-16), all reachable for removal: the rounded USB-C / HDMI /
# audio counterbore tops at the rear and the top of the front LED hole. The RJ45 opening now runs
# up to the split, so its old 12.3 mm roof is gone. PETG body, PLA interface (notes/PRINTING.md).
SUPPORT_MM2 = 40.0
VISIBLE_FACES = ("-X", "+X", "-Y", "+Y", "-Z")

DEVIATIONS = {
    "floor_vents": {
        "kind": "removed",
        "why": "9 through-floor exhaust slots (2x18 mm) behind the Bumpon feet gap (REQ-04)",
        "bbox": (-22.5, 21.5, -0.6, 14.5, 40.5, 2.2),
        "volume_mm3": 518.4,  # 9 x 2 x 18 x 1.6 mm floor (flush since C9)
        "tolerance_mm3": 5.0,
    },
    "waist_slots_l": {
        "kind": "removed",
        "why": "14 left waist louvers cut through wall + backing strip (REQ-04 exhaust)",
        "bbox": (-60.5, 2.5, 4.0, -56.5, 39.5, 11.0),
        "volume_mm3": 187.69,
        "tolerance_mm3": 3.0,
    },
    "waist_slots_r": {
        "kind": "removed",
        "why": "14 right waist louvers cut through wall + backing strip (REQ-04 exhaust)",
        "bbox": (56.5, 2.5, 4.0, 60.5, 39.5, 11.0),
        "volume_mm3": 187.69,
        "tolerance_mm3": 3.0,
    },
    "radxa_standoff_fl": {
        "kind": "added",
        "why": "Front-left M2.5 standoff (Z=8.2mm datum, RX-M2.5x4.0) for inverted Radxa X4 (J-02)",
        "bbox": (-48.5, -9.7, 1.5, -40.5, -1.7, 8.3),
        "volume_mm3": 213.84,
        "tolerance_mm3": 2.5,
    },
    "radxa_standoff_fr": {
        "kind": "added",
        "why": "Front-right M2.5 standoff (Z=8.2mm, RX-M2.5x4.0) for inverted Radxa X4 (J-02)",
        "bbox": (9.5, -9.7, 1.5, 17.5, -1.7, 8.3),
        "volume_mm3": 213.84,
        "tolerance_mm3": 2.5,
    },
    "radxa_standoff_rl": {
        "kind": "added",
        "why": "Rear-left M2.5 standoff (Z=8.2mm datum, RX-M2.5x4.0) for inverted Radxa X4 (J-02)",
        "bbox": (-48.5, 39.3, 1.5, -40.5, 47.3, 8.3),
        "volume_mm3": 213.84,
        "tolerance_mm3": 2.5,
    },
    "radxa_standoff_rr": {
        "kind": "added",
        "why": "Rear-right M2.5 standoff (Z=8.2mm datum, RX-M2.5x4.0) for inverted Radxa X4 (J-02)",
        "bbox": (9.5, 39.3, 1.5, 17.5, 47.3, 8.3),
        "volume_mm3": 213.84,
        "tolerance_mm3": 2.5,
    },
    "led_holder_cradle": {
        "kind": "added",
        "why": "Internal cradle holding Clear PETG light-pipe & wired 3mm red LED (J-07)",
        "bbox": (-5.6, -42.6, 1.5, 5.6, -35.4, 13.0),
        "volume_mm3": 681.53,
        "tolerance_mm3": 5.0,
    },
    "front_subasm_bosses_l": {
        "kind": "added",
        "why": "3x flat-top Z=5.00mm RX-M2.5x4.0 floor bosses for Left Front Subassembly (J-05)",
        "bbox": (-47.8, -36.2, 1.5, -2.2, -10.0, 5.5),
        "volume_mm3": 148.01,
        "tolerance_mm3": 5.0,
    },
    "front_subasm_bosses_r": {
        "kind": "added",
        "why": "3x flat-top Z=5.00mm RX-M2.5x4.0 floor bosses for Right Front Subassembly (J-05)",
        "bbox": (2.2, -36.2, 1.5, 47.8, -10.0, 5.5),
        "volume_mm3": 148.01,
        "tolerance_mm3": 5.0,
    },
    "front_subasm_bores_l": {
        "kind": "removed",
        "why": "Extend 3x Left Front Subassembly RX-M2.5x4.0 blind bores to Z=0.85mm (4.15mm deep)",
        "bbox": (-47.8, -36.2, 0.5, -2.2, -10.0, 1.7),
        "volume_mm3": 18.10,
        "tolerance_mm3": 2.5,
    },
    "front_subasm_bores_r": {
        "kind": "removed",
        "why": "Extend 3x Right Front Subassembly RX-M2.5x4.0 blind bores to Z=0.85mm (4.15mm)",
        "bbox": (2.2, -36.2, 0.5, 47.8, -10.0, 1.7),
        "volume_mm3": 18.10,
        "tolerance_mm3": 2.5,
    },
    "front_led_bore": {
        "kind": "removed",
        "why": "Through-wall lenticular Power LED lens aperture & collar pocket in apron (J-07)",
        "bbox": (-4.3, -46.8, 6.0, 4.3, -42.4, 10.5),
        "volume_mm3": 87.49,
        "tolerance_mm3": 3.0,
    },
    "rear_usbc_cutout": {
        "kind": "removed",
        "why": "Stepped USB-C 12V PD port + 12.8x6.8mm overmold counterbore at X=-36.78mm (REQ-05)",
        "bbox": (-43.5, 47.0, 3.0, -30.1, 49.8, 10.1),
        "volume_mm3": 107.37,
        "tolerance_mm3": 4.0,
    },
    "rear_hdmi1_blind_relief": {
        "kind": "removed",
        "why": "Blind internal relief pocket hiding unused 2nd Micro-HDMI at X=-21.99mm (REQ-05)",
        "bbox": (-25.8, 47.5, 4.8, -18.2, 48.2, 8.4),
        "volume_mm3": 7.45,
        "tolerance_mm3": 2.0,
    },
    "rear_hdmi_cutout": {
        "kind": "removed",
        "why": "Stepped Micro-HDMI port + 11.0x6.8mm overmold counterbore at X=-8.39mm (REQ-05)",
        "bbox": (-14.1, 46.8, 3.0, -2.6, 50.1, 10.1),
        "volume_mm3": 140.96,
        "tolerance_mm3": 5.0,
    },
    "rear_audio_cutout": {
        "kind": "removed",
        "why": "Stepped Ø6.60mm 3.5mm audio bore + Ø8.80x7.60mm overmold counterbore at X=+5.99mm",
        "bbox": (1.0, 47.7, 1.8, 11.0, 50.1, 10.2),
        "volume_mm3": 92.82,
        "tolerance_mm3": 4.0,
    },
}


def _led_holder_cradle_solid() -> cq.Shape:
    """Build the internal U-channel holder for the Clear PETG light-pipe & wired 3mm red LED."""
    block = cq.Solid.makeBox(
        10.8,
        7.0,
        D.SPLIT_Z - D.FLOOR_T,
        cq.Vector(-5.4, -42.50, D.FLOOR_T),
    )
    # Coaxial Ø3.40 mm 3mm-LED body cradle (Y = -39.50 .. -36.40 mm) + Ø4.20 mm rim seat
    led_body_bore = cq.Solid.makeCylinder(
        D.LED_3MM_BORE_D / 2.0,
        3.20,
        cq.Vector(0.0, -39.50, D.LED_PIPE_Z),
        cq.Vector(0.0, 1.0, 0.0),
    )
    led_rim_bore = cq.Solid.makeCylinder(
        2.10,
        1.30,
        cq.Vector(0.0, -36.60, D.LED_PIPE_Z),
        cq.Vector(0.0, 1.0, 0.0),
    )
    # Top wire-drop slot (2.20 mm wide) so pre-soldered LED leads drop in from +Z without threading
    wire_slot = cq.Solid.makeBox(
        2.20,
        4.30,
        6.00,
        cq.Vector(-1.10, -39.50, D.LED_PIPE_Z),
    )
    return block.cut(led_body_bore, led_rim_bore, wire_slot)


def _stadium_y(cx: float, cz: float, w: float, h: float, y0: float, dy: float) -> cq.Shape:
    """Horizontal stadium solid oriented along `+Y` (`y0 .. y0 + dy`) centred at `(cx, cz)`."""
    r = 0.5 * h
    dx = w - h
    return cq.Solid.makeBox(dx, dy, h, cq.Vector(cx - 0.5 * dx, y0, cz - r)).fuse(
        cq.Solid.makeCylinder(r, dy, cq.Vector(cx - 0.5 * dx, y0, cz), cq.Vector(0.0, 1.0, 0.0)),
        cq.Solid.makeCylinder(r, dy, cq.Vector(cx + 0.5 * dx, y0, cz), cq.Vector(0.0, 1.0, 0.0)),
    )


def _conical_boss(mx: float, my: float, r_boss: float = 2.80) -> cq.Shape:
    """Raised flat-top `RX-M2.5x4.0` boss in `lower_tub` (`Z = 1.60 .. 4.80 mm`), giving a flat
    `Z = 4.80 mm` horizontal datum seat for `front_io_carrier_l`/`_r`."""
    return cq.Solid.makeCylinder(
        r_boss,
        D.FRONT_SUBASM_BOSS_TOP_Z - (D.FLOOR_T - 0.5),
        cq.Vector(mx, my, D.FLOOR_T - 0.5),
    )


def _front_subasm_bosses() -> list[cq.Shape]:
    """6x flat-top `RX-M2.5x4.0` floor bosses (2 locating at R=2.80, 1 Z-clamp at R=2.42/side)."""
    out = []
    radii = (2.80, 2.80, 2.42)
    for side in (-1.0, 1.0):
        for (mx, my), r_b in zip(D.FRONT_SUBASM_MOUNT_PTS, radii):
            out.append(_conical_boss(side * mx, my, r_b))
    return out


def _front_subasm_bore_cutters() -> list[cq.Shape]:
    """6x `4.10 mm`-deep `RX-M2.5x4.0` blind bores (`Z = 0.70 .. 4.80 mm`, leaving `0.70 mm` solid
    floor underneath so `4.00 mm` Ruthex inserts seat flush and `M2.5 x 6` screws clear)."""
    z0 = D.FRONT_SUBASM_BOSS_BORE_Z0
    h = (D.FRONT_SUBASM_BOSS_TOP_Z + 0.10) - z0
    return [
        cq.Solid.makeCylinder(D.INSERT_M25_BORE_D / 2.0, h, cq.Vector(side * mx, my, z0))
        for side in (-1.0, 1.0)
        for mx, my in D.FRONT_SUBASM_MOUNT_PTS
    ]


def get_shape() -> cq.Shape:
    """Build the N64 Classic Mini Lower Tub variant from `part/lower_tub.py`."""
    base = FAITHFUL.get_shape()

    # 1. Additive 4x Radxa X4 M2.5 standoffs + LED cradle + RJ45 cradle + 6x Front bosses
    post_h = D.RADXA_STANDOFF_H + 0.5
    post_base = standoff(
        bore_dia=D.INSERT_M25_BORE_D,
        height=post_h,
        outer_dia=D.STANDOFF_M25_OD,
        bore_depth=D.INSERT_M25_DEPTH,
    )
    # The top steps in to the Ø6.4 contact face that clears Radxa's parts round the holes.
    z_step = post_h - D.RADXA_STANDOFF_TOP_H
    step_ring = cq.Solid.makeCylinder(D.STANDOFF_M25_OD, 1.0, cq.Vector(0, 0, z_step)).cut(
        cq.Solid.makeCylinder(D.RADXA_STANDOFF_TOP_D / 2.0, 1.0, cq.Vector(0, 0, z_step))
    )
    post_base = post_base.cut(step_ring)
    additions = (
        [
            post_base.moved(cq.Location(cq.Vector(hx, hy, D.FLOOR_T - 0.5)))
            for hx, hy in D.radxa_hole_centres()
        ]
        + [_led_holder_cradle_solid()]
        + _front_subasm_bosses()
    )
    with_posts = base.fuse(*additions)

    # 2. Subtractive through-wall lenticular front LED lens bore + continuous collar/guide slot
    #    (Y = -44.41 .. -39.35 mm across the Y = -42.50 mm pad/cradle junction, zero thin sliver!)
    y_collar0 = D.LED_PIPE_Y0 + 2.15  # -44.41 mm (0.15 mm ahead of y_flange0 = -44.26 mm)
    y_guide_end = -39.35  # 0.21 mm behind y_rear = -39.56 mm
    cuts = [
        C.n64_led_lens_prism(
            y0=D.FRONT_APRON_Y0 - 1.0,
            depth_y=3.50,
            clearance=D.LED_CLEAR,
            z_centre=D.LED_PIPE_Z,
        ),
        cq.Solid.makeBox(
            D.LED_FLANGE_W + 0.40,
            y_guide_end - y_collar0,
            D.LED_FLANGE_D + 0.40,
            cq.Vector(
                -(D.LED_FLANGE_W + 0.40) / 2.0,
                y_collar0,
                D.LED_PIPE_Z - (D.LED_FLANGE_D + 0.40) / 2.0,
            ),
        ),
    ]
    # 1. Stepped USB-C 12V PD cutout (9.54x3.60mm bore + 12.80x6.80mm overmold counterbore)
    cuts.append(
        _stadium_y(
            D.REAR_USBC_X, D.REAR_IO_Z_CENTRE, D.REAR_USBC_W, D.REAR_USBC_H, 45.20, 6.80
        ).fuse(_stadium_y(D.REAR_USBC_X, D.REAR_IO_Z_CENTRE, 12.80, 6.80, 48.40, 3.60))
    )
    # 2. Blind internal relief pocket for unused 2nd Micro-HDMI at X = -21.99 mm
    #    (stops at Y = 48.05 mm, leaving 1.69 mm solid exterior rear wall)
    cuts.append(
        cq.Solid.makeBox(
            7.20,
            2.85,
            3.30,
            cq.Vector(D.REAR_HDMI1_HIDDEN_X - 3.60, 45.20, 4.95),
        )
    )
    # 3. Stepped Micro-HDMI cutout (7.10x3.30mm bore + 11.00x6.80mm overmold counterbore)
    cuts.append(
        cq.Solid.makeBox(
            D.REAR_HDMI_W,
            6.80,
            D.REAR_HDMI_H,
            cq.Vector(
                D.REAR_HDMI_X - D.REAR_HDMI_W / 2.0,
                45.20,
                D.REAR_IO_Z_CENTRE - D.REAR_HDMI_H / 2.0,
            ),
        ).fuse(_stadium_y(D.REAR_HDMI_X, D.REAR_IO_Z_CENTRE, 11.00, 6.80, 48.15, 3.85))
    )
    # 4. Stepped 3.5mm audio jack bore (Ø6.60mm bore + 8.80x7.60mm overmold counterbore at Y=48.80)
    cuts.append(
        cq.Solid.makeCylinder(
            D.REAR_AUDIO_W / 2.0,
            6.80,
            cq.Vector(D.REAR_AUDIO_X, 45.20, 5.95),
            cq.Vector(0.0, 1.0, 0.0),
        ).fuse(_stadium_y(D.REAR_AUDIO_X, 5.95, 8.80, 7.60, 48.80, 3.20))
    )
    cuts.extend(_front_subasm_bore_cutters())
    cuts.extend(floor_vent_cutters())
    cuts.extend(waist_slot_cutters())
    return with_posts.cut(*cuts)


# Cooling exhaust (REQ-04): floor vents breathe through the gap under the Bumpon feet, clear of
# the M.2 SSD (X < -25.3), the standoffs and the duct's plenum ahead of the board.
FLOOR_SLOT_W, FLOOR_SLOT_L, FLOOR_SLOT_PITCH = 2.0, 18.0, 4.0
FLOOR_SLOT_XS = tuple(-22.0 + i * FLOOR_SLOT_PITCH for i in range(9))
FLOOR_SLOT_YS = (22.0,)  # slots run Y = 22..40, under the board (see above)
WAIST_SLOT_Y0, WAIST_SLOT_PITCH, WAIST_SLOT_W = 2.839, 2.60, 1.25
WAIST_SLOT_Z0, WAIST_SLOT_H = 4.25, 6.50
WAIST_CUT_X_IN = 56.9  # through the 2 mm wall and the louver backing strip behind it


def floor_vent_cutters() -> list[cq.Solid]:
    """Through-floor slots (2 x 18 mm), fed by the gap the Bumpon feet leave under the tub."""
    return [
        cq.Solid.makeBox(FLOOR_SLOT_W, FLOOR_SLOT_L, D.FLOOR_T + 1.0, cq.Vector(x, y, -0.5))
        for x in FLOOR_SLOT_XS
        for y in FLOOR_SLOT_YS
    ]


def waist_slot_cutters() -> list[cq.Solid]:
    """The 14 authentic waist louvers per side, cut through instead of recessed."""
    depth = D.WAIST_HALF_W + 0.2 - WAIST_CUT_X_IN
    out = []
    for i in range(14):
        sy = WAIST_SLOT_Y0 + i * WAIST_SLOT_PITCH
        for x0 in (-D.WAIST_HALF_W - 0.2, WAIST_CUT_X_IN):
            out.append(
                cq.Solid.makeBox(
                    depth, WAIST_SLOT_W, WAIST_SLOT_H, cq.Vector(x0, sy, WAIST_SLOT_Z0)
                )
            )
    return out
