"""Gate checks for the active cooling (REQ-04): fit, contact, open vents and the thermal budget.

Every row measures the solids (boolean common volume, distance, vertical ray classification).
The thermal rows feed `thermal.py` with areas measured here, never typed-in constants: a vent
only counts if a boolean proves it goes right through its wall.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
import printable  # noqa: E402
import thermal  # noqa: E402
from assembly import datum as D  # noqa: E402
from assembly import n64_mini  # noqa: E402
from component import hsb26_343408, sunon_mf30060v2  # noqa: E402
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common  # noqa: E402
from OCP.BRepExtrema import BRepExtrema_DistShapeShape  # noqa: E402
from part import cooling_duct, cooling_hood, duct_floor  # noqa: E402
from part.shared import n64_contours as C  # noqa: E402
from subassembly import cooling_mech  # noqa: E402
from testing import probe  # noqa: E402
from variant import lower_tub, upper_shell  # noqa: E402

CLEAR_MM3 = 0.01
# Parts meant to touch (contact, not interference): checked by distance instead.
CONTACTS = {
    ("hsb26_heatsink", "cooling_duct"),
    ("fan_mf30060v2", "cooling_duct"),
    ("fan_mf30060v2", "cooling_hood"),
    ("cooling_duct", "cooling_hood"),
    ("feet_sj5012", "lower_tub"),
}
SKIP_OTHERS = {
    "hsb26_heatsink",
    "fan_mf30060v2",
    "cooling_duct",
    "duct_floor",
    "cooling_hood",
    "feet_sj5012",
}
REQUIRED_TJ_6W = thermal.TJ_TARGET_C


def _common(a: cq.Shape, b: cq.Shape) -> float:
    op = BRepAlgoAPI_Common(a.wrapped, b.wrapped)
    op.Build()
    if not op.IsDone():
        return -1.0
    return cq.Shape.cast(op.Shape()).Volume()


def _distance(a: cq.Shape, b: cq.Shape) -> float:
    d = BRepExtrema_DistShapeShape(a.wrapped, b.wrapped)
    d.Perform()
    return d.Value()


def _open_area(wall: cq.Shape, cutters: list[cq.Solid], axis: str) -> tuple[float, int]:
    """Sum of cutter cross-sections whose column through `wall` holds no material."""
    area, n_open = 0.0, 0
    for c in cutters:
        bb = c.BoundingBox()
        if axis == "z":
            column = cq.Solid.makeBox(bb.xlen, bb.ylen, 60.0, cq.Vector(bb.xmin, bb.ymin, -10.0))
            section = bb.xlen * bb.ylen
        else:  # through a side or rear wall: the cutter spans the wall, so test the cutter itself
            column = c
            section = (bb.ylen * bb.zlen) if axis == "x" else (bb.xlen * bb.zlen)
        if _common(wall, column) <= CLEAR_MM3:
            area += section
            n_open += 1
    return area, n_open


def _louver_cutters() -> list[cq.Solid]:
    return [
        cq.Solid.makeBox(x1 - x0, y1 - y0, 12.0, cq.Vector(x0, y0, 22.0))
        for x0, y0, x1, y1 in C.TOP_LOUVER_BOXES_50
    ]


def _rear_slit_cutters() -> list[cq.Solid]:
    return [
        cq.Solid.makeBox(x1 - x0, 5.5, 4.6, cq.Vector(x0, 46.0, 19.5))
        for x0, _, x1, _ in C.TOP_LOUVER_BOXES_50[6:19]
    ]


def _floor_perimeter() -> float:
    """The N64 plan outline's perimeter: the edge air crosses to get under the floor."""
    prism = C.n64_plan_prism(z0=0.0, height=1.0)
    bottom = next(f for f in prism.Faces() if f.BoundingBox().zmax < 0.01)
    return bottom.outerWire().Length()


