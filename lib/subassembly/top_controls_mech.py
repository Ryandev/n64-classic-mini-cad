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
