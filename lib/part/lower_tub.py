"""Faithful 50%-scale N64 Lower Tub (`130.00 x 99.88 x 14.74 mm`, `Z = 0.00 .. SPLIT_Z + LIP_H`).

Sister file to `lib/step/lower_tub.py` and base for `lib/variant/lower_tub.py`.
Reconstructs the authentic 50%-scale Nintendo 64 lower chassis from analytic primitives
measured off `Console N64` (`lib/step/n64_shell.py`):
  - Exact 10-segment N64 planform (`130.00 x 99.88 mm`): twin protruding `R = 12.50 mm` front
    cylindrical pods, bowed recessed `R = 721.25 mm` front controller apron (`Y = -46.56 mm`),
    tapered flanks into `120.00 mm` waist (`X = +-60.00`), `R = 10.00 mm` rear corners, and
    bowed `R = 1200.75 mm` rear wall (`Y = +49.94 mm`)
  - Flat underside at `Z = 0` (the whole bottom is the bed face; the original's stepped feet and
    label pad are hidden under the Bumpon feet, so they were dropped for printing, C9)
  - Crisp exterior parting-line shadow groove (`Z = 12.56 .. 12.94 mm`) + `J-01` locating lip
  - 14 vertical recessed N64 cooling louver grooves along both `-X` and `+X` waist side walls
    (`Y = 2.84 .. 37.89 mm`, `Z = 4.25 .. 10.75 mm`, matching `Face[1832..1915]`)
  - Untouched `21.60 mm` central front apron (`X = -10.80 .. +10.80 mm`) carrying the authentic
    `6.36 x 1.76 mm` horizontal lenticular Power LED lens outline (`Face[1823]`, `Z = 8.24 mm`)
  - Lower halves of the Left (`P1+P2` at `X = -25.0`) and Right (`P3+P4` at `X = +25.0`) twin
    controller bays (`Z = 4.99 .. 12.94 mm`) with coaxial bottom pivot sockets (`Z = 6.09 mm`),
    lower USB-A access windows, and lower keeper magnet pockets (`J-05`)
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402
from process import printable  # noqa: E402
from shared import n64_contours as C  # noqa: E402

PROCESS = "fdm"
MANUFACTURE = "fdm"
PROFILE = "fdm_petg_x2d"  # process/profiles.py: allowances added at print time
PRINT_NORMAL = (0, 0, 1)
VISIBLE_FACES = ("-X", "+X", "-Y", "+Y", "-Z")


def _outward(bay_x: float) -> float:
    """+1 or -1: the direction from a bay towards the console's side (its outer wall)."""
    return -1.0 if bay_x < 0.0 else 1.0


def _flush_strip_xs(bx: float) -> tuple[float, float]:
    """X span of the strip beside a bay's outer end that is brought flush with the door."""
    side = _outward(bx)
    edge = bx + side * D.FRONT_BAY_W / 2.0
    lo, hi = sorted((edge, edge + side * D.FRONT_BAY_FLUSH_W))
    return lo, hi


def _hinge_wall_blocks() -> list[cq.Shape]:
    """Material each door hinge needs in the outer bay wall (J-05, owner 2026-11-17).

    Beside each door's outer end the N64 front curves back 0.7 mm behind the door face, which left
    0.13 mm in front of the hinge pin: that strip is brought forward flush with the door (the shell
    does the same above the split). A block round the pin hole carries it out to the hollow front
    corner the pins are pushed in from.
    """
    out = []
    for bx in D.FRONT_BAY_XS:
        side = _outward(bx)
        edge = bx + side * D.FRONT_BAY_W / 2.0
        x0, x1 = _flush_strip_xs(bx)
        out.append(cq.Solid.makeBox(x1 - x0, 1.1, D.SPLIT_Z, cq.Vector(x0, D.FRONT_BAY_Y0, 0.0)))
        # a block round the pin hole from the bay wall out to where the pins go in
        px0, px1 = sorted((edge + side * 1.0, edge + side * D.HINGE_OUTER_WALL))
        # it stands on the floor, so it prints without support
        r = D.HINGE_PRESS_D / 2.0 + 0.85
        out.append(
            cq.Solid.makeBox(
                px1 - px0,
                D.HINGE_Y + r + 0.5 - (D.FRONT_BAY_Y0 + 0.1),
                D.HINGE_Z + r - D.FLOOR_T,
                cq.Vector(px0, D.FRONT_BAY_Y0 + 0.1, D.FLOOR_T),
            )
        )
    return out