def thermal_inputs() -> tuple[thermal.Inputs, dict[str, float]]:
    """Measure every area the model uses."""
    shell = upper_shell.get_shape()
    tub = lower_tub.get_shape()
    louver_area, n_lou = _open_area(shell, _louver_cutters(), "z")
    rear_area, n_rear = _open_area(shell, _rear_slit_cutters(), "y")
    floor_area, n_floor = _open_area(tub, lower_tub.floor_vent_cutters(), "z")
    side_area, n_side = _open_area(tub, lower_tub.waist_slot_cutters(), "x")
    # Hood: air reaches the fan top three ways in parallel: straight down through the louvers
    # above the fan, over its rear edge, and along its two sides (each gap = roof - fan top).
    fan_x1, fan_y1 = D.FAN_X0 + D.FAN_W, D.FAN_Y0 + D.FAN_W
    fan_top = D.FAN_Z0 + D.FAN_H
    direct = sum(
        max(0.0, min(x1, fan_x1) - max(x0, D.FAN_X0))
        * max(0.0, min(y1, fan_y1) - max(y0, D.FAN_Y0))
        for x0, y0, x1, y1 in C.TOP_LOUVER_BOXES_50
    )
    rear_gap = cooling_hood.roof_z(D.FAN_X0 + D.FAN_W / 2.0, fan_y1) - fan_top
    side_len = fan_y1 - cooling_hood.A_Y0
    side_y = (fan_y1 + cooling_hood.A_Y0) / 2.0
    side_gaps = [cooling_hood.roof_z(x, side_y) - fan_top for x in (D.FAN_X0, fan_x1)]
    a_hood = direct + max(0.0, rear_gap) * D.FAN_W + sum(max(0.0, g) * side_len for g in side_gaps)
    # Narrowest turn: under the fan's rear edge (fan bottom to skirt line) x duct inner width, or
    # the chamber between fan and fins, whichever is smaller.
    inner_w = cooling_duct.X_IN_R - cooling_duct.X_IN_L
    under_fan = (D.FAN_Z0 - cooling_duct.Z_SKIRT) * inner_w
    chamber = (D.HS_Y0 - (D.FAN_Y0 + D.FAN_W)) * inner_w
    a_turn = min(under_fan, chamber)
    perimeter = _floor_perimeter()
    i = thermal.Inputs(
        fan_q_max=sunon_mf30060v2.Q_MAX_M3S,
        fan_p_max=sunon_mf30060v2.P_MAX_PA,
        hs_r_by_v=hsb26_343408.R_BY_VELOCITY,
        hs_width=D.HS_W,
        hs_fin_h=D.HS_FIN_H,
        hs_rows=D.HS_ROWS,
        hs_pin=D.HS_PIN,
        a_louver=louver_area,
        a_hood=a_hood,
        a_turn=a_turn,
        a_floor=floor_area,
        a_feet_gap=perimeter * D.FOOT_H,
        a_side=side_area,
        a_rear=rear_area,
    )
    counts = {
        "louvers": n_lou,
        "rear": n_rear,
        "floor": n_floor,
        "side": n_side,
        "perimeter": perimeter,
    }
    return i, counts


