"""50%-scale N64 Twin-Port Hinged Front Controller Cover (`front_port_cover.py`, `J-05`).

Charcoal Grey bottom-hinged, magnet-latched twin-port front controller cover
(`28.0 x 13.5 x 1.8 mm`, `2` instances per console: Left `P1+P2` at `X = -25.0 mm` and Right
`P3+P4` at `X = +25.0 mm`) seated at the authentic N64 controller port centreline
(`Z = 13.19 mm`, straddling `SPLIT_Z = 12.94 mm`) with `0.20 mm/side` XZ clearance (`J-05`).
Features:
  - Leaves the `21.60 mm` central front apron (`X = -10.80 .. +10.80 mm`), flush Clear Acrylic
    N64 jewel, and horizontal lenticular red Power LED lens 100% untouched authentic N64 shell
  - Hinge knuckle along the bottom edge (`Ø3.4 mm`, bored `Ø1.8 mm`) turning on the steel
    hinge pins (`HINGE_PIN_*`) held in `lower_tub`'s bay walls (doors + bezels clear `0..90 deg`)
  - Continuous `Z = 12.56 .. 12.94 mm` exterior parting-line shadow groove across the front face
  - Top-centre fingernail slit (`6.4 x 1.1 x 0.9 mm`) to flip down each twin cover and reveal
    its pair of horizontal `TE Connectivity 292303-7` USB-A receptacles
  - 2x rear magnet pockets (`Ø3.2 mm` with self-supporting conical tips at `Z = 9.9, 16.5 mm`)
    mating with the central keeper pillar of each twin bay (`8` magnets total across 2 covers)
  - 2x shallow circular locating pockets (`Ø8.2 x 0.45 mm`) + 3 top cooling fin notches above
    each port receiving the glued-on `n64_port_insert` parts (`J-08`)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402

PROCESS = "fdm"
MANUFACTURE = "fdm"
PROFILE = "fdm_petg_x2d"  # process/profiles.py: allowances added at print time
# Printed front face down (2026-11-17): the hinge knuckle stands proud of the back, so the back
# can't sit on the bed; the visible face takes the bed's flat finish instead.
PRINT_NORMAL = (0, 1, 0)
VISIBLE_FACES = ("-Y",)


def cover_at(bay_x: float = D.FRONT_BAY_X) -> cq.Shape:
    """Build one twin-port (`P1+P2` or `P3+P4`) hinged front controller cover at `bay_x`."""
    w = D.FRONT_BAY_W - 2.0 * D.FRONT_COVER_CLEAR
    h = D.FRONT_BAY_H - 2.0 * D.FRONT_COVER_CLEAR
    t = D.FRONT_COVER_T - 0.2  # 1.8 mm
    y_front = D.FRONT_BAY_Y0  # -46.12 mm
    y_back = y_front + t  # -44.32 mm
    z0 = D.FRONT_BAY_Z0 + D.FRONT_COVER_CLEAR

    plate = cq.Solid.makeBox(
        w,
        t,
        h,
        cq.Vector(bay_x - w / 2.0, y_front, z0),
    )

    # Hinge knuckle along the bottom edge (J-05): a round rib of HINGE_KNUCKLE_R about the pivot,
    # bored for the steel pins. Below the pivot the door is cut to that same radius, so nothing
    # of it sweeps lower than its bottom edge as it opens (the sill clears it at any angle).
    r = D.HINGE_KNUCKLE_R
    axis_x0 = bay_x - w / 2.0 - 0.1
    keep = cq.Solid.makeBox(
        w + 0.2, t + 2.0 * r, h, cq.Vector(axis_x0, y_front - r, D.HINGE_Z)
    ).fuse(
        cq.Solid.makeCylinder(
            r, w + 0.2, cq.Vector(axis_x0, D.HINGE_Y, D.HINGE_Z), cq.Vector(1.0, 0.0, 0.0)
        )
    )
    # trimmed to the front face: the round would otherwise touch it along a line, a hair proud
    knuckle = cq.Solid.makeCylinder(
        r, w, cq.Vector(bay_x - w / 2.0, D.HINGE_Y, D.HINGE_Z), cq.Vector(1.0, 0.0, 0.0)
    ).intersect(cq.Solid.makeBox(w, 2.0 * r, 2.0 * r, cq.Vector(bay_x - w / 2.0, y_front, z0)))
    body = plate.intersect(keep).fuse(knuckle)

    cuts = [
        cq.Solid.makeCylinder(
            D.HINGE_BORE_D / 2.0,
            w + 0.2,
            cq.Vector(axis_x0, D.HINGE_Y, D.HINGE_Z),
            cq.Vector(1.0, 0.0, 0.0),
        )
    ]

    # 2. Continuous Z = 12.56 .. 12.94 mm parting-line shadow groove across the -Y face
    cuts.append(
        cq.Solid.makeBox(
            w + 0.4,
            0.35,
            D.PARTING_GROOVE_H,
            cq.Vector(bay_x - w / 2.0 - 0.2, y_front - 0.1, D.SPLIT_Z - D.PARTING_GROOVE_H),
        )
    )

    # 3. 2x shallow circular locating pockets on -Y + 3 top cooling fin notches above each port
    port_xs = (
        (D.PORT_INSERT_XS[0], D.PORT_INSERT_XS[1])
        if bay_x < 0.0
        else (D.PORT_INSERT_XS[2], D.PORT_INSERT_XS[3])
    )
    for px in port_xs:
        cuts.append(
            cq.Solid.makeCylinder(
                D.PORT_POCKET_D / 2.0,
                D.PORT_POCKET_DEPTH + 0.2,
                cq.Vector(px, y_front - 0.2, D.USB_A_Z_CENTRE),
                cq.Vector(0.0, 1.0, 0.0),
            )
        )
        for dx_fin in (-2.0, 0.0, 2.0):
            cuts.append(
                cq.Solid.makeBox(
                    0.90,
                    0.45,
                    1.15,
                    cq.Vector(px + dx_fin - 0.45, y_front - 0.1, z0 + h - 1.35),
                )
            )

    # 4. Top-centre fingernail slit along the -Y/+Z top edge to flip open the twin cover
    cuts.append(
        cq.Solid.makeBox(
            D.FINGER_SLIT_W,
            D.FINGER_SLIT_D + 0.2,
            D.FINGER_SLIT_H + 0.2,
            cq.Vector(
                bay_x - D.FINGER_SLIT_W / 2.0,
                y_front - 0.2,
                z0 + h - D.FINGER_SLIT_H,
            ),
        )
    )

    # 5. 2x rear magnet pockets on +Y at X = bay_x with 45-degree conical tips (zero overhang)
    cyl_d = 0.55
    cone_h = 0.40
    for mz in D.MAGNET_ZS:
        cyl = cq.Solid.makeCylinder(
            D.MAGNET_BORE_D / 2.0,
            cyl_d + 0.1,
            cq.Vector(bay_x, y_back + 0.1, mz),
            cq.Vector(0.0, -1.0, 0.0),
        )
        cone = cq.Solid.makeCone(
            D.MAGNET_BORE_D / 2.0,
            0.0,
            cone_h,
            cq.Vector(bay_x, y_back - cyl_d, mz),
            cq.Vector(0.0, -1.0, 0.0),
        )
        cuts.extend([cyl, cone])

    return body.cut(*cuts)


def get_shape() -> cq.Shape:
    """Build the canonical Left (`P1+P2` at `X = -25.0 mm`) twin-port hinged cover."""
    return cover_at(D.FRONT_BAY_X)
