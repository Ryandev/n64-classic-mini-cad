"""Fit report, body census, and pairwise collision check for the N64 Classic Mini (`build.py`).

Mirrors `GBA/CAD/lib/assembly/build.py`: summarises internal fit margins (Radxa X4 PCB to
recessed `120 mm` N64 waist, finned SoC heatsink plenum inside the `33.5 mm` barrel dome,
rear-right `25.5 mm` RJ45 bay, and M.2 2230 NVMe floor clearance) and checks pairwise
boolean interference across all assembled bodies.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402
from assembly import n64_mini  # noqa: E402
from component import radxa_x4  # noqa: E402
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common  # noqa: E402


def fit_report() -> dict[str, object]:
    """Return measured clearance margins of the internal compute & I/O stack inside the shell."""
    pcb_bb = radxa_x4.board_solid().BoundingBox()
    hs_bb = radxa_x4.heatsink_solid().BoundingBox()
    m2_bb = radxa_x4.m2_keepout().BoundingBox()
    rj_bb = radxa_x4.rj45_jack().BoundingBox()

    waist_inner_x = D.WAIST_HALF_W - D.SHELL_WALL_T
    dome_inner_z = D.SHELL_H - 2.40
    return {
        "shell_envelope_mm": (D.SHELL_W, D.SHELL_D, D.SHELL_H),
        "waist_outer_mm": 2.0 * D.WAIST_HALF_W,
        "radxa_pcb_mm": (pcb_bb.xlen, pcb_bb.ylen, pcb_bb.zlen),
        "waist_left_gap_mm": pcb_bb.xmin - (-waist_inner_x),
        "rj45_bay_avail_mm": waist_inner_x - pcb_bb.xmax,
        "rj45_to_pcb_gap_mm": rj_bb.xmin - pcb_bb.xmax,
        "heatsink_zmax_mm": hs_bb.zmax,
        "dome_plenum_mm": dome_inner_z - hs_bb.zmax,
        "m2_floor_gap_mm": m2_bb.zmin - D.FLOOR_T,
    }


def bodies() -> list[tuple[str, cq.Shape]]:
    """Return `(name, shape)` for every body in `n64_mini.named_bodies()`."""
    return [(name, shp) for name, _, shp in n64_mini.named_bodies()]


def interference(threshold_mm3: float = 0.01) -> list[tuple[str, str, float]]:
    """Return overlapping `(name_a, name_b, volume_mm3)` pairs exceeding `threshold_mm3`."""
    items = bodies()
    # Skip m2_2230_nvme keepout against radxa_x4 (whose model includes the M.2 socket)
    skip = {frozenset(("radxa_x4", "m2_2230_nvme"))}
    clashes = []
    for i, (na, sa) in enumerate(items):
        ba = sa.BoundingBox()
        for nb, sb in items[i + 1 :]:
            if frozenset((na, nb)) in skip:
                continue
            bb = sb.BoundingBox()
            if (
                ba.xmax <= bb.xmin
                or bb.xmax <= ba.xmin
                or ba.ymax <= bb.ymin
                or bb.ymax <= ba.ymin
                or ba.zmax <= bb.zmin
                or bb.zmax <= ba.zmin
            ):
                continue
            com = BRepAlgoAPI_Common(sa.wrapped, sb.wrapped)
            com.Build()
            if com.IsDone():
                v = cq.Shape.cast(com.Shape()).Volume()
                if v > threshold_mm3:
                    clashes.append((na, nb, v))
    return clashes


def get_shape() -> cq.Shape:
    """Return the complete N64 Classic Mini assembly compound."""
    return n64_mini.get_shape(include_electronics=True)


if __name__ == "__main__":
    rep = fit_report()
    for k, v in rep.items():
        print(f"  {k:24s}: {v}")
    bad = interference()
    print(f"  interference pairs      : {len(bad)}")
    for na, nb, vol in bad:
        print(f"    CLASH {na} / {nb}: {vol:.3f} mm^3")
