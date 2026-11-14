"""3D Tetrahedral Finite Element Analysis (`Gmsh` + `CalculiX ccx`) for the N64 Classic Mini.

Runs 4 linear-elastic 3D tetrahedral (`C3D10`, mesh-converged) FEA load cases
(`E = 2200 MPa`, `nu = 0.36`,
conservative FDM PETG/PLA inter-layer yield limit `25.0 MPa`, in-plane yield `45.0 MPa`) on the
actual B-Rep solids from `lib/part/` and `lib/variant/`:
  1. `LC1_BUTTON_MASH_50N`: `part/usb_retainer_bracket.py` under `50 N` (`-Z`) heavy thumb mash on
     `Face70` (the button stop, `BUTTON_STOP_Z`), `15 N` (`-Y`) off-center lateral tilt on the
     `Ø2.80 mm` guide pole,
     and `15 N` (`+Z`) upward USB-A cable pry under the `Z = 16.85 mm` top retainer bridge.
  2. `LC2_TUB_USB_AND_OMRON`: `variant/lower_tub.py` front USB-A & Omron bay under simultaneous
     `40 N` (`+Y`) USB-A plug insertion, `30 N` (`-Y`) USB-A cable yank against the `Z = 5.80 ..
     10.80 mm` pull-stop step, and `50 N` (`-Z`) rear button mash on the button stop post
     (`BUTTON_STOP_Z`).
  3. `LC3_UPPER_SHELL_DOME_100N`: `variant/upper_shell.py` full top shell under a `100 N` (`~10 kgf`
     `-Z`) crush load across the central barrel dome & 25 parabolic cooling louvers, checking peak
     Von Mises stress, dome vertical sag, and `POWER`/`RESET` guide-chimney radial `XY` distortion.
  4. `LC4_RADXA_RJ45_STANDOFFS`: `variant/lower_tub.py` rear chassis & standoffs under `30 N` (`-Y`)
     rear cable insertion + `60 N` (`-Z`) M2.5 screw clamp preload across the 4 Radxa X4 standoffs
     (`Z = 8.20 mm`) and 2 RJ45 standoffs (`Z = 5.60 mm`).
"""

from __future__ import annotations

import argparse
import glob
import math
import os
import shutil
import subprocess
import sys
import tempfile
from typing import Callable

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402
from assembly.datum import BUTTON_STOP_Z as STOP_Z  # noqa: E402
from assembly.datum import CORNER_BOSS_XS as CORNER_XS  # noqa: E402
from assembly.datum import CORNER_BOSS_YS as CORNER_YS  # noqa: E402
from assembly.datum import FOOT_D  # noqa: E402
from component import omron_ss5gl  # noqa: E402
from part import usb_retainer_bracket  # noqa: E402
from variant import lower_tub, upper_shell  # noqa: E402

PETG_E_MPA = 2200.0
PETG_NU = 0.36


def _find_binary(name: str) -> str:
    """Locate `gmsh` or `ccx` on `PATH` or inside a running FreeCAD AppImage mount."""
    found = shutil.which(name)
    if found:
        return found
    # FreeCAD AppImage mounts are /tmp/.mount_FreeCA<random> (C4: a lowercase glob never matched)
    matches = sorted(glob.glob(f"/tmp/.mount_[Ff]ree[Cc][Aa]*/usr/bin/{name}"))
    if matches:
        return matches[-1]
    raise RuntimeError(f"FEM binary {name!r} not on PATH (environment.yml) or in FreeCAD")


ORDER = 2  # 10-node tetrahedra (C3D10): 4-node ones are too stiff to resolve stress (C4)
REFINE = 0.7  # the convergence mesh is this much finer
CONVERGED = 0.15  # the two meshes must agree this closely
# Stress is judged at this percentile of the integration points clear of loads and supports:
# the model's sharp inside corners are true stress singularities, so the maximum never converges
STRESS_PERCENTILE = 0.99