def _hinge_cuts(bx: float) -> list[cq.Shape]:
    """The bay's hinge holes and the groove the door's knuckle turns in (J-05)."""
    side = _outward(bx)
    half = D.FRONT_BAY_W / 2.0
    along = cq.Vector(1.0, 0.0, 0.0)
    return [
        # blind hole in the inner wall: the end of the pin train turns in it
        cq.Solid.makeCylinder(
            D.HINGE_BORE_D / 2.0,
            D.HINGE_BLIND_DEPTH + 0.2,
            cq.Vector(bx - side * (half - 0.2), D.HINGE_Y, D.HINGE_Z),
            -side * along,
        ),
        # through the outer wall into the hollow corner: the pins go in here, the last pressed
        cq.Solid.makeCylinder(
            D.HINGE_PRESS_D / 2.0,
            D.HINGE_OUTER_WALL + 1.0,
            cq.Vector(bx + side * (half - 0.2), D.HINGE_Y, D.HINGE_Z),
            side * along,
        ),
        # the knuckle turns in this groove through the ledge behind the door
        _teardrop(D.HINGE_KNUCKLE_R + D.HINGE_LEDGE_CLEAR, bx - half, D.FRONT_BAY_W),
    ]


def _teardrop(r: float, x0: float, length: float) -> cq.Shape:
    """A round groove along X on the hinge axis with a 45 deg peaked roof, so it prints.

    A round roof open to the front is held only from behind, so its top read as needing support
    (8.5 mm^2 a door, 2026-11-17). The peak is the standard fix for a horizontal hole.
    """
    centre = cq.Vector(x0, D.HINGE_Y, D.HINGE_Z)
    along = cq.Vector(1.0, 0.0, 0.0)
    roof = (
        cq.Solid.makeBox(length, 2.0 * r, 2.0 * r, cq.Vector(x0, D.HINGE_Y - r, D.HINGE_Z - r))
        .rotate(centre, centre + along, 45.0)
        .intersect(
            cq.Solid.makeBox(
                length, 4.0 * r, 2.0 * r, cq.Vector(x0, D.HINGE_Y - 2.0 * r, D.HINGE_Z)
            )
        )
    )
    return cq.Solid.makeCylinder(r, length, centre, along).fuse(roof)