def plenum_leaks(step: float = 0.5) -> tuple[int, list[str], list[str]]:
    """Flood air from inside the plenum through a voxel grid of every body near the duct.

    Air may only leave through the heat sink's rear face (the designed outlet). Any filled voxel
    on the region's boundary elsewhere is a leak path. Openings narrower than one `step` read as
    sealed.

    Also returns the fan-outlet spots that blow outside the plenum: every voxel under the fan's
    bore must be solid (blocked) or flooded plenum air. The flood treats the fan as a wall, so
    without this a bore overhanging the duct's front wall bypassed the heat sink unseen.
    """
    import numpy as np
    from OCP.gp import gp_Dir, gp_Lin, gp_Pnt
    from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector

    x0, x1 = cooling_duct.X_OUT_L - 1.5, cooling_duct.X_OUT_R + 1.5
    y0, y1 = D.FAN_Y0 - 1.5, cooling_duct.Y_REAR + 1.0  # whole fan footprint
    z0, z1 = D.RADXA_PCB_Z1 - 1.0, cooling_duct.Z_COVER1 + 1.5
    xs = np.arange(x0 + step / 2, x1, step)
    ys = np.arange(y0 + step / 2, y1, step)
    zs = np.arange(z0 + step / 2, z1, step)
    # Rays run up the voxel corners; a voxel is solid if solid touches it anywhere, so every gap
    # narrower than one voxel reads as sealed, consistently (not by where the centres fall).
    cx = np.append(xs - step / 2, xs[-1] + step / 2)
    cy = np.append(ys - step / 2, ys[-1] + step / 2)
    corner = np.zeros((len(cx), len(cy), len(zs)), dtype=bool)
    region = cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0)).BoundingBox()
    # The fan is the pump: treat its whole envelope as a wall (the assembly models its bore open).
    # The board's M2.5 screw heads are real bodies the assembly doesn't model.
    heads = [
        cq.Solid.makeCylinder(
            D.BOARD_SCREW_HEAD_D / 2.0, D.BOARD_SCREW_HEAD_H, cq.Vector(hx, hy, D.RADXA_PCB_Z1)
        )
        for hx, hy in D.radxa_hole_centres()
    ]
    shapes = [s for _, _, s in n64_mini.named_bodies()] + [sunon_mf30060v2.envelope()] + heads
    shapes = [sh for sh in shapes if sh.BoundingBox().zmax > z0 and sh.BoundingBox().zmin < z1]
    for sh in shapes:
        for so in sh.Solids():
            bb = so.BoundingBox()
            if (
                bb.xmax < region.xmin
                or bb.xmin > region.xmax
                or bb.ymax < region.ymin
                or bb.ymin > region.ymax
            ):
                continue
            it = IntCurvesFace_ShapeIntersector()
            it.Load(so.wrapped, 1e-4)
            for i, x in enumerate(cx):
                if x < bb.xmin - step or x > bb.xmax + step:
                    continue
                for j, y in enumerate(cy):
                    if y < bb.ymin - step or y > bb.ymax + step:
                        continue
                    it.Perform(gp_Lin(gp_Pnt(x, y, z0 - 20.0), gp_Dir(0, 0, 1)), 0.0, 80.0)
                    hz = sorted({round(it.Pnt(k).Z(), 4) for k in range(1, it.NbPnt() + 1)})
                    for a, b in zip(hz[0::2], hz[1::2]):
                        corner[i, j, (zs + step / 2 >= a) & (zs - step / 2 <= b)] = True
    solid = corner[:-1, :-1] | corner[1:, :-1] | corner[:-1, 1:] | corner[1:, 1:]
    outlet_j = ys > cooling_duct.Y_REAR - step  # the heat sink's rear face and beyond
    seed = (
        int(np.argmin(abs(xs - (D.FAN_X0 + D.FAN_W / 2.0)))),
        int(np.argmin(abs(ys - (cooling_duct.Y_PLATE1 - 3.0)))),
        int(np.argmin(abs(zs - (D.FAN_Z0 - 2.5)))),
    )
    if solid[seed]:
        return -1, ["seed voxel is solid: the plenum is not where the duct says it is"], []
    from collections import deque

    parent: dict[tuple[int, int, int], tuple[int, int, int]] = {seed: seed}
    queue = deque([seed])
    first_leak = None
    leaks: list[str] = []
    n = 0
    nx, ny, nz = solid.shape
    while queue:
        i, j, k = queue.popleft()
        n += 1
        if outlet_j[j]:
            continue  # reached the outlet: air leaves the duct here, as designed
        if i in (0, nx - 1) or j in (0, ny - 1) or k in (0, nz - 1):
            first_leak = first_leak or (i, j, k)
            continue
        for di, dj, dk in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            nb = (i + di, j + dj, k + dk)
            if nb not in parent and not solid[nb]:
                parent[nb] = (i, j, k)
                queue.append(nb)
    if first_leak is not None:
        path = [first_leak]
        while path[-1] != seed:
            path.append(parent[path[-1]])
        path.reverse()
        # report where the path turns: the route the air takes from the plenum to the leak
        turns = (
            [path[0]]
            + [
                p
                for a, p, b in zip(path, path[1:], path[2:])
                if (p[0] - a[0], p[1] - a[1], p[2] - a[2])
                != (b[0] - p[0], b[1] - p[1], b[2] - p[2])
            ]
            + [path[-1]]
        )
        leaks = [f"({xs[i]:.1f}, {ys[j]:.1f}, {zs[k]:.1f})" for i, j, k in turns[-12:]]
    # The voxel layer just under the fan (its top at or below the fan's bottom face).
    k_out = int(np.nonzero(zs + step / 2 <= D.FAN_Z0 + 1e-9)[0][-1])
    fcx, fcy, r = D.FAN_X0 + D.FAN_W / 2.0, D.FAN_Y0 + D.FAN_W / 2.0, D.FAN_BORE_D / 2.0
    bypass = [
        f"({x:.2f}, {y:.2f})"
        for i, x in enumerate(xs)
        for j, y in enumerate(ys)
        if (x - fcx) ** 2 + (y - fcy) ** 2 <= r * r
        and not solid[i, j, k_out]
        and (i, j, k_out) not in parent
    ]
    return n, leaks, bypass


