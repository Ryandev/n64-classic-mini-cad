"""Kingbright L-93WEGW (`Rapid 55-0155`) 3 mm Red/Green bi-colour 3-lead common-cathode LED.

Compact 3 mm T-1 through-hole bi-colour indicator LED (`J-07` front power/status indicator):
  - Red (`625 nm`, Pin 1 anode via `330 Ohm` to RP2040 `GP4` / S5 standby rail):
    lights **RED = Power connected / Standby**
  - Green (`565 nm`, Pin 3 anode via `330 Ohm` to RP2040 `GP5` / S0 active rail):
    lights **GREEN = Console ON**
  - Common Cathode (Pin 2 centre lead to `GND`)

Dimensions from Kingbright `L-93WEGW` (`3 mm` T-1 3-lead bi-colour datasheet, `mm`),
seated directly inside `lower_tub`'s integral LED holder cradle behind the Clear PETG
`led_light_pipe.py`:
  - Lens diameter:    `3.0 mm` (`R = 1.5 mm` hemispherical dome)
  - Rim flange:       `Ø3.8 x 0.9 mm` (`0.20 mm/side` radial clearance in `Ø4.20 mm` seat)
  - Lens body height: `4.2 mm` (`3.3 mm` cylinder/dome + `0.9 mm` rim)
  - Leads:            `3x 0.45 x 0.45 mm` square pins (`Pin 1 Red`, `Pin 2 Common Cathode`,
                      `Pin 3 Green` on `0.70 mm` spacing inside the `2.20 mm` top wire-drop slot)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402

LENS_DIA = 3.0
LENS_HEIGHT = 4.2
RIM_DIA = 3.8
RIM_HEIGHT = 0.9
RIM_FLAT_X = 1.7

LEAD_SIZE = 0.45
LEAD_PITCH = 0.70
LEAD_XS = (-LEAD_PITCH, 0.0, LEAD_PITCH)  # Pin 1 Red, Pin 2 Common Cathode, Pin 3 Green
LEAD_LEN = 6.5


def get_shape() -> cq.Shape:
    """Build the 3 mm Kingbright L-93WEGW 3-lead bi-colour LED in local coords (`+Z` = tip)."""
    r = LENS_DIA / 2.0
    cyl_h = LENS_HEIGHT - RIM_HEIGHT - r

    rim_cyl = cq.Solid.makeCylinder(RIM_DIA / 2.0, RIM_HEIGHT)
    flat_cut = cq.Solid.makeBox(
        RIM_DIA,
        RIM_DIA,
        RIM_HEIGHT + 1.0,
        cq.Vector(-RIM_FLAT_X - RIM_DIA, -RIM_DIA / 2.0, -0.5),
    )
    rim = rim_cyl.cut(flat_cut)

    body = cq.Solid.makeCylinder(r, cyl_h, cq.Vector(0.0, 0.0, RIM_HEIGHT))
    dome_z = RIM_HEIGHT + cyl_h
    dome = cq.Solid.makeSphere(r, cq.Vector(0.0, 0.0, dome_z), angleDegrees1=0, angleDegrees2=90)

    leads = [
        cq.Solid.makeBox(
            LEAD_SIZE,
            LEAD_SIZE,
            LEAD_LEN,
            cq.Vector(lx - LEAD_SIZE / 2.0, -LEAD_SIZE / 2.0, -LEAD_LEN),
        )
        for lx in LEAD_XS
    ]
    return rim.fuse(body, dome, *leads)


def placed_at_front() -> cq.Shape:
    """Place the 3 mm 3-lead Red/Green bi-colour LED coaxially inside `lower_tub`'s cradle.

    Seats the `Ø3.0 mm` lens barrel (`Y = -39.30 .. -36.50 mm`, `0.26 mm` behind
    `led_light_pipe`) inside the `Ø3.40 mm` cradle bore (`0.20 mm/side` radial clearance),
    with its `Ø3.80 mm` rim flange (`Y = -36.50 .. -35.60 mm`) seated inside the `Ø4.20 mm`
    counterbore and its `3x 0.45 mm` leads (`Pin 1 Red`, `Pin 2 Common Cathode`, `Pin 3 Green`)
    exiting rearward (`Y = -35.60 .. -29.10 mm`) through the `2.20 mm` top wire-drop slot.
    """
    snout = cq.Solid.makeCylinder(
        D.LED_3MM_D / 2.0,
        2.90,
        cq.Vector(0.0, -39.30, D.LED_PIPE_Z),
        cq.Vector(0.0, 1.0, 0.0),
    )
    collar = cq.Solid.makeCylinder(
        RIM_DIA / 2.0,
        RIM_HEIGHT,
        cq.Vector(0.0, -36.50, D.LED_PIPE_Z),
        cq.Vector(0.0, 1.0, 0.0),
    )
    leads = [
        cq.Solid.makeBox(
            LEAD_SIZE,
            LEAD_LEN,
            LEAD_SIZE,
            cq.Vector(lx - LEAD_SIZE / 2.0, -35.60, D.LED_PIPE_Z - LEAD_SIZE / 2.0),
        )
        for lx in LEAD_XS
    ]
    return snout.fuse(collar, *leads)
