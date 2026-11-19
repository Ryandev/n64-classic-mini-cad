"""Left (`P1+P2 / Power`) Removable Front Control & I/O Carrier (`front_io_carrier_l.py`).

Printed upright (`PRINT_NORMAL = (0, 0, 1)`, zero support) on its flat `Z = 2.80 mm` bottom plane.
Assembled on the bench with:
  - Left twin-port hinged controller door (`part/front_port_cover.py`) and a single continuous
    `Ø1.5 x 27.4 mm` steel hinge pin through the carrier's two 360-deg stationary hinge barrels
    inside the 28.40 mm bay opening (through-bored at both ends for bench disassembly)
  - 2x `TE Connectivity 292303-7` horizontal USB-A receptacles seated on the stepped `Z = 10.80 /
    9.55 mm` floor with downward kink-leg lock slots and `8.40 x 4.50 mm` through-floor solder-pin
    bays + rear `8.40 x 6.00 mm` open-bottom wire-exit arches (`USB_WIRING`)
  - Left `Omron SS-5GL` hinge-lever microswitch screwed into the integrated rear switch tower from
    behind on the bench (`2x M2.5 x 10 mm` screws, `OMRON_SCREW`) + integral rear button stop post
  - Left `part/usb_retainer_bracket.py` clamping bridge + `part/power_slider.py` button sleeve

Seats flat at `Z = 5.00 mm` on `3x` `RX-M2.5x4.0` floor bosses in `lower_tub` (`Outer-Front` at
`(-43.80, -32.20)`, `Inner-Rear` at `(-6.40, -30.20)`, and `Rear-Tower` at `(-25.00, -15.50)`).
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402
from part.shared import n64_contours as C  # noqa: E402
from process import printable  # noqa: E402

PROCESS = "fdm"
MANUFACTURE = "fdm"
PROFILE = "fdm_petg_x2d"
PRINT_NORMAL = (0, 0, 1)
VISIBLE_FACES = ()


def _corbel_prism_x(
    x_root: float, x_tip: float, y0: float, dy: float, z0: float, z1: float
) -> cq.Shape:
    """Box from `x_root` to `x_tip` whose underside slopes upward at 45 deg from `(x_root, z0)`."""
    lo, hi = sorted((x_root, x_tip))
    w = hi - lo
    box = cq.Solid.makeBox(w, dy, z1 - z0, cq.Vector(lo, y0, z0))
    pts = [
        (x_root, z0 - 0.1),
        (x_tip, z0 - 0.1),
        (x_tip, z0 + w),
    ]
    wire = cq.Wire.makePolygon([cq.Vector(x, y0 - 0.1, z) for x, z in pts + [pts[0]]])
    cutter = cq.Solid.extrudeLinear(cq.Face.makeFromWires(wire), cq.Vector(0, dy + 0.2, 0))
    return box.cut(cutter)


def _cheek_solid(x0: float, dx: float, y_back: float, base_z0: float) -> cq.Shape:
    """Side cheek sitting behind `lower_tub`'s full-thickness front shell wall (`Y = -44.48 mm`),
    with `0.13 mm` clearance (`y_front = -44.35 mm`) so the shell wall guides the carrier."""
    y_front = -44.35
    return cq.Solid.makeBox(
        dx, y_back - y_front, D.SPLIT_Z - base_z0, cq.Vector(x0, y_front, base_z0)
    )


def _hinge_barrel(x0: float, width: float, y_back: float, base_z0: float) -> cq.Shape:
    """360-deg stationary hinge barrel (`R = 1.65 mm` around `(HINGE_Y, HINGE_Z)`) with a 45-deg
    self-supporting foot down to `(y_bed, base_z0)` so it prints support-free on `Z = 2.80 mm`."""
    hy, hz = D.HINGE_Y, D.HINGE_Z
    r_bar = D.HINGE_BARREL_R
    y_tan = hy - r_bar / math.sqrt(2.0)
    z_tan = hz - r_bar / math.sqrt(2.0)
    y_bed = y_tan + (z_tan - base_z0)
    pts = [
        (y_bed, base_z0),
        (y_tan, z_tan),
        (hy, hz + r_bar),
        (y_back, hz + r_bar),
        (y_back, base_z0),
    ]
    wire = cq.Wire.makePolygon([cq.Vector(x0, y, z) for y, z in pts + [pts[0]]])
    foot = cq.Solid.extrudeLinear(cq.Face.makeFromWires(wire), cq.Vector(width, 0.0, 0.0))
    cyl = cq.Solid.makeCylinder(r_bar, width, cq.Vector(x0, hy, hz), cq.Vector(1.0, 0.0, 0.0))
    # Trim the tiny 0.005 mm^3 bottom-front tip below Z = 3.55 mm in front of Y = -44.45 mm so it
    # clears lower_tub's untouched sill with 0.0000 mm^3 collision.
    sill_trim = cq.Solid.makeBox(
        width + 0.2, 2.0, 3.55 - base_z0, cq.Vector(x0 - 0.1, -46.45, base_z0)
    )
    return cyl.fuse(foot).cut(sill_trim)


def _stepped_ear_socket(mx: float, my: float, r_cbore: float, base_z0: float) -> cq.Shape:
    """Flat-ceiling counterbore socket at `z_roof = D.FRONT_SUBASM_BOSS_TOP_Z = 5.00 mm` closed by
    the self-supporting two-layer bridge (`Z = 5.00..5.40 mm`) + `Ø2.70 mm` M2.5 bolt hole."""
    layer = printable.LAYER_MM
    z_roof = D.FRONT_SUBASM_BOSS_TOP_Z
    d_cbore = 2.0 * r_cbore
    clear = 2.70
    return cq.Solid.makeCylinder(
        r_cbore, z_roof - (base_z0 - 0.10), cq.Vector(mx, my, base_z0 - 0.10)
    ).fuse(
        cq.Solid.makeBox(
            d_cbore, clear, layer, cq.Vector(mx - r_cbore, my - clear / 2.0, z_roof)
        ).intersect(cq.Solid.makeCylinder(r_cbore, layer, cq.Vector(mx, my, z_roof))),
        cq.Solid.makeBox(
            clear, clear, layer, cq.Vector(mx - clear / 2.0, my - clear / 2.0, z_roof + layer)
        ),
        cq.Solid.makeCylinder(clear / 2.0, 15.0, cq.Vector(mx, my, z_roof + 2.0 * layer)),
    )


def carrier_at(side_sign: float = -1.0) -> cq.Shape:
    """Build the Left (`side_sign = -1.0`) or Right (`side_sign = +1.0`) Front I/O Carrier Base."""
    base_z0 = D.FRONT_SUBASM_BASE_Z0
    bx = side_sign * 25.0
    cx = side_sign * 32.32
    y_keeper_back = D.USB_A_Y0 - 0.05  # -41.75 mm
    y_seat = D.FRONT_BAY_Y0 + D.FRONT_COVER_T  # -44.12 mm

    mount_pts = [(side_sign * mx, my) for mx, my in D.FRONT_SUBASM_MOUNT_PTS]

    cheek_l = _cheek_solid(
        bx - D.FRONT_BAY_W / 2.0 - D.HINGE_CHEEK_T, D.HINGE_CHEEK_T, y_keeper_back, base_z0
    )
    cheek_r = _cheek_solid(bx + D.FRONT_BAY_W / 2.0, D.HINGE_CHEEK_T, y_keeper_back, base_z0)
    keeper_upper = cq.Solid.makeBox(
        31.60,
        y_keeper_back - y_seat,
        D.SPLIT_Z - 9.50,
        cq.Vector(bx - 15.80, y_seat, 9.50),
    )
    usb_floor = cq.Solid.makeBox(
        31.60,
        (-25.80) - y_seat,
        9.55 - base_z0,
        cq.Vector(bx - 15.80, y_seat, base_z0),
    )
    # Central bridge between the USB block and switch tower: 6.20 mm wide x 3.20 mm tall spine
    # (|X| = 22.20..28.40, Z = 2.80..6.00) clears both the Omron COM/NO leads and all 16 downward
    # USB solder pins & wires (at |X| <= 21.45 and |X| >= 28.55).
    col_x0 = -28.40 if side_sign < 0.0 else 22.20
    rib_mid = cq.Solid.makeBox(
        6.20,
        (-16.80) - (-30.50),
        6.00 - base_z0,
        cq.Vector(col_x0, -30.50, base_z0),
    ).fuse(
        cq.Solid.makeBox(
            3.60,
            (-25.80) - (-30.50),
            9.55 - base_z0,
            cq.Vector(bx - 1.80, -30.50, base_z0),
        ),
    )
    usb_front_step = cq.Solid.makeBox(
        31.60,
        8.45,
        10.80 - 9.55,
        cq.Vector(bx - 15.80, -40.80, 9.55),
    )
    walls = [
        cq.Solid.makeBox(1.70, 14.00, 2.00, cq.Vector(bx - 0.85, -39.80, 9.55)),
        cq.Solid.makeBox(1.70, 3.10, D.SPLIT_Z - 11.55, cq.Vector(bx - 0.85, -39.80, 11.55)),
        cq.Solid.makeBox(1.50, 14.00, 2.00, cq.Vector(bx - 15.80, -39.80, 9.55)),
        cq.Solid.makeBox(1.50, 3.10, D.SPLIT_Z - 11.55, cq.Vector(bx - 15.80, -39.80, 11.55)),
        cq.Solid.makeBox(1.50, 14.00, 2.00, cq.Vector(bx + 14.30, -39.80, 9.55)),
        cq.Solid.makeBox(1.50, 3.10, D.SPLIT_Z - 11.55, cq.Vector(bx + 14.30, -39.80, 11.55)),
        cq.Solid.makeBox(4.50, 1.40, 2.00, cq.Vector(bx - 2.25, -27.20, 9.55)),
        cq.Solid.makeBox(3.20, 1.40, 2.00, cq.Vector(bx - 15.80, -27.20, 9.55)),
        cq.Solid.makeBox(3.20, 1.40, 2.00, cq.Vector(bx + 12.60, -27.20, 9.55)),
    ]
    omron_tower = cq.Solid.makeBox(
        6.20, 4.0, 17.80 - base_z0, cq.Vector(col_x0, -20.80, base_z0)
    ).fuse(
        _corbel_prism_x(side_sign * 28.40, side_sign * 37.60, -20.80, 4.0, 4.65, 17.80),
        _corbel_prism_x(side_sign * 22.20, side_sign * 21.50, -20.80, 4.0, 10.50, 17.80),
        cq.Solid.makeBox(
            5.00,
            4.0,
            D.BUTTON_STOP_Z - 17.50,
            cq.Vector(cx - 2.50, -20.80, 17.50),
        ),
    )
    ear_hs = (8.40 - base_z0, 7.30 - base_z0, 7.30 - base_z0)
    ear_rs = (4.80, 4.80, 3.50)
    ears = [
        cq.Solid.makeCylinder(er, eh, cq.Vector(mx, my, base_z0))
        for (mx, my), eh, er in zip(mount_pts, ear_hs, ear_rs)
    ]
    ear_bridges = [
        cq.Solid.makeBox(
            4.0,
            9.60,
            ear_hs[0],
            cq.Vector(-43.80 if side_sign < 0.0 else 39.80, -32.20 - 4.80, base_z0),
        ),
        cq.Solid.makeBox(
            4.0,
            9.60,
            ear_hs[1],
            cq.Vector(-10.40 if side_sign < 0.0 else 6.40, -30.20 - 4.80, base_z0),
        ),
        cq.Solid.makeBox(6.20, 4.0, ear_hs[2], cq.Vector(col_x0, -18.50, base_z0)),
    ]
    carrier = keeper_upper.fuse(
        usb_floor,
        cheek_l,
        cheek_r,
        rib_mid,
        usb_front_step,
        omron_tower,
        *walls,
        *ears,
        *ear_bridges,
    )

    # First carve the front bay door seat & knuckle groove before fusing the two 360-deg
    # stationary hinge barrels at the ends of the 27.40 mm door width.
    r_mag = D.MAGNET_BORE_D / 2.0
    cz_mag = D.MAGNET_ZS[0]
    mag_center = cq.Vector(bx, y_seat - 0.05, cz_mag)
    mag_along = cq.Vector(0.0, 1.0, 0.0)
    # True 45-deg tangent roof (width strictly 2*r_mag = 3.20 mm in X so it never thins the
    # adjacent keeper pillar wall beside the USB windows).
    mag_pts = [
        (bx - r_mag, cz_mag),
        (bx, cz_mag + r_mag * math.sqrt(2.0)),
        (bx + r_mag, cz_mag),
    ]
    mag_wire = cq.Wire.makePolygon(
        [cq.Vector(x, y_seat - 0.05, z) for x, z in mag_pts + [mag_pts[0]]]
    )
    mag_roof = cq.Solid.extrudeLinear(
        cq.Face.makeFromWires(mag_wire), cq.Vector(0.0, D.MAGNET_BORE_DEPTH + 0.05, 0.0)
    )
    pre_cuts = [
        cq.Solid.makeBox(
            D.FRONT_BAY_W,
            y_seat - (-50.0),
            20.0,
            cq.Vector(bx - D.FRONT_BAY_W / 2.0, -50.0, D.FRONT_BAY_Z0),
        ),
        C.hinge_teardrop(
            D.HINGE_KNUCKLE_R + D.HINGE_LEDGE_CLEAR,
            bx - D.FRONT_BAY_W / 2.0,
            D.FRONT_BAY_W,
        ),
        cq.Solid.makeCylinder(r_mag, D.MAGNET_BORE_DEPTH + 0.05, mag_center, mag_along).fuse(
            mag_roof
        ),
    ]
    carrier = carrier.cut(*pre_cuts)

    # Fuse the two stationary 360-deg hinge barrels inside the 28.40 mm bay opening:
    w_door = D.FRONT_BAY_W - 2.0 * D.FRONT_COVER_CLEAR  # 27.40 mm
    x_bar_l = bx - w_door / 2.0
    x_bar_r = bx + w_door / 2.0 - D.HINGE_BARREL_W
    bar_l = _hinge_barrel(x_bar_l, D.HINGE_BARREL_W, y_keeper_back, base_z0)
    bar_r = _hinge_barrel(x_bar_r, D.HINGE_BARREL_W, y_keeper_back, base_z0)
    carrier = carrier.fuse(bar_l, bar_r)

    x_out_bar = x_bar_l if side_sign < 0.0 else x_bar_r
    x_in_bar = x_bar_r if side_sign < 0.0 else x_bar_l
    along = cq.Vector(1.0, 0.0, 0.0)
    carrier_cuts = [
        # Outer barrel: Ø1.50 mm line-to-line press fit
        cq.Solid.makeCylinder(
            D.HINGE_PRESS_D / 2.0,
            D.HINGE_BARREL_W + 0.20,
            cq.Vector(x_out_bar - 0.10, D.HINGE_Y, D.HINGE_Z),
            along,
        ),
        # Inner barrel: Ø1.60 mm close-fit journal
        cq.Solid.makeCylinder(
            D.HINGE_INNER_BORE_D / 2.0,
            D.HINGE_BARREL_W + 0.20,
            cq.Vector(x_in_bar - 0.10, D.HINGE_Y, D.HINGE_Z),
            along,
        ),
        # Through-access grooves across the side cheeks past both ends of the 27.40 mm pin so a
        # pin punch can push the pin straight through from either end on the bench.
        C.hinge_teardrop(0.85, bx - D.FRONT_BAY_W / 2.0 - D.HINGE_CHEEK_T - 0.5, 3.0),
        C.hinge_teardrop(0.85, bx + w_door / 2.0 + 0.02, 3.0),
    ]

    port_xs = D.FRONT_PORT_XS[:2] if side_sign < 0.0 else D.FRONT_PORT_XS[2:]
    for px in port_xs:
        # Keep the keeper pillar between P1 and P2 at full 5.00 mm width (|X - bx| <= 2.50 mm)
        # below Z = 11.40 mm around the Ø3.20 mm magnet pocket (0.90 mm side wall!), then open
        # to the full 11.60 mm USB-A window from Z = 10.80 mm behind the magnet pocket.
        carrier_cuts.append(
            cq.Solid.makeBox(10.20, 3.0, 10.0, cq.Vector(px - 5.10, y_seat - 0.2, 10.80))
        )
        carrier_cuts.append(
            cq.Solid.makeBox(11.60, 6.0, 10.0, cq.Vector(px - 5.80, y_seat - 0.2, 11.50))
        )
        carrier_cuts.append(cq.Solid.makeBox(11.60, 6.0, 10.0, cq.Vector(px - 5.80, -42.75, 9.75)))
        for s in (-1.0, 1.0):
            inboard = (px < bx and s > 0.0) or (px > bx and s < 0.0)
            w_leg = 2.80 if inboard else 1.70
            x_leg0 = px + 6.00 if s > 0.0 else px - 6.00 - w_leg
            carrier_cuts.append(
                cq.Solid.makeBox(w_leg, 2.35, 3.85, cq.Vector(x_leg0, -32.35, 5.80))
            )
        w_bay = D.USB_SOLDER_BAY_W
        carrier_cuts.append(
            cq.Solid.makeBox(w_bay, 4.50, 10.00, cq.Vector(px - w_bay / 2.0, -30.00, 2.00))
        )
    omron_screw_xs = (-33.73, -24.23) if side_sign < 0.0 else (24.23, 33.73)
    for x_m2 in omron_screw_xs:
        carrier_cuts.append(
            cq.Solid.makeCylinder(
                D.OMRON_SCREW_CLEAR_D / 2.0,
                6.0,
                cq.Vector(x_m2, -21.50, D.OMRON_HOLE_Z),
                cq.Vector(0, 1, 0),
            )
        )
    # Outer-Front and Inner-Rear sockets locate in XY (R_cbore = 2.95 around R_boss = 2.80 ->
    # 0.15 mm/side); Rear-Tower socket has R_cbore = 2.65 around R_boss = 2.42 (0.23 mm/side)
    # so only one locating pair constrains XY (Rule 3), while all 3 seat flat at Z = 5.00 mm.
    cbore_radii = (2.95, 2.95, 2.65)
    for (mx, my), r_cb in zip(mount_pts, cbore_radii):
        carrier_cuts.append(_stepped_ear_socket(mx, my, r_cb, base_z0))
    carrier_cuts.append(
        cq.Solid.makeBox(14.0, 6.0, 10.0, cq.Vector(side_sign * 25.00 - 7.0, -11.65, 0.0))
    )
    x_in_lop = -2.55 if side_sign < 0.0 else -3.45
    carrier_cuts.append(cq.Solid.makeBox(6.0, 14.0, 10.0, cq.Vector(x_in_lop, -37.0, 0.0)))
    return carrier.cut(*carrier_cuts)


def get_shape() -> cq.Shape:
    """Return the Left (`P1+P2 / Power`, `X = -25.0 mm`) Front Control & I/O Carrier solid."""
    return carrier_at(-1.0)
