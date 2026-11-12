"""Top-deck controls, cartridge dust flaps, Omron SS-5GL switches & front emblem subassembly.

Combines:
  - `variant/upper_shell.py` (50%-scale upper shell with rear dome exhaust slots)
  - `part/cartridge_flaps.py` (`J-09`, Light Cool Grey dual cartridge dust-flap insert)
  - `part/power_slider.py` (`J-03`, Light Cool Grey momentary `POWER` push button)
  - `part/reset_button.py` (`J-04`, `AC-T18`, Light Cool Grey momentary `RESET` push button)
  - `part/front_bezel.py` (`J-06`, Clear Acrylic front N64 jewel)
  - 2x `Omron SS-5GL` subminiature hinge-lever SPDT microswitches (`omron_switches()`,
    aliased as `tactile_switches()`) under `POWER` and `RESET`
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402
from component import omron_ss5gl  # noqa: E402
from part import cartridge_flaps, front_bezel, power_slider, reset_button  # noqa: E402
from variant import upper_shell  # noqa: E402


def omron_switches() -> list[cq.Shape]:
    """2x `Omron SS-5GL` subminiature hinge-lever microswitches under Power and Reset."""
    return [
        omron_ss5gl.placed_at(D.POWER_SLIDER_X),
        omron_ss5gl.placed_at(D.RESET_BTN_X),
    ]


def omron_screws() -> list[cq.Shape]:
    """2x switch screws (hole 2), head on the tower's rear face, tip inside the switch (C2).

    The thread-forming screw is modelled as its head, its Ø3.0 shank through the tower's clearance
    hole, and the Ø2.35 pilot it fills in the switch, where it rolls its own thread.
    """
    y = cq.Vector(0.0, -1.0, 0.0)
    out = []
    for x in (-33.73, 33.73):
        y1 = D.OMRON_TOWER_Y1
        y_switch = D.OMRON_Y + omron_ss5gl.BODY_WIDTH / 2.0  # switch rear face (-20.95)
        y_tip = y1 - D.OMRON_SCREW_L
        z = D.OMRON_HOLE_Z
        head = cq.Solid.makeCylinder(
            D.OMRON_SCREW_HEAD_D / 2.0,
            D.OMRON_SCREW_HEAD_H,
            cq.Vector(x, y1 + D.OMRON_SCREW_HEAD_H, z),
            y,
        )
        shank = cq.Solid.makeCylinder(D.OMRON_SCREW_D / 2.0, y1 - y_switch, cq.Vector(x, y1, z), y)
        core = cq.Solid.makeCylinder(
            D.OMRON_HOLE_D / 2.0, y_switch - y_tip, cq.Vector(x, y_switch, z), y
        )
        out.append(cq.Compound.makeCompound([head, shank, core]))  # touching, not overlapping
    return out


def tactile_switches() -> list[cq.Shape]:
    """Alias for `omron_switches()` returning the 2x `Omron SS-5GL` microswitches."""
    return omron_switches()


def get_shape() -> cq.Shape:
    """Return the assembled compound of `upper_shell` and all top-deck controls."""
    return cq.Compound.makeCompound(
        [
            upper_shell.get_shape(),
            cartridge_flaps.get_shape(),
            power_slider.get_shape(),
            reset_button.get_shape(),
            front_bezel.get_shape(),
            *omron_switches(),
        ]
    )