def _parse_inp(path: str) -> tuple[dict[int, tuple[float, float, float]], list[list[int]]]:
    """Nodes and C3D10 elements (id + 10 nodes, possibly wrapped over lines) from Gmsh's INP."""
    nodes: dict[int, tuple[float, float, float]] = {}
    elems: list[list[int]] = []
    mode: str | None = None
    pending: list[int] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("**"):
                continue
            if s.startswith("*"):
                mode = "node" if s.upper().startswith("*NODE") else None
                if s.upper().startswith("*ELEMENT") and "C3D10" in s.upper():
                    mode = "c3d10"
                continue
            if mode == "node":
                parts = [p.strip() for p in s.split(",")]
                nodes[int(parts[0])] = (float(parts[1]), float(parts[2]), float(parts[3]))
            elif mode == "c3d10":
                pending += [int(p) for p in s.split(",") if p.strip()]
                if len(pending) >= 11:
                    elems.append(pending[:11])
                    pending = []
    if not elems:
        raise RuntimeError(f"{path}: no C3D10 elements (Gmsh -order {ORDER} produced none)")
    return nodes, elems


def _near_any(points: list[tuple[float, float, float]], radius: float):
    """A test `f(xyz) -> bool`: is xyz within `radius` of any of `points` (grid hashed)."""
    grid: dict[tuple[int, int, int], list[tuple[float, float, float]]] = {}
    for p in points:
        grid.setdefault(tuple(int(math.floor(c / radius)) for c in p), []).append(p)
    r2 = radius * radius

    def near(xyz: tuple[float, float, float]) -> bool:
        cx, cy, cz = (int(math.floor(c / radius)) for c in xyz)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for q in grid.get((cx + dx, cy + dy, cz + dz), ()):
                        if sum((a - b) ** 2 for a, b in zip(xyz, q, strict=True)) <= r2:
                            return True
        return False

    return near


