"""Faithful 50%-scale N64 Lower Tub (`130.00 x 99.88 x 14.74 mm`, `Z = 0.00 .. SPLIT_Z + LIP_H`).

Sister file to `lib/step/lower_tub.py` and base for `lib/variant/lower_tub.py`.
Reconstructs the authentic 50%-scale Nintendo 64 lower chassis from analytic primitives
measured off `Console N64` (`lib/step/n64_shell.py`):
  - Exact 10-segment N64 planform (`130.00 x 99.88 mm`): twin protruding `R = 12.50 mm` front
    cylindrical pods, bowed recessed `R = 721.25 mm` front controller apron (`Y = -46.56 mm`),
    tapered flanks into `120.00 mm` waist (`X = +-60.00`), `R = 10.00 mm` rear corners, and
    bowed `R = 1200.75 mm` rear wall (`Y = +49.94 mm`)
  - Stepped underside (`Z = 0.00 .. 0.90 mm`) with 4 bevelled circular N64 corner feet + central
    bottom specification plaque pad (`>= 18%` flat `Z = 0` bed contact, zero overhang)
  - Crisp exterior parting-line shadow groove (`Z = 12.56 .. 12.94 mm`) + `J-01` locating lip
  - 14 vertical recessed N64 cooling louver grooves along both `-X` and `+X` waist side walls
    (`Y = 2.84 .. 37.89 mm`, `Z = 4.25 .. 10.75 mm`, matching `Face[1832..1915]`)
  - Untouched `21.60 mm` central front apron (`X = -10.80 .. +10.80 mm`) carrying the authentic
    `6.36 x 1.76 mm` horizontal lenticular Power LED lens outline (`Face[1823]`, `Z = 8.24 mm`)
  - Lower halves of the Left (`P1+P2` at `X = -25.0`) and Right (`P3+P4` at `X = +25.0`) twin
    controller bays (`Z = 4.99 .. 12.94 mm`) with coaxial bottom pivot sockets (`Z = 6.09 mm`),
    lower USB-A access windows, and lower keeper magnet pockets (`J-05`)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402
from shared import n64_contours as C  # noqa: E402

PROCESS = "fdm"
MANUFACTURE = "fdm"
PRINT_NORMAL = (0, 0, 1)
VISIBLE_FACES = ("-X", "+X", "-Y", "+Y", "-Z")


def get_shape() -> cq.Shape:
    """Construct the faithful 50%-scale N64 Lower Tub solid."""
    foot_step_h = 0.90

    # 1. Main N64 outer tub body (Z = foot_step_h .. SPLIT_Z) + stepped inset under-chassis
    upper_body = C.n64_plan_prism(z0=foot_step_h, height=D.SPLIT_Z - foot_step_h, inset=0.0)
    under_skirt = C.n64_plan_prism(z0=0.45, height=0.65, inset=1.6)

    # 4x circular N64 corner feet (45-deg bevelled cones on Z = 0.0) + central spec-plate pad
    feet_and_pad = [
        cq.Solid.makeCone(
            10.6, 11.6, foot_step_h + 0.2, cq.Vector(-D.FRONT_POD_X, D.FRONT_POD_Y, 0.0)
        ),
        cq.Solid.makeCone(
            10.6, 11.6, foot_step_h + 0.2, cq.Vector(D.FRONT_POD_X, D.FRONT_POD_Y, 0.0)
        ),
        cq.Solid.makeCone(
            8.2, 9.2, foot_step_h + 0.2, cq.Vector(-D.REAR_CORNER_X, D.REAR_CORNER_Y, 0.0)
        ),
        cq.Solid.makeCone(
            8.2, 9.2, foot_step_h + 0.2, cq.Vector(D.REAR_CORNER_X, D.REAR_CORNER_Y, 0.0)
        ),
        C.stadium_prism(0.0, 2.0, 42.0, 34.0, 0.0, foot_step_h + 0.2),
    ]
    full_plan_clip = C.n64_plan_prism(z0=-0.1, height=D.SPLIT_Z + D.LIP_H + 1.0, inset=0.0)
    feet_clipped = cq.Compound.makeCompound(feet_and_pad).intersect(full_plan_clip)

    # J-01 inner perimeter locating lip (inset = 1.15 .. 2.00 mm, Z = SPLIT_Z .. SPLIT_Z + LIP_H)
    lip = C.n64_plan_prism(
        z0=D.SPLIT_Z - 0.5,
        height=D.LIP_H + 0.5,
        inset=D.LIP_OUTER_INSET,
    )

    # Hollow interior cavity above Z = FLOOR_T (1.60 mm)
    cavity = C.n64_plan_prism(
        z0=D.FLOOR_T,
        height=D.SPLIT_Z + D.LIP_H + 1.0,
        inset=D.SHELL_WALL_T,
    )

    tub_shell = upper_body.fuse(under_skirt, *feet_clipped.Solids(), lip).cut(cavity)

    # 2. Internal louver backing ribs + twin-bay keeper blocks + central LED boss + M3 bosses
    add_solids = [
        cq.Solid.makeCylinder(
            D.CORNER_BOSS_OD / 2.0,
            D.SPLIT_Z - 1.0,
            cq.Vector(bx, by, 1.0),
        )
        for bx in D.CORNER_BOSS_XS
        for by in D.CORNER_BOSS_YS
    ]
    # Waist louver backing strips (X = +-57.2 .. +-58.6, Y = 1.5 .. 38.8, Z = FLOOR_T .. 11.4)
    for sx in (-1.0, 1.0):
        x0 = -D.WAIST_HALF_W + 1.4 if sx < 0 else D.WAIST_HALF_W - 2.8
        add_solids.append(cq.Solid.makeBox(1.4, 37.3, 9.8, cq.Vector(x0, 1.5, D.FLOOR_T)))

    # Left (X = -25.0) and Right (X = +25.0) lower twin-port bay keeper blocks +
    # full-depth 4-sided USB-A mounting cradles (Y = -41.75 .. -25.25 mm, Z = FLOOR_T .. SPLIT_Z)
    y_keeper_back = D.USB_A_Y0 - 0.05  # -41.75 mm (clears TE 292303-7 front flange at -41.70 mm)
    front_raw_blocks = [
        cq.Solid.makeBox(
            D.FRONT_BAY_W + 3.6,
            y_keeper_back - (D.FRONT_BAY_Y0 - 1.5),
            D.SPLIT_Z - D.FLOOR_T,
            cq.Vector(
                bx - (D.FRONT_BAY_W + 3.6) / 2.0,
                D.FRONT_BAY_Y0 - 1.5,
                D.FLOOR_T,
            ),
        ).fuse(
            # Full-depth Z = 9.55 mm seating floor under the pair of TE 292303-7 USB-A receptacles
            cq.Solid.makeBox(
                D.FRONT_BAY_W + 3.6,
                15.95,
                9.55 - D.FLOOR_T,
                cq.Vector(
                    bx - (D.FRONT_BAY_W + 3.6) / 2.0,
                    y_keeper_back,
                    D.FLOOR_T,
                ),
            ),
            # Stepped Z = 10.80 mm front metal-shell seating shelf (Y = -40.80 .. -32.35 mm)
            # that supports the Z = 10.95 mm front shell floor and aligns flush with the
            # Y = -32.35 mm retention-leg slot wall to form a continuous 5.00 mm tall -Y pull stop
            cq.Solid.makeBox(
                D.FRONT_BAY_W + 3.6,
                8.45,
                10.80 - 9.55,
                cq.Vector(
                    bx - (D.FRONT_BAY_W + 3.6) / 2.0,
                    -40.80,
                    9.55,
                ),
            ),
            # Central divider wall + 3.10mm front registration shoulder (Y=-39.80..-36.70, Z=12.94)
            # and flat Z=11.55mm glue shelf (Y=-36.70..-25.80) for part/usb_retainer_bracket.py
            cq.Solid.makeBox(1.70, 14.00, 2.00, cq.Vector(bx - 0.85, -39.80, 9.55)),
            cq.Solid.makeBox(1.70, 3.10, D.SPLIT_Z - 11.55, cq.Vector(bx - 0.85, -39.80, 11.55)),
            # Left and right lateral guide walls (1.50 mm thick) for each twin USB-A cradle
            cq.Solid.makeBox(1.50, 14.00, 2.00, cq.Vector(bx - 15.80, -39.80, 9.55)),
            cq.Solid.makeBox(1.50, 3.10, D.SPLIT_Z - 11.55, cq.Vector(bx - 15.80, -39.80, 11.55)),
            cq.Solid.makeBox(1.50, 14.00, 2.00, cq.Vector(bx + 14.30, -39.80, 9.55)),
            cq.Solid.makeBox(1.50, 3.10, D.SPLIT_Z - 11.55, cq.Vector(bx + 14.30, -39.80, 11.55)),
            # Rear plug-insertion backstop wall (0.85 mm thick, Y = -26.65 .. -25.80 mm)
            cq.Solid.makeBox(
                D.FRONT_BAY_W + 3.6,
                0.85,
                2.00,
                cq.Vector(bx - (D.FRONT_BAY_W + 3.6) / 2.0, -26.65, 9.55),
            ),
        )
        for bx in D.FRONT_BAY_XS
    ] + [
        # Central front apron backing pad behind the lenticular Power LED lens (X = -5.4..+5.4)
        cq.Solid.makeBox(
            10.8,
            (-42.50) - (D.FRONT_APRON_Y0 - 1.0),
            D.SPLIT_Z - D.FLOOR_T,
            cq.Vector(-5.4, D.FRONT_APRON_Y0 - 1.0, D.FLOOR_T),
        ),
        # Internal rear I/O bezel boss around Micro-HDMI #2 (X = -14.80..-1.90, Y = 47.00..48.20)
        cq.Solid.makeBox(
            12.90,
            1.20,
            10.60 - D.FLOOR_T,
            cq.Vector(-14.80, 47.00, D.FLOOR_T),
        ),
    ]
    front_clipped = cq.Compound.makeCompound(front_raw_blocks).intersect(
        C.n64_plan_prism(z0=D.FLOOR_T, height=D.SPLIT_Z - D.FLOOR_T, inset=0.0)
    )
    add_solids.extend(front_clipped.Solids())

    tub_with_bosses = tub_shell.fuse(*add_solids)

    # 3. Subtractive features:
    #    - Authentic Z = 12.56 .. 12.94 mm exterior parting shadow groove
    #    - 14x per side vertical N64 waist cooling louver grooves (Y = 2.84 .. 37.89 mm)
    #    - 4x corner M3 counterbores (J-01)
    #    - Shallow lenticular front Power LED lens outline on central front apron (Face[1823])
    #    - Left & Right lower twin-port bays + bottom hinge sockets + USB windows + magnets (J-05)
    cuts = []

    groove_ring = C.n64_plan_prism(
        z0=D.SPLIT_Z - D.PARTING_GROOVE_H,
        height=D.PARTING_GROOVE_H + 0.10,
        inset=-0.2,
    ).cut(
        C.n64_plan_prism(
            z0=D.SPLIT_Z - D.PARTING_GROOVE_H - 0.10,
            height=D.PARTING_GROOVE_H + 0.30,
            inset=0.30,
        )
    )
    cuts.append(groove_ring)

    # 14 vertical side cooling louver slots per side along X = +-60.00 mm (Face[1832..1915])
    slot_w_y = 1.25
    slot_depth_x = 1.15
    slot_z0 = 4.25
    slot_h_z = 6.50
    for i in range(14):
        sy = 2.839 + i * 2.60
        cuts.append(
            cq.Solid.makeBox(
                slot_depth_x + 0.2,
                slot_w_y,
                slot_h_z,
                cq.Vector(-D.WAIST_HALF_W - 0.2, sy, slot_z0),
            )
        )
        cuts.append(
            cq.Solid.makeBox(
                slot_depth_x + 0.2,
                slot_w_y,
                slot_h_z,
                cq.Vector(D.WAIST_HALF_W - slot_depth_x, sy, slot_z0),
            )
        )

    # 4x stepped M3 clearance + socket-head counterbores
    stepped_bolt_cutter = cq.Solid.makeCylinder(
        D.M3_CLEAR_D / 2.0,
        D.SPLIT_Z + D.LIP_H + 1.0,
        cq.Vector(0.0, 0.0, D.M3_CBORE_H - 0.2),
    ).fuse(
        cq.Solid.makeCylinder(
            D.M3_CBORE_D / 2.0,
            D.M3_CBORE_H + 0.4,
            cq.Vector(0.0, 0.0, -0.2),
        )
    )
    for bx in D.CORNER_BOSS_XS:
        for by in D.CORNER_BOSS_YS:
            cuts.append(stepped_bolt_cutter.moved(cq.Location(cq.Vector(bx, by, 0.0))))

    # Shallow cosmetic outline of the lenticular N64 Power LED lens on the faithful shell
    cuts.append(
        C.n64_led_lens_prism(
            y0=D.FRONT_APRON_Y0 - 1.0,
            depth_y=1.35,
            clearance=D.LED_CLEAR,
            z_centre=D.LED_PIPE_Z,
        )
    )

    # Lower half of Left (P1+P2 at X = -25.0) and Right (P3+P4 at X = +25.0) twin-port bays
    z_bay0 = D.FRONT_BAY_Z0
    y_seat = D.FRONT_BAY_Y0 + D.FRONT_COVER_T  # -44.12 mm
    for bx in D.FRONT_BAY_XS:
        cuts.append(
            cq.Solid.makeBox(
                D.FRONT_BAY_W,
                y_seat - (-50.0),
                (D.SPLIT_Z + D.LIP_H + 0.5) - z_bay0,
                cq.Vector(bx - D.FRONT_BAY_W / 2.0, -50.0, z_bay0),
            )
        )
        # Trim the J-01 locating lip (Z >= SPLIT_Z) across the open front twin-port bay
        cuts.append(
            cq.Solid.makeBox(
                D.FRONT_BAY_W + 2.8,
                8.0,
                D.LIP_H + 1.0,
                cq.Vector(bx - (D.FRONT_BAY_W + 2.8) / 2.0, -50.0, D.SPLIT_Z),
            )
        )
        # Coaxial bottom hinge pivot sockets in outer and inner cheeks of each twin bay
        for side in (-1.0, 1.0):
            sx = bx + side * (D.FRONT_BAY_W / 2.0 - 0.2)
            cuts.append(
                cq.Solid.makeCylinder(
                    D.HINGE_SOCKET_D / 2.0,
                    D.HINGE_SOCKET_DEPTH + 0.2,
                    cq.Vector(sx, D.HINGE_Y, D.HINGE_Z),
                    cq.Vector(side, 0.0, 0.0),
                )
            )
        # Lower keeper magnet pocket at (bx, y_seat, 9.90 mm)
        cuts.append(
            cq.Solid.makeCylinder(
                D.MAGNET_BORE_D / 2.0,
                D.MAGNET_BORE_DEPTH + 0.05,
                cq.Vector(bx, y_seat - 0.05, D.MAGNET_ZS[0]),
                cq.Vector(0.0, 1.0, 0.0),
            )
        )

    # 4x lower USB-A plug access windows through the keeper walls (11.6 mm wide, Z = 9.75..14.9)
    # + downward PCB retention kink-leg lock slots (Y = -32.45..-30.00, Z = 5.80..9.65)
    # + central rear wire-exit notch through the Y = -26.25 mm backstop wall
    win_w = 11.60
    for px in D.FRONT_PORT_XS:
        cuts.append(
            cq.Solid.makeBox(
                win_w,
                6.0,
                (D.SPLIT_Z + D.LIP_H + 0.5) - 9.75,
                cq.Vector(px - win_w / 2.0, y_seat - 0.2, 9.75),
            )
        )
        for side in (-1.0, 1.0):
            x_leg0 = px + 6.00 if side > 0.0 else px - 8.80
            cuts.append(cq.Solid.makeBox(2.80, 2.35, 3.85, cq.Vector(x_leg0, -32.35, 5.80)))
        cuts.append(cq.Solid.makeBox(8.60, 1.50, 2.50, cq.Vector(px - 4.30, -26.80, 9.55)))

    return tub_with_bosses.cut(*cuts)
