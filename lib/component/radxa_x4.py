"""Parametric reference solids and keepouts for the Radxa X4 SBC and I/O connectors.

Dimensions from the Radxa X4 mechanical specification (`85.0 x 56.0 mm`, `4x Ø2.7 mm`
mounting holes on a `58.0 x 49.0 mm` rectangle), wired directly to the `lib/step/` ->
`lib/variant/` pipeline (`variant/radxa_x4.py`); the SoC heat sink is the bought
Same Sky HSB26-343408 (`component/hsb26_343408.py`).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import assembly_positions as AP  # noqa: E402
import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402
from component import hsb26_343408 as _heatsink  # noqa: E402
from step import usb_a_te_292303_7 as _usb_a_step  # noqa: E402
from variant import radxa_x4 as _radxa_variant  # noqa: E402

# Tall through-hole connectors stripped in `lib/variant/radxa_x4.py` from `lib/step/radxa_x4.py`
# (console-frame bounding boxes when inverted at RADXA_PCB_Z0 = 8.6 mm)
STRIPPED_HEADERS: dict[str, dict[str, object]] = {
    "usb3_dual_stack": {
        "step_solid_idx": 0,
        "bbox": (17.76, 15.03, -7.60, 35.22, 30.70, 11.80),
        "volume_mm3": 2452.38,
    },
    "usb2_dual_stack": {
        "step_solid_idx": 1,
        "bbox": (17.76, -3.49, -7.60, 35.22, 12.18, 11.80),
        "volume_mm3": 2452.38,
    },
    "rj45_ethernet_tower": {
        "step_solid_idx": 2,
        "bbox": (14.51, -22.47, -5.00, 35.76, -6.24, 12.30),
        "volume_mm3": 3634.77,
    },
    "poe_4pin_header": {
        "step_solid_idx": 47,
        "bbox": (6.40, -17.38, 1.10, 11.48, -12.30, 10.60),
        "volume_mm3": 68.07,
    },
    "fan_2pin_header": {
        "step_solid_idx": 357,
        "bbox": (-36.01, 27.95, 1.10, -30.93, 30.49, 10.60),
        "volume_mm3": 34.04,
    },
    "gpio_40pin_header": {
        "step_solid_idx": 361,
        "bbox": (-45.62, -24.85, -1.05, 5.18, -17.15, 8.60),
        "volume_mm3": 676.92,
    },
}


def vendor_step_compound() -> cq.Shape:
    """De-ported Radxa X4 v1.11 STEP (23 solids from `variant/radxa_x4.py`) in console coords."""
    return _radxa_variant.placed()


def heatsink_solid() -> cq.Shape:
    """Bought Same Sky HSB26-343408 pin-fin heat sink seated on the N100, in console coords."""
    return _heatsink.placed()


def board_solid() -> cq.Shape:
    """Placed Radxa X4 PCB (`85.0 x 56.0 x 1.6 mm` with `4x Ø2.7 mm` mounting holes)."""
    bb = D.radxa_bbox()
    x0, _ = bb["x"]
    y0, _ = bb["y"]
    z0, _ = bb["z"]

    pcb = cq.Solid.makeBox(D.RADXA_W, D.RADXA_D, D.RADXA_PCB_T, cq.Vector(x0, y0, z0))
    holes = [
        cq.Solid.makeCylinder(
            D.RADXA_HOLE_D / 2.0,
            D.RADXA_PCB_T + 0.4,
            cq.Vector(hx, hy, z0 - 0.2),
        )
        for hx, hy in D.radxa_hole_centres()
    ]
    return pcb.cut(cq.Compound.makeCompound(holes))


def m2_keepout() -> cq.Shape:
    """Underside M.2 2230 NVMe socket + SSD keepout (`22.0 x 30.0 x 5.53 mm` below PCB `-Z`)."""
    x0 = D.RADXA_X_CENTRE - 41.8
    y0 = D.RADXA_Y_CENTRE - 16.7
    z0 = D.RADXA_PCB_Z0 - D.RADXA_M2_H
    return cq.Solid.makeBox(22.0, D.RADXA_M2_H * 0.0 + 30.0, D.RADXA_M2_H, cq.Vector(x0, y0, z0))


def usb_a_cluster() -> cq.Shape:
    """4x TE Connectivity `292303-7` horizontal USB-A receptacles (`lib/step/usb_a_te_292303_7`)."""
    raw = _usb_a_step.get_shape()
    dy = D.USB_A_Y0 - float(AP.FRONT_USB_A_SPEC["step_ymin_mm"])
    solids = []
    for cx in D.FRONT_PORT_XS:
        placed = raw.translate((cx, dy, D.USB_A_SEAT_Z))
        solids.extend(placed.Solids())
    return cq.Compound.makeCompound(solids)


def rj45_jack() -> cq.Shape:
    """3D-modelled 2.5GbE 8P8C shielded RJ45 Ethernet receptacle + M2.5 mounting carrier (`REQ-05`).

    Features:
      - Shielded 8P8C housing (`11.00 x 19.50 x 10.40 mm` at `X = 37.50..48.50, Y = 27.50..47.00,
        Z = 2.00..12.40 mm`) with rear panel-mount bezel nose (`14.00 x 1.30 x 10.60 mm` at
        `Y = 47.00..48.30 mm`, flush with the rear `+Y` wall cutout)
      - Stepped IEC 60603-7 8P8C modular plug cavity (`9.20 x 5.60 mm` upper cavity + `6.80 x 1.20`
        keying shoulder + `3.60 x 1.20 mm` bottom locking-tab latch keyway)
      - 8x gold-plated contact spring fingers (`1.02 mm` pitch) inside the upper 8P8C cavity
      - Top-left (Green Link) and top-right (Amber 2.5GbE Activity) LED windows on the `+Y` face
      - Carrier PCB (`Z = 5.65..7.25 mm`) with `2x Ø2.70 mm` M2.5 mounting ears at
        `(43.00, 23.00)` and `(51.50, 28.50)` bolting to `lower_tub`'s `RX-M2.5x4.0` standoffs
    """
    housing = cq.Solid.makeBox(10.40, 20.80, 10.40, cq.Vector(38.00, 27.50, 2.00))
    bezel = cq.Solid.makeBox(12.20, 2.10, 10.60, cq.Vector(38.00, 47.00, 1.90))
    carrier_spine = cq.Solid.makeBox(
        10.40, 8.50, 1.60, cq.Vector(38.00, 21.00, D.RJ45_SEAT_Z + 0.05)
    )
    ear_f = cq.Solid.makeCylinder(
        3.00,
        1.60,
        cq.Vector(D.RJ45_MOUNT_HOLES[0][0], D.RJ45_MOUNT_HOLES[0][1], D.RJ45_SEAT_Z + 0.05),
    )
    ear_s_arm = cq.Solid.makeBox(6.80, 5.60, 1.60, cq.Vector(45.20, 25.70, D.RJ45_SEAT_Z + 0.05))
    ear_s = cq.Solid.makeCylinder(
        3.00,
        1.60,
        cq.Vector(D.RJ45_MOUNT_HOLES[1][0], D.RJ45_MOUNT_HOLES[1][1], D.RJ45_SEAT_Z + 0.05),
    )
    header_blk = cq.Solid.makeBox(8.40, 3.20, 2.80, cq.Vector(39.00, 24.00, D.RJ45_SEAT_Z + 1.65))
    body = housing.fuse(bezel, carrier_spine, ear_f, ear_s_arm, ear_s, header_blk)

    cuts = [
        cq.Solid.makeCylinder(1.35, 3.00, cq.Vector(hx, hy, D.RJ45_SEAT_Z - 0.50))
        for hx, hy in D.RJ45_MOUNT_HOLES
    ] + [
        cq.Solid.makeBox(8.80, 13.80, 5.60, cq.Vector(38.80, 35.80, 4.90)),
        cq.Solid.makeBox(6.60, 13.80, 1.20, cq.Vector(39.90, 35.80, 3.70)),
        cq.Solid.makeBox(3.60, 13.80, 1.20, cq.Vector(41.40, 35.80, 2.50)),
        cq.Solid.makeBox(2.00, 1.00, 1.10, cq.Vector(38.40, 48.30, 10.90)),
        cq.Solid.makeBox(2.00, 1.00, 1.10, cq.Vector(46.00, 48.30, 10.90)),
    ]
    carved = body.cut(*cuts)
    pins = [
        cq.Solid.makeBox(
            0.42,
            8.50,
            1.10,
            cq.Vector(43.20 + (i - 3.5) * 1.02 - 0.21, 36.20, 9.50),
        )
        for i in range(8)
    ]
    return carved.fuse(*pins)


def get_shape() -> cq.Shape:
    """Combined reference compound of all internal bought electronics."""
    return cq.Compound.makeCompound(
        [
            board_solid(),
            m2_keepout(),
            heatsink_solid(),
            usb_a_cluster(),
            rj45_jack(),
        ]
    )