def solve_calculix(
    name: str,
    shape: cq.Shape,
    clmin: float,
    clmax: float,
    fix_pred: Callable[[float, float, float], bool],
    loads: list[tuple[Callable[[float, float, float], bool], tuple[float, float, float]]],
    out_dir: str | None = None,
    roller_pred: Callable[[float, float, float], bool] | None = None,
    watch_pred: Callable[[float, float, float], bool] | None = None,
) -> dict[str, object]:
    """Mesh `shape` with Gmsh (C3D10), solve linear statics with CalculiX, return metrics.

    `fix_pred` nodes are held in all directions; `roller_pred` nodes only vertically (a part
    resting on a surface). `max_vm_mpa` is the `STRESS_PERCENTILE` von Mises stress away from
    the loaded and held nodes (within `2 x clmax` of them a point load or a clamp makes a spike
    that grows as the mesh is refined); `peak_vm_mpa` is the raw peak, for information.
    `watch_uz_mm` is the largest downward movement of the `watch_pred` nodes (a stop face whose
    give matters on its own, not just the part's largest movement anywhere).
    """
    gmsh_bin = _find_binary("gmsh")
    ccx_bin = _find_binary("ccx")

    with tempfile.TemporaryDirectory(prefix=f"n64_fem_{name}_") as tmp:
        work_dir = os.path.join(out_dir, name) if out_dir else tmp
        os.makedirs(work_dir, exist_ok=True)

        step_f = os.path.join(work_dir, "part.step")
        inp_mesh = os.path.join(work_dir, "mesh.inp")
        cq.exporters.export(shape, step_f)
        cmd_gmsh = [
            # straight-sided C3D10: curving mid-edge nodes onto the tub's surfaces inverted some
            # elements ("nonpositive jacobian" in CalculiX)
            gmsh_bin, step_f, "-3", "-optimize_netgen", "-order", str(ORDER),
            "-setnumber", "Mesh.SecondOrderLinear", "1",
            "-clmin", str(clmin), "-clmax", str(clmax),
            "-format", "inp", "-o", inp_mesh, "-v", "1",
        ]  # fmt: skip
        subprocess.run(cmd_gmsh, check=True, capture_output=True, text=True)
        nodes, elems = _parse_inp(inp_mesh)

        fix_nodes = [nid for nid, xyz in nodes.items() if fix_pred(*xyz)]
        if not fix_nodes:
            raise RuntimeError(f"{name}: fix_pred matched 0 nodes")
        roll_nodes = (
            [n for n, xyz in nodes.items() if roller_pred(*xyz) and n not in set(fix_nodes)]
            if roller_pred
            else []
        )
        held = set(fix_nodes) | set(roll_nodes)

        job_inp = os.path.join(work_dir, "job.inp")
        load_nodes: list[int] = []
        with open(job_inp, "w", encoding="utf-8") as out:
            out.write(f"*HEADING\n{name}\n*NODE, NSET=Nall\n")
            for nid, (x, y, z) in sorted(nodes.items()):
                out.write(f"{nid}, {x:.6f}, {y:.6f}, {z:.6f}\n")
            out.write("*ELEMENT, TYPE=C3D10, ELSET=Eall\n")
            for idx, el in enumerate(elems, 1):
                ns = el[1:]
                out.write(f"{idx}, " + ", ".join(str(n) for n in ns[:7]) + ",\n")
                out.write(", ".join(str(n) for n in ns[7:]) + "\n")
            for set_name, members in (("Nfix", fix_nodes), ("Nroll", roll_nodes)):
                if members:
                    out.write(f"*NSET, NSET={set_name}\n")
                    for k in range(0, len(members), 10):
                        out.write(", ".join(str(n) for n in members[k : k + 10]) + "\n")
            out.write(f"*MATERIAL, NAME=PETG\n*ELASTIC\n{PETG_E_MPA:.1f}, {PETG_NU:.3f}\n")
            out.write("*SOLID SECTION, ELSET=Eall, MATERIAL=PETG\n")
            out.write("*STEP\n*STATIC\n*BOUNDARY\nNfix, 1, 3, 0.0\n")
            if roll_nodes:
                out.write("Nroll, 3, 3, 0.0\n")
            out.write("*CLOAD\n")
            for load_pred, (fx, fy, fz) in loads:
                lnodes = [n for n, xyz in nodes.items() if load_pred(*xyz) and n not in held]
                if not lnodes:
                    raise RuntimeError(f"{name}: load predicate matched 0 free nodes")
                load_nodes += lnodes
                for nid in lnodes:
                    for dof, f in ((1, fx), (2, fy), (3, fz)):
                        if abs(f) > 1e-9:
                            out.write(f"{nid}, {dof}, {f / len(lnodes):.6f}\n")
            out.write("*NODE FILE\nU\n*EL FILE\nS\n")
            out.write("*NODE PRINT, NSET=Nall\nU\n*EL PRINT, ELSET=Eall\nS\n*END STEP\n")

        subprocess.run([ccx_bin, "job"], cwd=work_dir, check=True, capture_output=True, text=True)

        near_bc = _near_any([nodes[n] for n in (*held, *load_nodes)], 2.0 * clmax)
        centroid = {
            idx: tuple(sum(nodes[n][k] for n in el[1:5]) / 4.0 for k in range(3))
            for idx, el in enumerate(elems, 1)
        }
        away = {idx for idx, c in centroid.items() if not near_bc(c)}
        max_u, max_chimney_xy_u, peak_vm, watch_uz = 0.0, 0.0, 0.0, 0.0
        max_u_at = (0.0, 0.0, 0.0)
        away_vm: list[float] = []
        with open(os.path.join(work_dir, "job.dat"), encoding="utf-8") as f:
            sec: str | None = None
            for line in f:
                s = line.strip()
                if not s:
                    continue
                if "displacements" in s:
                    sec = "u"
                    continue
                if "stresses" in s:
                    sec = "s"
                    continue
                p = s.split()
                if sec == "u" and len(p) == 4 and p[0].isdigit():
                    ux, uy, uz = float(p[1]), float(p[2]), float(p[3])
                    nx, ny, nz = nodes[int(p[0])]
                    if math.sqrt(ux * ux + uy * uy + uz * uz) > max_u:
                        max_u, max_u_at = math.sqrt(ux * ux + uy * uy + uz * uz), (nx, ny, nz)
                    if watch_pred is not None and watch_pred(nx, ny, nz):
                        watch_uz = max(watch_uz, -uz)
                    if abs(abs(nx) - 32.32) <= 7.0 and -39.0 <= ny <= -19.0 and 23.5 <= nz <= 30.0:
                        max_chimney_xy_u = max(max_chimney_xy_u, math.sqrt(ux * ux + uy * uy))
                elif sec == "s" and len(p) == 8 and p[0].isdigit():
                    sxx, syy, szz = float(p[2]), float(p[3]), float(p[4])
                    sxy, sxz, syz = float(p[5]), float(p[6]), float(p[7])
                    vm = math.sqrt(
                        0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 + (szz - sxx) ** 2)
                        + 3.0 * (sxy**2 + sxz**2 + syz**2)
                    )
                    peak_vm = max(peak_vm, vm)
                    if int(p[0]) in away:
                        away_vm.append(vm)

        if not away_vm:
            raise RuntimeError(f"{name}: no element is clear of the loads and supports")
        away_vm.sort()
        max_vm = away_vm[min(len(away_vm) - 1, int(STRESS_PERCENTILE * len(away_vm)))]
        return {
            "name": name,
            "nodes": len(nodes),
            "elems": len(elems),
            "max_u_mm": max_u,
            "max_u_at": max_u_at,
            "load_nodes": len(load_nodes),
            "max_chimney_xy_u_mm": max_chimney_xy_u,
            "watch_uz_mm": watch_uz,
            "max_vm_mpa": max_vm,
            "peak_vm_mpa": peak_vm,
            "frd_path": os.path.join(work_dir, "job.frd") if out_dir else None,
        }


