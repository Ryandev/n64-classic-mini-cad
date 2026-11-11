"""Front controller port bays, twin hinged covers, N64 inserts, Clear PETG light-pipe & 3mm LED.

Combines:
  - `variant/lower_tub.py` (with twin-bay pivot sockets, keeper bridges & internal LED holder)
  - 2x twin-port hinged `part/front_port_cover.py` (`P1+P2` left at `X = -25.0 mm`, `P3+P4` right
    at `X = +25.0 mm`) straddling `SPLIT_Z = 12.94 mm` (`Z = 13.19 mm` centreline)
  - 4x separately-printed shallow `part/n64_port_insert.py` (`X = -32.6, -17.4, +17.4, +32.6 mm`)
  - `part/led_light_pipe.py` (`J-07`, Clear PETG lenticular N64 Power LED light-pipe at `X = 0.0`)
  - `wired_led_3mm()` (3 mm red through-hole LED seated inside `lower_tub`'s LED holder cradle)
  - `component/radxa_x4.py` `usb_a_cluster()` (4x `TE Connectivity 292303-7` USB-A receptacles)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402
from component import led_l819, radxa_x4  # noqa: E402
from part import (  # noqa: E402
    front_port_cover,
    led_light_pipe,
    n64_port_insert,
    usb_retainer_bracket,
)
from variant import lower_tub  # noqa: E402


def usb_retainer_brackets() -> list[cq.Shape]:
    """Left (`P1+P2 / Power`) and Right (`P3+P4 / Reset`) glue-in USB-A & button-stop brackets."""
    return usb_retainer_bracket.brackets()


def usb_retainer_compound() -> cq.Shape:
    """Compound of both Left and Right `usb_retainer_bracket` solids."""
    return cq.Compound.makeCompound(usb_retainer_brackets())


def covers() -> list[cq.Shape]:
    """Left (`P1+P2` at `X = -25.0 mm`) and Right (`P3+P4` at `X = +25.0 mm`) twin-port covers."""
    return [front_port_cover.cover_at(bx) for bx in D.FRONT_BAY_XS]


def cover() -> cq.Shape:
    """Compound of both Left (`P1+P2`) and Right (`P3+P4`) twin-port hinged covers."""
    return cq.Compound.makeCompound(covers())


def cover_open(deg: float) -> cq.Shape:
    """Twin hinged front controller port covers rotated forward/down by `deg` around their hinge."""
    pivot = cq.Vector(0.0, D.HINGE_Y, D.HINGE_Z)
    axis = cq.Vector(1.0, 0.0, 0.0)
    return cover().rotate(pivot, pivot + axis, deg)


def port_inserts() -> list[cq.Shape]:
    """All 4 separately-printed shallow N64 controller port inserts (`P1..P4`)."""
    return [
        n64_port_insert.insert_at(px, player_num=idx)
        for idx, px in enumerate(D.PORT_INSERT_XS, start=1)
    ]


def bicolour_led() -> cq.Shape:
    """3-lead Red/Green bi-colour LED (`Kingbright L-819EGW`) seated in `lower_tub`'s cradle."""
    return led_l819.placed_at_front()


def wired_led_3mm() -> cq.Shape:
    """Alias for `bicolour_led()` (3-lead Red=Power / Green=ON bi-colour LED in cradle)."""
    return bicolour_led()


def door_magnets() -> cq.Shape:
    """4x N52 neodymium latch magnets seated inside the `+Y` pockets of the 2 twin covers."""
    y_cov_back = D.FRONT_BAY_Y0 + (D.FRONT_COVER_T - 0.2)
    r = D.MAGNET_D / 2.0
    return cq.Compound.makeCompound(
        [
            cq.Solid.makeCylinder(
                r,
                0.48,
                cq.Vector(mx, y_cov_back - 0.02, mz),
                cq.Vector(0.0, -1.0, 0.0),
            )
            for mx in D.MAGNET_XS
            for mz in D.MAGNET_ZS
        ]
    )


def tub_magnets() -> cq.Shape:
    """4x N52 neodymium keeper magnets seated inside the `-Y` bridge pockets of the shell."""
    y_tub_face = D.FRONT_BAY_Y0 + D.FRONT_COVER_T
    r = D.MAGNET_D / 2.0
    return cq.Compound.makeCompound(
        [
            cq.Solid.makeCylinder(
                r,
                D.MAGNET_T,
                cq.Vector(mx, y_tub_face + 0.05, mz),
                cq.Vector(0.0, 1.0, 0.0),
            )
            for mx in D.MAGNET_XS
            for mz in D.MAGNET_ZS
        ]
    )


def magnets() -> cq.Shape:
    """All 8 N52 neodymium latch magnets (`4x` door + `4x` shell)."""
    return cq.Compound.makeCompound([*door_magnets().Solids(), *tub_magnets().Solids()])


def get_shape() -> cq.Shape:
    """Return the assembled front-panel compound."""
    return cq.Compound.makeCompound(
        [
            lower_tub.get_shape(),
            *usb_retainer_brackets(),
            *covers(),
            *port_inserts(),
            led_light_pipe.get_shape(),
            wired_led_3mm(),
            magnets(),
            radxa_x4.usb_a_cluster(),
        ]
    )
