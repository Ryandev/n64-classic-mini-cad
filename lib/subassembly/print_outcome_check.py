"""The printability check must agree with what the printer actually did.

Ground truth (MFIC rung 1, a real system): coupon plate 1, printed 2026-11-14 on the X2D in black
PETG at 0.20 mm with NO supports, judged by the owner. Each piece is loaded from the very STL that
was sliced (`testing/fixtures/coupon_plate1/`, bedded as printed), so later design changes (the
switch pin removed on 2026-11-15) can't rewrite what the printer was given. It goes to
`printable.check_overhang` with no support declared, as it was sliced. A piece that failed on the
bed must fail the check, and one that printed clean must pass it. A row fails when the two
disagree.

What failed, and where (owner's FreeCAD selection):
  - tub_tower: the switch V-pin, a horizontal pin whose underside starts ~13.5 mm up
  - bracket: the side peg (Ø2.8 x 4.3), sticking out ~3 mm above the bed
  - power_button_on_side: the rounded cap end, 1-4 mm above the bed
  - shell_chimney: the skin, 4.5-7.6 mm above the bed, held only by the chimney; it drooped and
    its free edge curled up
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
import printable  # noqa: E402
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeSolid, BRepBuilderAPI_Sewing  # noqa: E402
from OCP.StlAPI import StlAPI_Reader  # noqa: E402
from OCP.TopoDS import TopoDS, TopoDS_Shape  # noqa: E402

FIXTURES = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "testing",
    "fixtures",
    "coupon_plate1",
)


def _printed(name: str) -> cq.Shape:
    """The piece as the slicer was given it: its plate-1 STL, sewn into a solid."""
    path = os.path.join(FIXTURES, name + ".stl")
    mesh = TopoDS_Shape()
    if not StlAPI_Reader().Read(mesh, path):
        raise FileNotFoundError(path)
    sew = BRepBuilderAPI_Sewing(1e-4)
    sew.Add(mesh)
    sew.Perform()
    return cq.Shape.cast(BRepBuilderAPI_MakeSolid(TopoDS.Shell(sew.SewedShape())).Solid())


# piece name -> printed clean on plate 1 (owner, 2026-11-14)
PLATE1 = {
    "1_button_chimney_shell_chimney": False,
    "1_button_chimney_power_button": True,
    "1_button_chimney_power_button_on_side": False,
    "1_button_chimney_bracket": False,
    "2_switch_tower_tub_tower": False,
    "6_hole_gauge_wall_sideways": True,
    "6_hole_gauge_plate_downward": True,
}


def _wall_with_opening(width: float) -> cq.Shape:
    """A 2.2 mm wall, 14 mm tall, with a `width` x 5 mm window through it 4 mm up."""
    wall = cq.Solid.makeBox(width + 10.0, 2.2, 14.0)
    window = cq.Solid.makeBox(width, 2.2, 5.0, cq.Vector(5.0, 0.0, 4.0))
    return wall.cut(window)


def _wall_with_pin(length: float) -> cq.Shape:
    """A wall with a Ø2.8 pin sticking `length` out of its side, 5 mm up."""
    wall = cq.Solid.makeBox(10.0, 3.0, 10.0)
    pin = cq.Solid.makeCylinder(1.4, length, cq.Vector(5.0, 3.0, 5.0), cq.Vector(0, 1, 0))
    return wall.fuse(pin)


def _long_bar_with_pin() -> cq.Shape:
    """A 130 x 20 mm bar (wider in X than Y, like the tub and shell) with a pin 60 mm out."""
    bar = cq.Solid.makeBox(130.0, 20.0, 10.0, cq.Vector(-65.0, -10.0, 0.0))
    pin = cq.Solid.makeCylinder(1.4, 4.0, cq.Vector(60.0, 10.0, 5.0), cq.Vector(0, 1, 0))
    return bar.fuse(pin)


# Shapes whose answer is known from how FDM works (lower rung than the print: the author's own
# picks), one per kind of overhang, so each branch of the rule can fail on its own.
RULES = (
    ("a 6 mm window in a wall bridges (held at both ends)", _wall_with_opening(6.0), True),
    ("a 12 mm window needs support (bridge over 10 mm)", _wall_with_opening(12.0), False),
    ("a sideways pin needs support (held at one end)", _wall_with_pin(4.0), False),
    (
        "a pin 60 mm along a 130 mm part is seen (the whole width is sliced)",
        _long_bar_with_pin(),
        False,
    ),
)


def _verdict(shape: cq.Shape) -> tuple[bool | None, str]:
    """The overhang row's verdict with no support declared; None if it refused the shape."""
    try:
        return printable.check_overhang(shape, up=(0, 0, 1), support_mm2=0.0)
    except ValueError as e:  # a section the check refuses to trust fails the row, loudly
        return None, f"check raised: {e}"


def check_all():
    rows = []
    for label, shape, printable_ok in RULES:
        ok, msg = _verdict(shape)
        rows.append((f"PRINT_RULE {label}", ok is not None and ok == printable_ok, msg))
    for name, printed_ok in PLATE1.items():
        if not os.path.isfile(os.path.join(FIXTURES, name + ".stl")):
            rows.append((f"PRINT_OUTCOME {name}", False, f"no plate-1 STL for {name}"))
            continue
        # The bedded shape sits on z=0 with its print-up along +Z.
        ok, msg = _verdict(_printed(name))
        said = {True: "printable", False: "needs support", None: "no verdict"}[ok]
        real = "printed clean" if printed_ok else "FAILED on the bed"
        rows.append(
            (
                f"PRINT_OUTCOME {name}",
                ok is not None and ok == printed_ok,
                f"check: {said}; real: {real}; {msg}",
            )
        )
    return rows


def main():
    rows = check_all()
    for label, ok, msg in rows:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
        print(f"        {msg}")
    return 0 if all(ok for _l, ok, _m in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