def solve_converged(name: str, shape: cq.Shape, clmin: float, clmax: float, **kw) -> dict:
    """Solve on the given mesh and on one `REFINE` x finer; report the fine one and the change."""
    coarse = solve_calculix(name, shape, clmin, clmax, **kw)
    fine = solve_calculix(f"{name}_fine", shape, clmin * REFINE, clmax * REFINE, **kw)
    for key in ("max_vm_mpa", "max_u_mm"):
        c, f = float(coarse[key]), float(fine[key])
        fine[f"{key}_change"] = abs(f - c) / f if f > 0 else 0.0
    fine["converged"] = all(fine[f"{k}_change"] <= CONVERGED for k in ("max_vm_mpa", "max_u_mm"))
    return fine


def _row(label: str, r: dict, vm_limit: float, u_limit: float) -> tuple[str, bool, str]:
    vm, u = float(r["max_vm_mpa"]), float(r["max_u_mm"])
    ok = vm <= vm_limit and u <= u_limit and bool(r["converged"])
    return (
        label,
        ok,
        f"{r['elems']} C3D10: von Mises {vm:.2f} MPa (p{100 * STRESS_PERCENTILE:.0f}, away from "
        f"loads/supports; limit "
        f"{vm_limit:.1f}; raw peak {float(r['peak_vm_mpa']):.1f}), disp {u:.3f} mm (limit "
        f"{u_limit:.3f}) at ({', '.join(f'{c:.1f}' for c in r['max_u_at'])}), "
        f"{r['load_nodes']} loaded nodes; mesh x{REFINE} changes them "
        f"{100 * r['max_vm_mpa_change']:.0f}% / {100 * r['max_u_mm_change']:.0f}% "
        f"(max {100 * CONVERGED:.0f}%)",
    )


def _under_a_foot(x: float, y: float, z: float) -> bool:
    """On the tub's underside under one of the 4 rubber feet, which grip the table."""
    return z <= 0.05 and _near_corner_screw(x, y, r=FOOT_D / 2.0)


def _on_a_standoff_top(x: float, y: float, z: float) -> bool:
    """On the top face of one of the 4 Radxa or 2 RJ45 standoffs (where the screws clamp)."""
    tops = [(hx, hy, D.RADXA_PCB_Z0) for hx, hy in D.radxa_hole_centres()]
    tops += [(rx, ry, D.RJ45_SEAT_Z) for rx, ry in D.RJ45_MOUNT_HOLES]
    return any(
        abs(z - tz) <= 0.15 and (x - tx) ** 2 + (y - ty) ** 2 <= 3.6**2 for tx, ty, tz in tops
    )


