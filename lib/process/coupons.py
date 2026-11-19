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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402
from part import (  # noqa: E402
    front_io_carrier_l,
    front_port_cover,
    power_slider,
    usb_retainer_bracket,
)
from process.printable import (
    check_footprint,  # noqa: E402
    orient_to_bed,  # noqa: E402
)
from variant import lower_tub, upper_shell  # noqa: E402

# cad/, three levels up from lib/<stage>/this_file.py. Two levels pointed at lib/ after the move
# into lib/<stage>/ (2026-11-15), so exports went to lib/export/ and stale copies were sliced.
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if not os.path.isfile(os.path.join(REPO, "run")):
    raise RuntimeError(f"{REPO} is not the cad/ folder (no ./run): exports would go astray")
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

# Stepped hole gauge. GBA's PETG prints came out ~0.33 mm small on a Ø10 bore and ~0.4 mm small
# under Ø2 (notes/PRINTING.md), so the magnet pockets and hinge pin holes are tried at drawn size
# and two steps up. Hole i (i = 1..3, left to right) is marked by i bumps on top.
GAUGE_STEP = 0.2
GAUGE_PITCH = 7.0
MAGNET_SIZES = tuple(D.MAGNET_BORE_D + i * GAUGE_STEP for i in range(3))
HINGE_SIZES = tuple(D.HINGE_PRESS_D + i * GAUGE_STEP for i in range(3))


def _marks(x: float, n: int, z: float) -> list[cq.Solid]:
    return [
        cq.Solid.makeCylinder(0.5, 0.4, cq.Vector(x + (k - (n - 1) / 2) * 1.4, 0.0, z))
        for k in range(n)
    ]


def _wall_gauge() -> cq.Shape:
    """8.0 mm-deep full through-holes bored horizontally along Y (no foot or fillet), so both
    caliper jaws and Ø3.0 magnets / Ø1.5 hinge pins can measure them cleanly (owner, plate 5)."""
    w, t, h = 3 * GAUGE_PITCH + 4.0, 8.0, 14.0
    x0 = -w / 2
    body = cq.Solid.makeBox(w, t, h, cq.Vector(x0, -t / 2, 0.0))
    marks, holes = [], []
    for i in range(3):
        x = (i - 1) * GAUGE_PITCH
        marks += _marks(x, i + 1, h)
        holes.append(
            cq.Solid.makeCylinder(
                MAGNET_SIZES[i] / 2,
                t + 0.4,
                cq.Vector(x, -t / 2 - 0.2, 9.5),
                cq.Vector(0, 1, 0),
            )
        )
        holes.append(
            cq.Solid.makeCylinder(
                HINGE_SIZES[i] / 2,
                t + 0.4,
                cq.Vector(x, -t / 2 - 0.2, 4.0),
                cq.Vector(0, 1, 0),
            )
        )
    return body.fuse(*marks).cut(*holes)


def _plate_gauge() -> cq.Shape:
    """8.0 mm-deep full through-holes bored vertically along Z (no blind floor or fillet), so
    caliper inside-jaws and Ø3.0 mm magnets can measure them cleanly (owner, plate 5)."""
    w, d, t = 3 * GAUGE_PITCH + 4.0, 10.0, 8.0
    body = cq.Solid.makeBox(w, d, t, cq.Vector(-w / 2, -d / 2, 0.0))
    marks, holes = [], []
    for i in range(3):
        x = (i - 1) * GAUGE_PITCH
        marks += [m.translate(cq.Vector(0, -3.2, 0)) for m in _marks(x, i + 1, t)]
        holes.append(
            cq.Solid.makeCylinder(
                MAGNET_SIZES[i] / 2,
                t + 0.4,
                cq.Vector(x, 0.8, -0.2),
            )
        )
    return body.fuse(*marks).cut(*holes)


COUPONS = (
    Coupon(
        "1_button_chimney",
        "power button's sleeve slides on the bracket's pole (Ø3.1 on Ø2.8) with no binding over "
        "the 2.1 mm stroke; the button slides freely in the chimney (0.22 mm/side); held on the "
        "pole and in the chimney together it doesn't rock (plate 4 wobbled)",
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
        "SS-5GL drops into the carrier's tower from above; two M2.5 x 10 screws, from behind "
        "through the close-fit holes, bite into both switch holes and pull it flat to the tower",
        (
            Piece(
                "tub_tower",
                front_io_carrier_l.get_shape,
                front_io_carrier_l.PRINT_NORMAL,
                ((-38.6, -24.0, 0.0), (-21.5, -16.0, TOP)),
            ),
        ),
    ),
    Coupon(
        "3_port_door",
        "door seats between the carrier's hinge cheeks on the bench; push the continuous Ø1.5 x "
        "31.4 mm steel pin through both cheeks and the door knuckle: it presses into the outer "
        "cheek, turns freely in the door, and pushes out from the inner cheek for disassembly; "
        "carrier then bolts into the 3 conical RX-M2.5x4.0 bosses on tub_bay",
        (
            Piece(
                "carrier_bay",
                front_io_carrier_l.get_shape,
                front_io_carrier_l.PRINT_NORMAL,
            ),
            Piece(
                "tub_bay",
                lower_tub.get_shape,
                lower_tub.PRINT_NORMAL,
                ((-50.0, -51.0, 0.0), (-2.0, -9.0, TOP)),
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
    Coupon(
        "6_hole_gauge",
        "magnets (Ø3.0) and a Ø1.5 steel pin in each hole; holes 1/2/3 (bumps on top) are "
        + ", ".join(f"Ø{m:.1f}" for m in MAGNET_SIZES)
        + " (magnets) and "
        + ", ".join(f"Ø{h:.1f}" for h in HINGE_SIZES)
        + " (hinge, lower row). Report the smallest magnet hole that takes a magnet by hand,"
        " the hinge hole the pin presses into and stays, and the smallest it turns freely in",
        (
            Piece("wall_sideways", _wall_gauge, (0, 0, 1)),
            Piece("plate_downward", _plate_gauge, (0, 0, 1)),
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
