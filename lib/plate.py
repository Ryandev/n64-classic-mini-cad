"""Orient and pack all 11 printable FDM parts onto a single 256 x 256 mm build plate (`plate.py`).

Every FDM part declares `PRINT_NORMAL` (the unit vector in console coordinates that points `+Z`
up on the print bed). This module rotates each part by a proper rotation (`det == +1`) so its
`PRINT_NORMAL` aligns with `+Z`, drops its bed face to `Z = 0.0 mm`, packs all 11 parts of one
complete N64 Classic Mini console (`lower_tub`, `upper_shell`, `front_bezel`, `power_slider`,
`reset_button`, `led_light_pipe`, `front_port_cover`, `4x n64_port_insert`) with `6.0 mm` XY
spacing inside the `256 x 256 mm` Bambu Lab P1S / X1C build plate, and writes
`export/plate/print_plate.step`.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cadquery as cq  # noqa: E402
from part import (  # noqa: E402
    cartridge_flaps,
    front_bezel,
    front_port_cover,
    led_light_pipe,
    n64_port_insert,
    power_slider,
    reset_button,
    usb_retainer_bracket,
)
from variant import lower_tub, upper_shell  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLATE_STEP = os.path.join(REPO, "export", "plate", "print_plate.step")
BED_XY = (256.0, 256.0)
SPACING_MM = 6.0

# Complete FDM part set for one N64 Classic Mini console (15 printed bodies total).
PLATE_BOM = (
    ("lower_tub", lower_tub, 1),
    ("upper_shell", upper_shell, 1),
    ("cartridge_flaps", cartridge_flaps, 1),
    ("front_bezel", front_bezel, 1),
    ("power_slider", power_slider, 1),
    ("reset_button", reset_button, 1),
    ("led_light_pipe", led_light_pipe, 1),
    ("front_port_cover", front_port_cover, 2),
    ("usb_retainer_bracket", usb_retainer_bracket, 2),
    ("n64_port_insert", n64_port_insert, 4),
)


def orient_to_bed(shape: cq.Shape, up: tuple[float, float, float]) -> cq.Shape:
    """Rotate `shape` so `up` points along `+Z` and shift `(xmin, ymin, zmin)` to `(0, 0, 0)`."""
    ux, uy, uz = (round(float(v), 4) for v in up)
    origin = cq.Vector(0.0, 0.0, 0.0)
    if (ux, uy, uz) == (0.0, 0.0, 1.0):
        rot = shape
    elif (ux, uy, uz) == (0.0, 0.0, -1.0):
        rot = shape.rotate(origin, cq.Vector(1.0, 0.0, 0.0), 180.0)
    elif (ux, uy, uz) == (0.0, -1.0, 0.0):
        rot = shape.rotate(origin, cq.Vector(1.0, 0.0, 0.0), -90.0)
    elif (ux, uy, uz) == (0.0, 1.0, 0.0):
        rot = shape.rotate(origin, cq.Vector(1.0, 0.0, 0.0), 90.0)
    elif (ux, uy, uz) == (1.0, 0.0, 0.0):
        rot = shape.rotate(origin, cq.Vector(0.0, 1.0, 0.0), -90.0)
    elif (ux, uy, uz) == (-1.0, 0.0, 0.0):
        rot = shape.rotate(origin, cq.Vector(0.0, 1.0, 0.0), 90.0)
    else:
        raise ValueError(f"unsupported non-axis PRINT_NORMAL: {up!r}")

    bb = rot.BoundingBox()
    return rot.moved(cq.Location(cq.Vector(-bb.xmin, -bb.ymin, -bb.zmin)))


def build_plate() -> tuple[cq.Compound, list[dict[str, object]]]:
    """Orient and shelf-pack all 12 printable FDM parts onto `Z = 0.0 mm`."""
    items = []
    for name, mod, qty in PLATE_BOM:
        oriented = orient_to_bed(mod.get_shape(), mod.PRINT_NORMAL)
        bb = oriented.BoundingBox()
        for idx in range(1, qty + 1):
            label = f"{name}_{idx}" if qty > 1 else name
            items.append((label, oriented, bb.xlen, bb.ylen, bb.zlen))

    max_row_w = BED_XY[0] - 2.0 * SPACING_MM
    placed_raw = []
    cur_x = 0.0
    cur_y = 0.0
    row_h = 0.0

    for label, shape, w, d, h in items:
        if cur_x > 0.0 and cur_x + w > max_row_w:
            cur_x = 0.0
            cur_y += row_h + SPACING_MM
            row_h = 0.0
        placed_raw.append((label, shape, cur_x, cur_y, w, d, h))
        cur_x += w + SPACING_MM
        row_h = max(row_h, d)

    total_w = max(x + w for _, _, x, _, w, _, _ in placed_raw)
    total_d = max(y + d for _, _, _, y, _, d, _ in placed_raw)
    shift_x = -total_w / 2.0
    shift_y = -total_d / 2.0

    solids = []
    placements: list[dict[str, object]] = []
    for label, shape, x, y, w, d, h in placed_raw:
        px = x + shift_x
        py = y + shift_y
        moved = shape.moved(cq.Location(cq.Vector(px, py, 0.0)))
        solids.append(moved)
        placements.append(
            {
                "label": label,
                "xmin": px,
                "xmax": px + w,
                "ymin": py,
                "ymax": py + d,
                "zmin": 0.0,
                "zmax": h,
            }
        )

    compound = cq.Compound.makeCompound(solids)
    return compound, placements


def export_plate(out_path: str = PLATE_STEP) -> tuple[cq.Compound, list[dict[str, object]]]:
    """Build the 12-part print plate and export it to `export/plate/print_plate.step`."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    compound, placements = build_plate()
    cq.exporters.export(compound, out_path)
    return compound, placements


def main() -> int:
    compound, placements = export_plate()
    bb = compound.BoundingBox()
    print(
        f"Exported {len(placements)} parts to {PLATE_STEP} "
        f"({bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm on Z=0)"
    )
    for p in placements:
        print(
            f"  - {p['label']:20s}: X=[{p['xmin']:+6.1f}, {p['xmax']:+6.1f}] "
            f"Y=[{p['ymin']:+6.1f}, {p['ymax']:+6.1f}] Z=[0.0, {p['zmax']:.1f}] mm"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