def get_shape() -> cq.Shape:
    """Construct the faithful 50%-scale N64 Lower Tub solid."""
    # 1. Main outer tub body, flat-bottomed from Z = 0 (C9, owner 2026-11-13). The original's
    #    stepped underside (raised corner feet and label pad, floor 0.45-0.9 mm up) left 9,500 mm^2
    #    of floor printing in mid-air; the underside is hidden under the Bumpon feet and the owner
    #    only replicates what is visible, so the whole bottom is now the bed face (BED_FLAT).
    upper_body = C.n64_plan_prism(z0=0.0, height=D.SPLIT_Z, inset=0.0)

    # J-01 locating lip (owner's joint, 2026-11-16): it stands inside the shell's wall line,
    # LIP_IN0 .. LIP_IN0 + LIP_T in from the outside, from a ledge on the wall's inner face. The
    # ledge steps out 0.2 mm per 0.2 mm layer (45 deg) so it prints without support.
    def ring(z0: float, height: float, outer: float, inner: float) -> cq.Shape:
        return C.n64_plan_prism(z0=z0, height=height, inset=outer).cut(
            C.n64_plan_prism(z0=z0 - 0.1, height=height + 0.2, inset=inner)
        )

    lip_in1 = D.LIP_IN0 + D.LIP_T
    z_ledge = D.SPLIT_Z - D.LIP_LEDGE_DROP
    lip_parts = [
        ring(z_ledge, D.LIP_LEDGE_DROP, D.SHELL_WALL_T - 0.01, lip_in1),
        ring(D.SPLIT_Z - 0.01, D.LIP_H + 0.01, D.LIP_IN0, lip_in1),
    ]
    step = 0.2
    k = 1
    while lip_in1 - step * k > D.SHELL_WALL_T + 1e-6:
        lip_parts.append(
            ring(z_ledge - step * k, step + 0.01, D.SHELL_WALL_T - 0.01, lip_in1 - step * k)
        )
        k += 1

    # No lip across the front port bays, where the doors sit (cut from the lip alone)
    gaps = [
        cq.Solid.makeBox(x1 - x0, y1 - y0, 40.0, cq.Vector(x0, y0, -5.0))
        for x0, x1, y0, y1 in D.lip_gaps()
    ]
    lip_parts = [p.cut(*gaps) for p in lip_parts]

    # Hollow interior cavity above Z = FLOOR_T (1.60 mm)
    cavity = C.n64_plan_prism(
        z0=D.FLOOR_T,
        height=D.SPLIT_Z + D.LIP_H + 1.0,
        inset=D.SHELL_WALL_T,
    )

    tub_shell = upper_body.cut(cavity).fuse(*lip_parts)

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
    add_solids.extend(_hinge_wall_blocks())

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
    # the flush strips beside the doors' outer ends get their own groove on their face (below)
    groove_ring = groove_ring.cut(
        *[
            cq.Solid.makeBox(
                x1 - x0, 3.0, 2.0, cq.Vector(x0, D.FRONT_BAY_Y0 - 0.5, D.SPLIT_Z - 1.0)
            )
            for x0, x1 in map(_flush_strip_xs, D.FRONT_BAY_XS)
        ]
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

    # 4x stepped M3 clearance + socket-head counterbores. The counterbore opens on the bed, so
    # its roof is closed by the two-layer bridge: one layer leaves a slot the hole's width across
    # the counterbore (two bridges along the slot), the next a square (two short bridges across
    # it), then the round hole. A plain roof is a ring round the hole held only at its rim, which
    # the overhang row fails (coupon plate 1 lesson, 2026-11-14).
    layer = printable.LAYER_MM
    z_roof = math.ceil((D.M3_CBORE_H + 0.2) / layer - 1e-9) * layer  # on a layer line: 3.8
    clear = D.M3_CLEAR_D
    stepped_bolt_cutter = cq.Solid.makeCylinder(
        D.M3_CBORE_D / 2.0,
        z_roof + 0.2,
        cq.Vector(0.0, 0.0, -0.2),
    ).fuse(
        # the slot only spans the counterbore: its square corners poked 0.35 mm into the boss
        # wall and left it 0.69 mm for that layer (NECK, 2026-11-15)
        cq.Solid.makeBox(
            D.M3_CBORE_D, clear, layer, cq.Vector(-D.M3_CBORE_D / 2.0, -clear / 2.0, z_roof)
        ).intersect(cq.Solid.makeCylinder(D.M3_CBORE_D / 2.0, layer, cq.Vector(0, 0, z_roof))),
        cq.Solid.makeBox(
            clear, clear, layer, cq.Vector(-clear / 2.0, -clear / 2.0, z_roof + layer)
        ),
        cq.Solid.makeCylinder(
            clear / 2.0,
            D.SPLIT_Z + D.LIP_H + 1.0,
            cq.Vector(0.0, 0.0, z_roof + 2.0 * layer),
        ),
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
        cuts.extend(_hinge_cuts(bx))
        # the parting groove along the flush strip's face, 0.3 mm deep like the ring's
        gx0, gx1 = _flush_strip_xs(bx)
        cuts.append(
            cq.Solid.makeBox(
                gx1 - gx0,
                0.5,
                D.PARTING_GROOVE_H + 0.10,
                cq.Vector(gx0, D.FRONT_BAY_Y0 - 0.2, D.SPLIT_Z - D.PARTING_GROOVE_H),
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
