"""Complete 50%-scale N64 Classic Mini Assembly (`lib/assembly/n64_mini.py`).

Mirrors `GBA/CAD/lib/assembly/gba.py`: combines every fabricated enclosure part and
every bought/modified internal component in the right-handed console coordinate frame:
  - `variant/lower_tub.py` (Charcoal Grey lower chassis + Radxa standoffs + rear I/O)
  - `variant/upper_shell.py` (Charcoal Grey sculpted N64 top deck + dome exhaust louvers)
  - `part/front_bezel.py` (Matte Black N64 curved-top front shield emblem)
  - `part/power_slider.py` & `part/reset_button.py` (Light Cool Grey stadium controls)
  - `part/front_port_cover.py` (Charcoal Grey single 4-port magnetic bottom-hinged plate)
  - `4x part/n64_port_insert.py` (Light Cool Grey `Ø10.2 mm` N64 controller port bezels)
  - `part/led_light_pipe.py` (Translucent Red front power indicator light-pipe)
  - `variant/radxa_x4.py` (`placed()`, 23-solid de-ported Radxa X4 v1.11 SBC)
  - `component/hsb26_343408.py` (bought pin-fin SoC heat sink), `component/sunon_mf30060v2.py`
    (30 mm fan), `part/cooling_duct.py` + `part/cooling_hood.py` (printed), and
    `component/bumpon_sj5012.py` (4 rubber feet)
  - `component/radxa_x4.py` (`m2_keepout()`, `usb_a_cluster()`, `rj45_jack()`)
  - `subassembly/top_controls_mech.py` (`2x` `6x6x5 mm` tactile switches)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402
from component import bumpon_sj5012, radxa_x4, sunon_mf30060v2  # noqa: E402
from part import (  # noqa: E402
    cartridge_flaps,
    cooling_duct,
    cooling_hood,
    front_bezel,
    led_light_pipe,
    power_slider,
    reset_button,
)
from subassembly import front_panel_mech, top_controls_mech  # noqa: E402
from variant import lower_tub, upper_shell  # noqa: E402

SHELL_ENVELOPE = (D.SHELL_W, D.SHELL_D, D.SHELL_H)
DEFAULT_STEP = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "export",
    "assembly",
    "n64_classic_mini_assembly.step",
)


def named_bodies() -> list[tuple[str, tuple[float, float, float], cq.Shape]]:
    """Return `(name, rgb, shape)` for every visual component in the assembled N64 Classic Mini."""
    charcoal = (0.22, 0.23, 0.25)
    cool_grey = (0.68, 0.70, 0.73)
    matte_black = (0.09, 0.09, 0.10)
    led_red = (0.88, 0.14, 0.14)
    pcb_green = (0.10, 0.44, 0.26)
    silver = (0.76, 0.78, 0.82)
    nvme_dark = (0.16, 0.18, 0.22)
    brass = (0.80, 0.68, 0.32)

    inserts = front_panel_mech.port_inserts()
    sw_l, sw_r = top_controls_mech.tactile_switches()
    return [
        ("lower_tub", charcoal, lower_tub.get_shape()),
        ("upper_shell", charcoal, upper_shell.get_shape()),
        ("cartridge_flaps", cool_grey, cartridge_flaps.get_shape()),
        ("front_bezel", matte_black, front_bezel.get_shape()),
        ("power_slider", cool_grey, power_slider.get_shape()),
        ("reset_button", cool_grey, reset_button.get_shape()),
        ("front_port_cover", charcoal, front_panel_mech.cover()),
        ("usb_retainer_brackets", charcoal, front_panel_mech.usb_retainer_compound()),
        ("n64_port_p1", cool_grey, inserts[0]),
        ("n64_port_p2", cool_grey, inserts[1]),
        ("n64_port_p3", cool_grey, inserts[2]),
        ("n64_port_p4", cool_grey, inserts[3]),
        ("led_light_pipe", led_red, led_light_pipe.get_shape()),
        ("wired_led_3mm", (0.98, 0.22, 0.18), front_panel_mech.wired_led_3mm()),
        ("radxa_x4_deported", pcb_green, radxa_x4.vendor_step_compound()),
        ("hsb26_heatsink", matte_black, radxa_x4.heatsink_solid()),
        ("m2_2230_nvme", nvme_dark, radxa_x4.m2_keepout()),
        ("front_usb_a_x4", silver, radxa_x4.usb_a_cluster()),
        ("front_door_magnets_x4", silver, front_panel_mech.door_magnets()),
        ("front_tub_magnets_x4", silver, front_panel_mech.tub_magnets()),
        ("rear_rj45_2_5gbe", silver, radxa_x4.rj45_jack()),
        ("tact_switch_power", brass, sw_l),
        ("tact_switch_reset", brass, sw_r),
        ("fan_mf30060v2", matte_black, sunon_mf30060v2.placed()),
        ("cooling_duct", charcoal, cooling_duct.get_shape()),
        ("cooling_hood", charcoal, cooling_hood.get_shape()),
        ("feet_sj5012", matte_black, bumpon_sj5012.placed()),
    ]


def get_shape(include_electronics: bool = True) -> cq.Shape:
    """Return the full N64 Classic Mini compound in console coordinates."""
    items = named_bodies()
    if not include_electronics:
        items = items[:12]
    return cq.Compound.makeCompound([shp for _, _, shp in items])


def export(path: str = DEFAULT_STEP) -> str:
    """Export the full console assembly STEP to `export/assembly/n64_classic_mini_assembly.step`."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cq.exporters.export(get_shape(include_electronics=True), path)
    return path


if __name__ == "__main__":
    s = get_shape()
    b = s.BoundingBox()
    print(f"N64 Classic Mini assembly: {b.xlen:.2f} x {b.ylen:.2f} x {b.zlen:.2f} mm")
    print(
        f"  X=[{b.xmin:+.2f}, {b.xmax:+.2f}] "
        f"Y=[{b.ymin:+.2f}, {b.ymax:+.2f}] "
        f"Z=[{b.zmin:+.2f}, {b.zmax:+.2f}]"
    )
    out = export()
    print(f"  wrote {out}")
