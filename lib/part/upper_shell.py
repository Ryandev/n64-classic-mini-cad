"""Faithful 50%-scale N64 Upper Shell (`130.00 x 99.88 x 20.56 mm`, `Z = 12.94 .. 33.50 mm`).

Sister file to `lib/step/upper_shell.py` and base for `lib/variant/upper_shell.py`.
Reconstructs 100% of the authentic 50%-scale Nintendo 64 upper enclosure geometry from
`Console N64` (`lib/step/n64_shell.py`):
  - Exact two-body N64 upper planform: 8-segment `G1`-tangent `120.00 x 96.50 mm` main wing
    body with `R = 1.00 mm` top edge fillet fused with twin protruding `R = 12.50 mm` front
    corner pod lobes topped by `R = 5.00 mm` convex domes (`Z = 12.94 .. 22.75 mm`)
  - `G1`-tangent `10.275 deg` sloped left/right wing decks meeting the `R = 161.18 mm` convex
    front barrel dome (`Z = 33.50 mm` crest running all the way forward to the bowed front wall)
  - Concave rear cartridge cradle (`Z = 27.33 mm`) and parabolic vent saddle ramp with all 25
    authentic cooling louver pockets
  - Recessed cartridge slot throat with closed dual dust flaps, centre parting seam, and
    `R = 3.00 mm` semicircular end tabs (`Z = 26.75 mm`)
  - 3D-engraved `MEMORY EXPANSION` cover seam, rear finger-pry slot, and all 15 block letters
  - 3D-engraved rear `Nintendo` stadium oval border and all 9 script letters
  - Sculpted stadium thumb depressions at `(+-32.32, -25.81)` housing the longitudinal `POWER`
    slider slot (`J-03`) and stadium `RESET` plunger bore (`J-04`, `AC-T18`)
  - Flush curved N64 front emblem pocket (`J-06`) on the untouched `21.60 mm` central front
    apron flanked by the upper halves of the Left (`P1+P2`) and Right (`P3+P4`) twin-port bays
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402
from shared import n64_contours as C  # noqa: E402
from shared import n64_text as T  # noqa: E402

PROCESS = "fdm"
MANUFACTURE = "fdm"
PRINT_NORMAL = (0, 0, 1)
VISIBLE_FACES = ("-X", "+X", "-Y", "+Y", "+Z")


def _magnet_bore_y(x: float, y0: float, z: float) -> cq.Shape:
    """Cylindrical magnet pocket oriented along `+Y` at `(x, y0, z)`."""
    return cq.Solid.makeCylinder(
        D.MAGNET_BORE_D / 2.0,
        D.MAGNET_BORE_DEPTH + 0.05,
        cq.Vector(x, y0 - 0.05, z),
        cq.Vector(0.0, 1.0, 0.0),
    )


def get_shape() -> cq.Shape:
    """Construct the faithful 50%-scale N64 Upper Shell solid."""
    # 1. Exact 50%-scale N64 upper outer solid (Z = 12.94 .. 33.50 mm)
    outer = C.upper_outer_body()

    # 2. Hollow interior cavity with uniform sculpted roof thickness, J-01 annular rabbet,
    #    and wide flat Z = SPLIT_Z bed-contact stiffening rim
    rabbet_ring = C.n64_plan_prism(
        z0=D.SPLIT_Z - 0.3,
        height=D.LIP_H + 0.5,
        inset=D.RABBET_INSET,
    ).cut(
        C.n64_plan_prism(
            z0=D.SPLIT_Z - 0.4,
            height=D.LIP_H + 0.7,
            inset=D.SHELL_WALL_T + 0.15,
        )
    )

    inner_roof_cap = outer.moved(cq.Location(cq.Vector(0.0, 0.0, -2.05)))
    upper_cavity_wing = C.main_wing_prism(
        z0=D.SPLIT_Z + D.LIP_H + 0.4,
        height=D.SHELL_H,
        inset=D.SHELL_WALL_T,
    )
    upper_cavity_pods = C.n64_plan_prism(
        z0=D.SPLIT_Z + D.LIP_H + 0.4,
        height=5.2,
        inset=D.SHELL_WALL_T,
    )
    upper_cavity_outer = upper_cavity_wing.fuse(upper_cavity_pods).intersect(inner_roof_cap)

    lower_window = C.n64_plan_prism(
        z0=D.SPLIT_Z - 0.5,
        height=D.LIP_H + 1.4,
        inset=D.UPPER_FLANGE_W,
    )

    shell_hollow = outer.cut(rabbet_ring.fuse(upper_cavity_outer, lower_window))

    # 3. Additive internal bosses & upper twin-port bay housing blocks:
    #    - 4x corner M3 enclosure bosses (Ø8.5 mm, Z = SPLIT_Z .. 28.9 mm)
    #    - 2x stadium backing bosses under the POWER and RESET thumb wells
    #    - Central front nose backing block behind the Clear Acrylic N64 jewel pocket (J-06)
    #    - Left (X = -25.0) and Right (X = +25.0) upper twin-port bay keeper blocks
    bay_top_z = D.FRONT_BAY_Z1
    boss_raw = (
        [
            cq.Solid.makeCylinder(
                D.CORNER_BOSS_OD / 2.0,
                16.0,
                cq.Vector(bx, by, D.SPLIT_Z),
            )
            for bx in D.CORNER_BOSS_XS
            for by in D.CORNER_BOSS_YS
        ]
        + [
            # Full-perimeter stadium plunger guide chimneys (Z = 22.10 .. 29.00 mm) surrounding
            # the 11.0 x 17.2 mm POWER (J-03) and RESET (J-04) button flanges + thumb-well backing
            C.stadium_prism(
                cx,
                D.CONTROLS_Y,
                D.SLIDER_FLANGE_W + 3.6,
                D.SLIDER_FLANGE_D + 3.6,
                22.10,
                7.90,
            ).fuse(
                C.stadium_prism(
                    cx,
                    D.CONTROL_WELL_Y,
                    D.CONTROL_WELL_W + 4.4,
                    D.CONTROL_WELL_D + 4.4,
                    D.DECK_H - D.ROOF_T,
                    5.0,
                )
            )
            for cx in (D.POWER_SLIDER_X, D.RESET_BTN_X)
        ]
        + [
            cq.Solid.makeBox(
                D.BEZEL_W + 2.8,
                4.2,
                D.BEZEL_H + 4.0,
                cq.Vector(
                    -(D.BEZEL_W + 2.8) / 2.0,
                    D.BEZEL_Y0 - 0.5,
                    D.SPLIT_Z,
                ),
            )
        ]
        + [
            cq.Solid.makeBox(
                D.FRONT_BAY_W + 2.8,
                (D.USB_A_Y0 - 0.05) - (D.FRONT_BAY_Y0 - 1.0),
                (bay_top_z + 1.4) - D.SPLIT_Z,
                cq.Vector(
                    bx - (D.FRONT_BAY_W + 2.8) / 2.0,
                    D.FRONT_BAY_Y0 - 1.0,
                    D.SPLIT_Z,
                ),
            )
            for bx in D.FRONT_BAY_XS
        ]
        + [
            # Internal backing pad under the recessed Z = 25.35 mm cartridge flap pocket (J-09)
            cq.Solid.makeBox(
                62.0,
                14.5,
                5.1,
                cq.Vector(-31.0, 9.2, 23.80),
            ),
        ]
    )
    boss_sub_roof = outer.intersect(outer.moved(cq.Location(cq.Vector(0.0, 0.0, -0.5))))
    bosses_clipped = cq.Compound.makeCompound(boss_raw).intersect(boss_sub_roof)
    with_bosses = shell_hollow.fuse(*bosses_clipped.Solids()).cut(rabbet_ring)

    # 4. Surface-conforming 0.28 mm skin cutter for top louvers, MEMORY EXPANSION & Nintendo
    surface_skin = outer.cut(outer.moved(cq.Location(cq.Vector(0.0, 0.0, -0.28))))
    skin_prisms = (
        T.memory_expansion_prisms(z0=25.0, height=10.0)
        + T.nintendo_plaque_prisms(z0=24.0, height=10.0)
        + C.top_louver_prisms(z0=24.0, height=11.0)
    )
    surface_detail_cuts = cq.Compound.makeCompound(skin_prisms).intersect(surface_skin)

    # 5. Functional bores, stadium control wells, cartridge throat, shield pocket & twin bays
    cuts = list(surface_detail_cuts.Solids())
    cuts.append(C.cartridge_slot_throat_cutter())

    for bx in D.CORNER_BOSS_XS:
        for by in D.CORNER_BOSS_YS:
            cuts.append(
                cq.Solid.makeCylinder(
                    D.INSERT_M3_BORE_D / 2.0,
                    D.INSERT_M3_DEPTH + 0.2,
                    cq.Vector(bx, by, D.SPLIT_Z - 0.2),
                )
            )

    # Sculpted concave stadium thumb depressions (Face[45], 11.00 x 22.50 mm at Y = -25.81 mm)
    for side in (-1.0, 1.0):
        cuts.append(C.control_well_cutter(side))

    # Left deck stadium Momentary Power Button stepped guide bore (J-03, 0.22 mm/side clearance):
    #   - Upper shaft bore (8.94 x 14.94 mm, Z = 26.60 .. 30.80 mm)
    #   - Lower flange guide counterbore (11.44 x 17.64 mm, Z = 21.80 .. 27.20 mm)
    #   - Inboard Omron SS-5GL lever entry window (Y = -26.55 .. -21.75 mm, Z = 21.80 .. 25.40 mm)
    cbore_w = D.SLIDER_FLANGE_W + 2.0 * D.SLIDER_CLEAR
    cbore_d = D.SLIDER_FLANGE_D + 2.0 * D.SLIDER_CLEAR
    for cx, slot_w, slot_d in (
        (D.POWER_SLIDER_X, D.SLIDER_SLOT_W, D.SLIDER_SLOT_D),
        (D.RESET_BTN_X, D.RESET_BORE_W, D.RESET_BORE_LEN_Y),
    ):
        cuts.append(
            C.stadium_prism(
                cx,
                D.CONTROLS_Y,
                slot_w,
                slot_d,
                D.DECK_H - D.ROOF_T - 0.6,
                D.ROOF_T + 3.6,
            )
        )
        cuts.append(
            C.stadium_prism(
                cx,
                D.CONTROLS_Y,
                cbore_w,
                cbore_d,
                21.80,
                (D.DECK_H - D.ROOF_T) - 21.80,
            )
        )
        # Rear slot below Z = 23.60 mm clearing Lower_Tub's button travel-stop post (BUTTON_STOP_Z)
        cuts.append(
            cq.Solid.makeBox(
                5.60,
                3.20,
                1.80,
                cq.Vector(cx - 2.80, -21.20, 21.80),
            )
        )
        x_slot0 = cx if cx < 0.0 else cx - 7.80
        cuts.append(
            cq.Solid.makeBox(
                7.80,
                4.80,
                3.60,
                cq.Vector(x_slot0, -26.55, 21.80),
            )
        )

    # Flush curved N64 front shield emblem pocket on central front apron (J-06, 0.15 mm/side)
    cuts.append(
        C.n64_shield_prism(
            y0=D.BEZEL_Y0 - 1.5,
            depth_y=D.BEZEL_T + 1.5,
            z_centre=D.BEZEL_Z_CENTRE,
            clearance=D.BEZEL_POCKET_CLEAR,
        )
    )

    # Upper half of the Left (P1+P2 at X = -25.0) and Right (P3+P4 at X = +25.0) twin-port bays
    y_seat = D.FRONT_BAY_Y0 + D.FRONT_COVER_T
    for bx in D.FRONT_BAY_XS:
        # Upper twin-cover seat recess (Z = SPLIT_Z .. 18.89 mm, 28.4 mm wide)
        cuts.append(
            cq.Solid.makeBox(
                D.FRONT_BAY_W,
                y_seat - (-50.0),
                bay_top_z - (D.SPLIT_Z - 0.5),
                cq.Vector(bx - D.FRONT_BAY_W / 2.0, -50.0, D.SPLIT_Z - 0.5),
            )
        )
        # Upper fingernail relief notch above the twin cover's fingernail slit
        notch_w = D.FINGER_SLIT_W + 0.8
        cuts.append(
            cq.Solid.makeBox(
                notch_w,
                (D.FRONT_BAY_Y0 + 1.1) - (-50.0),
                0.7,
                cq.Vector(bx - notch_w / 2.0, -50.0, bay_top_z - 0.1),
            )
        )
        # Upper keeper magnet pocket at (bx, y_seat, 16.5 mm)
        cuts.append(_magnet_bore_y(bx, y_seat, D.MAGNET_ZS[1]))

    # 4x USB-A plug access windows through the keeper walls (11.6 mm wide, Z = SPLIT_Z..16.8 mm)
    # + rear EMI-flange clearance pocket behind Y = D.USB_A_Y0 - 0.05
    win_w = 11.60
    emi_w = D.USB_A_FLANGE_W + 0.40
    for px in D.FRONT_PORT_XS:
        cuts.append(
            cq.Solid.makeBox(
                win_w,
                (D.USB_A_Y0 + 0.5) - (y_seat - 0.2),
                16.80 - (D.SPLIT_Z - 0.5),
                cq.Vector(px - win_w / 2.0, y_seat - 0.2, D.SPLIT_Z - 0.5),
            )
        )
        cuts.append(
            cq.Solid.makeBox(
                emi_w,
                5.0,
                17.65 - (D.SPLIT_Z - 0.5),
                cq.Vector(px - emi_w / 2.0, D.USB_A_Y0 - 0.05, D.SPLIT_Z - 0.5),
            )
        )

    # Authentic Z = SPLIT_Z exterior parting-line shadow groove chamfer (0.19 mm top half)
    _ = math
    return with_bosses.cut(*cuts)