def _near_corner_screw(x: float, y: float, r: float = 2.6) -> bool:
    """Within the M3 corner boss at (x, y): where the screws hold the halves together."""
    return any((x - bx) ** 2 + (y - by) ** 2 <= r * r for bx in CORNER_XS for by in CORNER_YS)


# Flex limits by what each part has to do (owner, C4 2026-11-13: don't reinforce; the old fixed
# limits were set against a C3D4 model 5-15x too stiff):
#   - guide pole: must not reach the button, so the BTN_DATUM gap;
#   - button stop: may let the switch go no further than its guaranteed over-travel. A nominal
#     SS-5GL (OP 8.8) is (OP - tip at stop) past its click point at the stop and is rated for
#     OT_min, so the stop may give (OT_min - that) at the tip, x the lever ratio at the button;
#   - chimneys: must not close the button's sliding clearance;
#   - standoffs: the rear jack must keep the 0.5 mm from the tub wall REAR_IO requires.
POLE_FLEX_MAX = D.BUTTON_POLE_GAP
STOP_FLEX_MAX = (
    omron_ss5gl.OVERTRAVEL_MIN - (omron_ss5gl.OPERATING_POSITION - D.OMRON_TIP_AT_STOP)
) * D.OMRON_LEVER_RATIO
CHIMNEY_FLEX_MAX = D.RESET_CLEAR
STANDOFF_FLEX_MAX = 0.50
# The dome sag is reported, not limited: the hood and fan under the loaded area (foam-taped to
# the shell) hold it up, and this model leaves them out, so its sag is an upper bound.
DOME_SAG_REPORT_ONLY = math.inf