def check_all():
    rows = []
    mine = cooling_mech.bodies()
    others = [(n, s) for n, _, s in n64_mini.named_bodies() if n not in SKIP_OTHERS]

    # 1. G13: no cooling part enters any other body (contacts are checked by distance below).
    clashes = []
    for a_name, a in mine:
        for b_name, b in others + [x for x in mine if x[0] != a_name]:
            if (a_name, b_name) in CONTACTS or (b_name, a_name) in CONTACTS:
                continue
            if a_name > b_name and any(b_name == m for m, _ in mine):
                continue  # each cooling pair once
            v = _common(a, b)
            if v > CLEAR_MM3 or v < 0:
                clashes.append(f"{a_name}/{b_name}={v:.2f}")
    rows.append(
        (
            "G13_COOL  heat sink, fan, duct, hood and feet clear every other body",
            not clashes,
            "0 overlaps" if not clashes else "overlap mm3: " + ", ".join(clashes),
        )
    )

    # 2. Contacts that do the work: cover clamps the pins, sink sits on the die, fan seats.
    hs = hsb26_343408.placed()
    duct = cooling_duct.get_shape()
    # The glued-in floor, measured both ways on the solids (Gemini review #4: the whole-solid
    # distance let wall contact pass as "seated" and the frame gap was only the constant):
    #   - the frame gap, in a slab through the plate's mid-thickness (walls, not the ledge);
    #   - the seat, the plate's top skin against the duct just above it: the ledge touches, the
    #     walls are FLOOR_GAP away sideways, so a missing ledge reads as the wall gap.
    floor = cooling_duct.floor_plate()
    z1 = cooling_duct.Z_PLATE1
    frame_gap = probe.slice_gap(floor, duct, "z", (cooling_duct.Z_PLATE0 + z1) / 2.0)
    big = 400.0
    top_skin = floor.intersect(
        cq.Solid.makeBox(big, big, 0.1, cq.Vector(-big / 2, -big / 2, z1 - 0.1))
    )
    above = duct.intersect(cq.Solid.makeBox(big, big, 0.1, cq.Vector(-big / 2, -big / 2, z1)))
    seat = _distance(top_skin, above)
    rows.append(
        (
            "FLOOR_SEAT duct floor plate seats on its ledge, clear of the frame walls",
            # GBA's measured PETG locating band, not the constant (which a typo would move too)
            seat <= 0.01 and 0.10 <= frame_gap <= 0.20,
            f"plate to ledge {seat:.3f} mm (must touch); frame gap {frame_gap:.3f} mm a side "
            f"measured (locating band 0.10..0.20, for the glue)",
        )
    )
    fan = sunon_mf30060v2.envelope()
    soc = cq.Solid.makeBox(
        D.SOC_X1 - D.SOC_X0,
        D.SOC_Y1 - D.SOC_Y0,
        D.SOC_H,
        cq.Vector(D.SOC_X0, D.SOC_Y0, D.RADXA_PCB_Z1),
    )
    clamp = _distance(hs, duct)
    seat = _distance(fan, duct)
    bond = _distance(hs, soc)
    rows.append(
        (
            "COOL_SEAT duct clamps the pins, fan seats, sink one bond line off the die",
            clamp <= 0.01
            and _common(hs, duct) <= CLEAR_MM3
            and seat <= 0.01
            and abs(bond - D.PASTE_T) <= 0.01,
            f"cover-to-pins {clamp:.3f} mm, fan-to-seat {seat:.3f} mm, "
            f"sink-to-die {bond:.3f} mm (paste {D.PASTE_T})",
        )
    )

    # 2a. HS_STOP (C9): pushed 0.5 mm any way sideways, the sink runs into the duct (skirts in X,
    # the corner stops in Y), so it can't slide off the die
    free = []
    for label, (dx, dy) in (
        ("+X", (0.5, 0)),
        ("-X", (-0.5, 0)),
        ("+Y", (0, 0.5)),
        ("-Y", (0, -0.5)),
    ):
        if hs.translate(cq.Vector(dx, dy, 0.0)).intersect(duct).Volume() <= 1e-3:
            free.append(label)
    rows.append(
        (
            "HS_STOP   heat sink can't slide off the die: duct stops it within 0.5 mm every way",
            not free,
            "skirts stop it in X, corner stops in Y (0.3 mm clear)"
            if not free
            else f"slides more than 0.5 mm towards {', '.join(free)}",
        )
    )

    # 2b. Clamp: the cradle above the die compresses the pad on the cover by 20-70 %.
    from OCP.gp import gp_Dir, gp_Lin, gp_Pnt

    it = cooling_hood._roof_intersector()
    it.Perform(
        gp_Lin(gp_Pnt(D.SOC_CX, D.SOC_CY, cooling_duct.Z_COVER1), gp_Dir(0, 0, 1)), 0.0, 20.0
    )
    hits = [it.Pnt(k).Z() for k in range(1, it.NbPnt() + 1)]
    gap = (min(hits) - cooling_duct.Z_COVER1) if hits else float("inf")
    squeeze = 1.0 - gap / D.CLAMP_PAD_T
    rows.append(
        (
            "CLAMP     closing the shell compresses the pad over the die by 20-70 %",
            0.2 <= squeeze <= 0.7,
            f"cradle {gap:.2f} mm above the cover at the die centre; {D.CLAMP_PAD_T} mm pad "
            f"compressed {squeeze * 100:.0f} %",
        )
    )

    # 2c. Seal: air pushed into the plenum can only leave through the pin fins.
    n_air, leaks, bypass = plenum_leaks()
    rows.append(
        (
            "COOL_SEAL plenum air leaves only through the heat sink (openings >= 0.5 mm)",
            n_air > 0 and not leaks,
            f"{n_air} air voxels reached; "
            + ("no leak" if not leaks else "leak route ... " + " -> ".join(leaks)),
        )
    )
    # 2d. The fan blows only into the plenum: the thermal model sends its whole flow through the
    # pins, so any bore area over open case air is a bypass the model can't see.
    rows.append(
        (
            "COOL_FAN  every part of the fan's bore blows into the plenum or onto a wall",
            n_air > 0 and not bypass,
            "whole bore covered"
            if not bypass
            else f"{len(bypass) * 0.25:.0f} mm2 of bore over open case air, e.g. "
            + ", ".join(bypass[:3] + bypass[-3:]),
        )
    )

    # 3. Printability of the three printed parts.
    rows.extend(
        printable.check_part("cooling_duct", duct, up=cooling_duct.PRINT_NORMAL, min_wall_mm=0.8)
    )
    rows.extend(
        printable.check_part(
            "duct_floor", cooling_duct.floor_plate(), up=duct_floor.PRINT_NORMAL, min_wall_mm=0.8
        )
    )
    rows.extend(
        printable.check_part(
            "cooling_hood", cooling_hood.get_shape(), up=cooling_hood.PRINT_NORMAL, min_wall_mm=0.8
        )
    )

    # 4. Openings, measured, and the thermal budget computed from them.
    i, counts = thermal_inputs()
    rows.append(
        (
            "COOL_VENT every louver, floor vent and waist slot goes right through",
            counts["louvers"] == len(_louver_cutters())
            and counts["floor"] == len(lower_tub.floor_vent_cutters())
            and counts["side"] == len(lower_tub.waist_slot_cutters()),
            f"open: louvers {counts['louvers']}/25 ({i.a_louver:.0f} mm2), "
            f"floor {counts['floor']}/{len(lower_tub.floor_vent_cutters())} "
            f"({i.a_floor:.0f} mm2), waist {counts['side']}/28 ({i.a_side:.0f} mm2), rear slits "
            f"{counts['rear']}/13 ({i.a_rear:.0f} mm2); feet gap {i.a_feet_gap:.0f} mm2 "
            f"({counts['perimeter']:.0f} mm perimeter x {D.FOOT_H} mm)",
        )
    )
    try:
        r6 = thermal.solve(i, 6.0)
        r10 = thermal.solve(i, 10.0)
    except ValueError as exc:
        rows.append(
            ("THERMAL   N100 junction at stock PL1 6 W <= 85 C (30 C room)", False, str(exc))
        )
        return rows
    rows.append(
        (
            f"THERMAL   N100 junction at stock PL1 6 W <= {REQUIRED_TJ_6W:.0f} C (30 C room)",
            r6.tj <= REQUIRED_TJ_6W,
            f"fan at {r6.q * 1e3:.2f} L/s against {r6.dp:.0f} Pa; "
            f"sink sees {r6.v_approach / thermal.LFM:.0f} LFM "
            f"-> {r6.r_hs:.2f} K/W ({sunon_mf30060v2.PART}); "
            f"Tj {r6.tj:.1f} C at 6 W, {r10.tj:.1f} C at 10 W "
            f"(throttles at {thermal.TJ_MAX_C:.0f} C); "
            f"hood {i.a_hood:.0f} mm2, turn {i.a_turn:.0f} mm2",
        )
    )
    rows.append(
        (
            "THERMAL   case exhaust air (SSD, RAM) <= 60 C at stock power",
            r6.t_exhaust <= 60.0,
            f"exhaust {r6.t_exhaust:.1f} C (N100 6 W + 3 W board, {r6.q * 1e3:.2f} L/s)",
        )
    )
    return rows


if __name__ == "__main__":
    results = check_all()
    failed = 0
    for label, ok, msg in results:
        tag = "PASS" if ok else "FAIL"
        print(f"  {tag}  {label}")
        print(f"        {msg}")
        if not ok:
            failed += 1
    sys.exit(1 if failed else 0)
