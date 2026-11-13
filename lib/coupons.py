"""Print-test coupons: small regions cut from the real parts, to check fits before a full print.

Each coupon is a box crop of the part as designed (no separate test geometry, so a coupon can't
pass while the part fails), oriented by the part's own `PRINT_NORMAL` and written to
`export/coupons/<name>.stl` and `.step`. A crop that comes back empty or in several pieces raises:
the box has drifted off the feature it is meant to test.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402
from part import front_port_cover, power_slider, usb_retainer_bracket  # noqa: E402
from plate import orient_to_bed  # noqa: E402
from printable import check_footprint  # noqa: E402
from variant import lower_tub, upper_shell  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(REPO, "export", "coupons")
TOP = 60.0  # above every part: crops that keep a part's full height use it
LOOSE_MAX = 0.02  # loose crop fragments may total at most 2% of the coupon


@dataclass(frozen=True)
class Piece:
    """One printed body of a coupon: `source` cropped to `box` (or whole), printed `up`."""

    name: str
    source: Callable[[], cq.Shape]
    up: tuple[float, float, float]
    box: tuple[tuple[float, float, float], tuple[float, float, float]] | None = None


@dataclass(frozen=True)
class Coupon:
    """A fit to test, the pieces that make it, and what to check on the bench."""

    name: str
    check: str
    pieces: tuple[Piece, ...]


def _crop(shape: cq.Shape, box: tuple[tuple[float, float, float], ...]) -> cq.Shape:
    (x0, y0, z0), (x1, y1, z1) = box
    cutter = cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))
    out = shape.intersect(cutter)
    solids = sorted(out.Solids(), key=lambda s: -s.Volume())
    if not solids:
        raise ValueError(f"crop {box} is empty")
    # A box edge can clip the corner of a neighbouring feature into a loose fragment that would
    # only print as debris. Drop those, but only if they are tiny: a big second piece means the
    # box missed the feature it is meant to hold.
    loose = sum(s.Volume() for s in solids[1:])
    if loose > LOOSE_MAX * solids[0].Volume():
        vols = ", ".join(f"{s.Volume():.1f}" for s in solids)
        raise ValueError(f"crop {box} falls apart into {len(solids)} pieces ({vols} mm^3)")
    if loose:
        print(f"   (dropped {len(solids) - 1} loose fragment(s), {loose:.1f} mm^3)")
    return solids[0]


def _button_box() -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    bb = power_slider.get_shape().BoundingBox()
    m = 4.0  # chimney wall (~1.2) plus a rim so the crop stands on more than the chimney
    return (bb.xmin - m, bb.ymin - m, D.SPLIT_Z), (bb.xmax + m, bb.ymax + m, TOP)


def _standoff_box() -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    x, y = D.radxa_hole_centres()[0]
    return (x - 6.0, y - 6.0, 0.0), (x + 6.0, y + 6.0, D.RADXA_PCB_Z0 + 1.0)


def _corner_box() -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    x, y = D.CORNER_BOSS_XS[0], D.CORNER_BOSS_YS[0]
    return (x - 9.0, y - 9.0, D.SPLIT_Z - D.LIP_H - 1.0), (x + 9.0, y + 9.0, D.SPLIT_Z + 10.0)


_BAY = D.FRONT_BAY_X
_LIP_Y = (-8.0, 8.0)  # a straight run of the right-hand side wall

COUPONS = (
    Coupon(
        "1_button_chimney",
        "power button slides freely in the chimney (0.22 mm/side) and drops onto the bracket pole "
        "(Ø2.8 in Ø4.0); no rocking, no binding at full 2.1 mm stroke",
        (
            Piece("shell_chimney", upper_shell.get_shape, upper_shell.PRINT_NORMAL, _button_box()),
            Piece("power_button", power_slider.get_shape, power_slider.PRINT_NORMAL),
            Piece(
                "bracket",
                lambda: usb_retainer_bracket.bracket_at(_BAY),
                usb_retainer_bracket.PRINT_NORMAL,
            ),
        ),
    ),
    Coupon(
        "2_switch_tower",
        "SS-5GL hole 1 slides onto the Ø2.2 V-pin without force or play; the 3x10 PT screw, from "
        "behind through the Ø3.4 hole, pulls the switch tight to the tower without cracking it",
        (
            Piece(
                "tub_tower",
                lower_tub.get_shape,
                lower_tub.PRINT_NORMAL,
                ((-38.5, -29.0, 0.0), (-19.5, -15.0, TOP)),
            ),
        ),
    ),
    Coupon(
        "3_port_door",
        "door snaps onto its hinge pins, swings 0-90° freely and stays shut; check the pins "
        "(Ø1.8) didn't sag or break printing",
        (
            Piece(
                "tub_bay",
                lower_tub.get_shape,
                lower_tub.PRINT_NORMAL,
                (
                    (_BAY - D.FRONT_BAY_W / 2 - 4.0, -51.0, 0.0),
                    (_BAY + D.FRONT_BAY_W / 2 + 4.0, -38.0, TOP),
                ),
            ),
            Piece("door", lambda: front_port_cover.cover_at(_BAY), front_port_cover.PRINT_NORMAL),
        ),
    ),
    Coupon(
        "4_inserts",
        "RX-M2.5x4.0 into the Ø3.2 standoff and RX-M3x5.7 into the Ø4.0 corner boss: set flush "
        "and square, no bulge or split in the wall; an M2.5 and an M3 screw then turn in cleanly",
        (
            Piece("tub_standoff", lower_tub.get_shape, lower_tub.PRINT_NORMAL, _standoff_box()),
            Piece("shell_corner", upper_shell.get_shape, upper_shell.PRINT_NORMAL, _corner_box()),
        ),
    ),
    Coupon(
        "5_split_lip",
        "shell section drops over the tub lip (0.15 mm/side) by hand, no rattle; outer walls "
        "flush at the split",
        (
            Piece(
                "tub_lip",
                lower_tub.get_shape,
                lower_tub.PRINT_NORMAL,
                ((50.0, _LIP_Y[0], 0.0), (70.0, _LIP_Y[1], TOP)),
            ),
            Piece(
                "shell_lip",
                upper_shell.get_shape,
                upper_shell.PRINT_NORMAL,
                ((50.0, _LIP_Y[0], D.SPLIT_Z - D.LIP_H - 1.0), (70.0, _LIP_Y[1], TOP)),
            ),
        ),
    ),
)


def build(coupon: Coupon) -> list[tuple[str, cq.Shape, str]]:
    """Crop and orient each piece; return `(name, shape, footprint report)`."""
    out = []
    for p in coupon.pieces:
        shape = p.source()
        if p.box is not None:
            shape = _crop(shape, p.box)
        bedded = orient_to_bed(shape, p.up)
        _ok, msg = check_footprint(bedded)
        out.append((f"{coupon.name}_{p.name}", bedded, msg))
    return out


def main(argv: list[str] | None = None) -> int:
    """Write every coupon (or the named ones) to `export/coupons/`."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("names", nargs="*", help="coupon names (prefixes); default all")
    args = ap.parse_args(argv)
    os.makedirs(OUT_DIR, exist_ok=True)
    chosen = [c for c in COUPONS if not args.names or any(c.name.startswith(n) for n in args.names)]
    if not chosen:
        print(f"no coupon matches {args.names}; have {[c.name for c in COUPONS]}")
        return 2
    for c in chosen:
        print(f"== {c.name}: {c.check}", flush=True)
        for name, shape, msg in build(c):
            bb = shape.BoundingBox()
            for ext in ("stl", "step"):
                cq.exporters.export(shape, os.path.join(OUT_DIR, f"{name}.{ext}"))
            print(f"   {name}: {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm, {msg}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