def check_all(out_dir: str | None = None) -> list[tuple[str, bool, str]]:
    """Run all 4 Gmsh + CalculiX 3D FEM load cases (C3D10, mesh-converged) as gate rows."""
    rows: list[tuple[str, bool, str]] = []

    # 1. LC1: usb_retainer_bracket (glued along its base) under a 50 N mash on the button stop,
    #    15 N sideways on the guide pole and a 15 N USB-A pry under the top bridge. The stop
    #    shelf's own give is graded against the switch margin (Gemini review #5): the part's
    #    largest movement is the pole tip, which says nothing about how far the button goes.
    def on_stop_shelf(x: float, y: float, z: float) -> bool:
        return abs(z - STOP_Z) <= 0.15 and -35.0 <= x <= -29.6

    r1 = solve_converged(
        "LC1_BUTTON_MASH_50N",
        usb_retainer_bracket.get_shape(),
        clmin=0.45,
        clmax=1.10,
        fix_pred=lambda x, y, z: z <= 11.75 or (y <= -36.50 and z <= 13.00),
        watch_pred=on_stop_shelf,
        loads=[
            (on_stop_shelf, (0.0, 0.0, -50.0)),
            (lambda x, y, z: z >= 25.00, (0.0, -15.0, 0.0)),
            (
                lambda x, y, z: (
                    abs(z - 16.85) <= 0.15 and (-39.0 <= x <= -26.0 or -24.0 <= x <= -11.0)
                ),
                (0.0, 0.0, 15.0),
            ),
        ],
        out_dir=out_dir,
    )
    label1, ok1, msg1 = _row(
        "FEM_LC1   usb_retainer_bracket 50N button mash + 15N pole tilt + 15N USB pry",
        r1,
        25.0,
        POLE_FLEX_MAX,
    )
    stop1 = float(r1["watch_uz_mm"])
    rows.append(
        (
            label1,
            ok1 and stop1 <= STOP_FLEX_MAX,
            f"{msg1}; stop shelf gives {stop1:.3f} mm (limit {STOP_FLEX_MAX:.3f}, the switch's "
            "over-travel margin)",
        )
    )

    # 2. LC2: the tub's front-left USB-A & Omron bay, cut from the tub (the cut faces held as the
    #    rest of the tub would hold them), resting on its floor
    tub = lower_tub.get_shape()
    tub_fl = tub.intersect(cq.Solid.makeBox(66.0, 36.0, 25.0, cq.Vector(-66.0, -50.0, -0.5)))
    r2 = solve_converged(
        "LC2_TUB_USB_AND_OMRON",
        tub_fl,
        clmin=0.80,
        clmax=2.20,
        fix_pred=lambda x, y, z: y >= -14.2 or x >= -0.2 or _under_a_foot(x, y, z),
        roller_pred=lambda x, y, z: z <= 0.05,
        loads=[
            (
                lambda x, y, z: -40.5 <= x <= -9.5 and -26.80 <= y <= -25.70 and 9.60 <= z <= 11.60,
                (0.0, 40.0, 0.0),
            ),
            (
                lambda x, y, z: -40.5 <= x <= -9.5 and -32.60 <= y <= -32.10 and 5.80 <= z <= 10.85,
                (0.0, -30.0, 0.0),
            ),
            (
                lambda x, y, z: (
                    -35.0 <= x <= -29.5 and -20.90 <= y <= -16.70 and z >= STOP_Z - 0.25
                ),
                (0.0, 0.0, -50.0),
            ),
        ],
        out_dir=out_dir,
    )
    rows.append(
        _row(
            "FEM_LC2   lower_tub USB-A cradle (40N insert, 30N yank) & 50N Omron rear stop",
            r2,
            20.0,
            STOP_FLEX_MAX,
        )
    )

    # 3. LC3: the upper shell resting on the tub's rim (held vertically) and screwed at its four
    #    corners (held fully; C4: holding the whole rim fully over-stiffened it), 100 N on the dome
    sh = upper_shell.get_shape()
    r3 = solve_converged(
        "LC3_UPPER_SHELL_DOME_100N",
        sh,
        clmin=1.10,
        clmax=2.80,
        fix_pred=lambda x, y, z: z <= 13.20 and _near_corner_screw(x, y),
        roller_pred=lambda x, y, z: z <= 13.00,
        loads=[
            (
                lambda x, y, z: -28.0 <= x <= 28.0 and -35.0 <= y <= 10.0 and z >= 31.0,
                (0.0, 0.0, -100.0),
            ),
        ],
        out_dir=out_dir,
    )
    label, ok, msg = _row(
        "FEM_LC3   upper_shell 100N top-dome crush; button chimneys stay round",
        r3,
        25.0,
        DOME_SAG_REPORT_ONLY,
    )
    uc3 = float(r3["max_chimney_xy_u_mm"])
    rows.append(
        (
            label,
            ok and uc3 <= CHIMNEY_FLEX_MAX,
            f"{msg} (dome sag reported only: hood and fan not modelled); chimney XY {uc3:.3f} mm "
            f"(limit {CHIMNEY_FLEX_MAX:.3f}, the button's sliding clearance)",
        )
    )

    # 4. LC4: the tub's rear half on its floor (held vertically), the cut face held, 30 N rear plug
    #    push + 60 N screw preload on the 4 Radxa and 2 RJ45 standoffs
    tub_rear = tub.intersect(cq.Solid.makeBox(132.0, 63.0, 16.0, cq.Vector(-66.0, -12.0, -0.5)))
    r4 = solve_converged(
        "LC4_RADXA_RJ45_STANDOFFS",
        tub_rear,
        clmin=1.00,
        clmax=2.80,
        fix_pred=lambda x, y, z: y <= -11.8 or _under_a_foot(x, y, z),
        roller_pred=lambda x, y, z: z <= 0.05,
        # on the 6 standoff tops only (C4: a box here also caught the rear wall's top edge)
        loads=[(_on_a_standoff_top, (0.0, -30.0, -60.0))],
        out_dir=out_dir,
    )
    rows.append(
        _row(
            "FEM_LC4   lower_tub Radxa X4 & RJ45 standoffs (30N -Y plug push + 60N preload)",
            r4,
            15.0,
            STANDOFF_FLEX_MAX,
        )
    )

    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", help="Optional directory to persist CalculiX .frd/.inp files")
    args = parser.parse_args()

    print("=== 3D TETRAHEDRAL FEM STRUCTURAL ANALYSIS (Gmsh + CalculiX) ===\n")
    rows = check_all(out_dir=args.out_dir)
    failed = 0
    for label, ok, msg in rows:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
        print(f"        {msg}")
        if not ok:
            failed += 1
    print(f"\n{len(rows) - failed}/{len(rows)} FEM load cases passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
