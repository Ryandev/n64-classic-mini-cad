"""3D Tetrahedral Finite Element Analysis (`Gmsh` + `CalculiX ccx`) for the N64 Classic Mini.

Runs 4 linear-elastic 3D tetrahedral (`C3D4`) FEA load cases (`E = 2200 MPa`, `nu = 0.36`,
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
from assembly.datum import BUTTON_STOP_Z as STOP_Z  # noqa: E402
from part import usb_retainer_bracket  # noqa: E402
from variant import lower_tub, upper_shell  # noqa: E402

PETG_E_MPA = 2200.0
PETG_NU = 0.36


def _find_binary(name: str) -> str:
    """Locate `gmsh` or `ccx` on `PATH` or inside a running FreeCAD AppImage mount."""
    found = shutil.which(name)
    if found:
        return found
    matches = sorted(glob.glob(f"/tmp/.mount_freeca*/usr/bin/{name}"))
    if matches:
        return matches[-1]
    raise RuntimeError(f"Required FEM binary {name!r} not found on PATH or in /tmp/.mount_freeca*")


def solve_calculix(
    name: str,
    shape: cq.Shape,
    clmin: float,
    clmax: float,
    fix_pred: Callable[[float, float, float], bool],
    loads: list[tuple[Callable[[float, float, float], bool], tuple[float, float, float]]],
    out_dir: str | None = None,
) -> dict[str, object]:
    """Mesh `shape` with Gmsh, solve linear static FEA with CalculiX, and return peak metrics."""
    gmsh_bin = _find_binary("gmsh")
    ccx_bin = _find_binary("ccx")

    with tempfile.TemporaryDirectory(prefix=f"n64_fem_{name}_") as tmp:
        work_dir = os.path.join(out_dir, name) if out_dir else tmp
        os.makedirs(work_dir, exist_ok=True)

        step_f = os.path.join(work_dir, "part.step")
        inp_mesh = os.path.join(work_dir, "mesh.inp")
        cq.exporters.export(shape, step_f)

        cmd_gmsh = [
            gmsh_bin,
            step_f,
            "-3",
            "-clmin",
            str(clmin),
            "-clmax",
            str(clmax),
            "-optimize_netgen",
            "-format",
            "inp",
            "-o",
            inp_mesh,
            "-v",
            "1",
        ]
        subprocess.run(cmd_gmsh, check=True, capture_output=True, text=True)

        nodes: dict[int, tuple[float, float, float]] = {}
        elems: list[list[int]] = []
        mode: str | None = None
        with open(inp_mesh, encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if not s or s.startswith("**"):
                    continue
                if s.upper().startswith("*NODE"):
                    mode = "node"
                    continue
                if s.upper().startswith("*ELEMENT"):
                    mode = "c3d4" if "C3D4" in s.upper() else None
                    continue
                if s.startswith("*"):
                    mode = None
                    continue
                if mode == "node":
                    parts = [p.strip() for p in s.split(",")]
                    nodes[int(parts[0])] = (float(parts[1]), float(parts[2]), float(parts[3]))
                elif mode == "c3d4":
                    elems.append([int(p.strip()) for p in s.split(",") if p.strip()])

        fix_nodes = [nid for nid, xyz in nodes.items() if fix_pred(*xyz)]
        if not fix_nodes:
            raise RuntimeError(f"{name}: fix_pred matched 0 nodes")

        job_inp = os.path.join(work_dir, "job.inp")
        with open(job_inp, "w", encoding="utf-8") as out:
            out.write(f"*HEADING\n{name}\n*NODE, NSET=Nall\n")
            for nid, (x, y, z) in sorted(nodes.items()):
                out.write(f"{nid}, {x:.6f}, {y:.6f}, {z:.6f}\n")
            out.write("*ELEMENT, TYPE=C3D4, ELSET=Eall\n")
            for idx, el in enumerate(elems, 1):
                out.write(f"{idx}, {el[1]}, {el[2]}, {el[3]}, {el[4]}\n")
            out.write("*NSET, NSET=Nfix\n")
            for i in range(0, len(fix_nodes), 10):
                out.write(", ".join(str(n) for n in fix_nodes[i : i + 10]) + "\n")
            out.write(f"*MATERIAL, NAME=PETG\n*ELASTIC\n{PETG_E_MPA:.1f}, {PETG_NU:.3f}\n")
            out.write("*SOLID SECTION, ELSET=Eall, MATERIAL=PETG\n")
            out.write("*STEP\n*STATIC\n*BOUNDARY\nNfix, 1, 3, 0.0\n*CLOAD\n")
            fix_set = set(fix_nodes)
            for load_pred, (fx, fy, fz) in loads:
                lnodes = [
                    nid for nid, xyz in nodes.items() if load_pred(*xyz) and nid not in fix_set
                ]
                if not lnodes:
                    raise RuntimeError(f"{name}: load predicate matched 0 free nodes")
                n_l = len(lnodes)
                for nid in lnodes:
                    if abs(fx) > 1e-9:
                        out.write(f"{nid}, 1, {fx / n_l:.6f}\n")
                    if abs(fy) > 1e-9:
                        out.write(f"{nid}, 2, {fy / n_l:.6f}\n")
                    if abs(fz) > 1e-9:
                        out.write(f"{nid}, 3, {fz / n_l:.6f}\n")
            out.write("*NODE FILE\nU\n*EL FILE\nS\n")
            out.write("*NODE PRINT, NSET=Nall\nU\n*EL PRINT, ELSET=Eall\nS\n*END STEP\n")

        subprocess.run([ccx_bin, "job"], cwd=work_dir, check=True, capture_output=True, text=True)

        max_u = 0.0
        max_u_at = (0.0, 0.0, 0.0)
        max_chimney_xy_u = 0.0
        max_vm = 0.0
        max_vm_at = (0.0, 0.0, 0.0)
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
                    nid = int(p[0])
                    ux, uy, uz = float(p[1]), float(p[2]), float(p[3])
                    umag = math.sqrt(ux * ux + uy * uy + uz * uz)
                    nx, ny, nz = nodes[nid]
                    if umag > max_u:
                        max_u = umag
                        max_u_at = (nx, ny, nz)
                    if abs(abs(nx) - 32.32) <= 7.0 and -39.0 <= ny <= -19.0 and 23.5 <= nz <= 30.0:
                        max_chimney_xy_u = max(max_chimney_xy_u, math.sqrt(ux * ux + uy * uy))
                elif sec == "s" and len(p) == 8 and p[0].isdigit():
                    eid = int(p[0])
                    sxx, syy, szz = float(p[2]), float(p[3]), float(p[4])
                    sxy, sxz, syz = float(p[5]), float(p[6]), float(p[7])
                    vm = math.sqrt(
                        0.5
                        * (
                            (sxx - syy) ** 2
                            + (syy - szz) ** 2
                            + (szz - sxx) ** 2
                            + 6.0 * (sxy**2 + sxz**2 + syz**2)
                        )
                    )
                    if vm > max_vm:
                        max_vm = vm
                        el_ns = elems[eid - 1][1:5]
                        max_vm_at = (
                            sum(nodes[n][0] for n in el_ns) / 4.0,
                            sum(nodes[n][1] for n in el_ns) / 4.0,
                            sum(nodes[n][2] for n in el_ns) / 4.0,
                        )

        return {
            "name": name,
            "nodes": len(nodes),
            "elems": len(elems),
            "max_u_mm": max_u,
            "max_u_at": max_u_at,
            "max_chimney_xy_u_mm": max_chimney_xy_u,
            "max_vm_mpa": max_vm,
            "max_vm_at": max_vm_at,
            "frd_path": os.path.join(work_dir, "job.frd") if out_dir else None,
        }


def check_all(out_dir: str | None = None) -> list[tuple[str, bool, str]]:
    """Run all 4 Gmsh + CalculiX 3D FEM load cases and return `(label, ok, msg)` rows."""
    rows: list[tuple[str, bool, str]] = []

    # 1. LC1: usb_retainer_bracket under 50N downward mash + 15N pole tilt + 15N USB-A upward pry
    r1 = solve_calculix(
        "LC1_BUTTON_MASH_50N",
        usb_retainer_bracket.get_shape(),
        clmin=0.45,
        clmax=1.10,
        fix_pred=lambda x, y, z: z <= 11.75 or (y <= -36.50 and z <= 13.00),
        loads=[
            (lambda x, y, z: abs(z - STOP_Z) <= 0.15 and -35.0 <= x <= -29.6, (0.0, 0.0, -50.0)),
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
    vm1 = float(r1["max_vm_mpa"])
    u1 = float(r1["max_u_mm"])
    rows.append(
        (
            "FEM_LC1   usb_retainer_bracket 50N button mash + 15N pole tilt + 15N USB pry",
            vm1 <= 25.0 and u1 <= 0.25,
            f"{r1['elems']} C3D4 elems: max von Mises={vm1:.2f} MPa (limit 25.0), "
            f"max disp={u1:.3f} mm (limit 0.250)",
        )
    )

    # 2. LC2: Lower_Tub front-left USB-A & Omron bay (40N +Y insert, 30N -Y yank, 50N -Z stop mash)
    tub = lower_tub.get_shape()
    tub_fl = tub.intersect(cq.Solid.makeBox(66.0, 36.0, 25.0, cq.Vector(-66.0, -50.0, -0.5)))
    r2 = solve_calculix(
        "LC2_TUB_USB_AND_OMRON",
        tub_fl,
        clmin=0.80,
        clmax=2.20,
        fix_pred=lambda x, y, z: z <= 1.65 or y >= -14.2 or x >= -0.2,
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
                lambda x, y, z: -35.0 <= x <= -29.5 and -20.90 <= y <= -16.70 and z >= 23.20,
                (0.0, 0.0, -50.0),
            ),
        ],
        out_dir=out_dir,
    )
    vm2 = float(r2["max_vm_mpa"])
    u2 = float(r2["max_u_mm"])
    rows.append(
        (
            "FEM_LC2   lower_tub USB-A cradle (40N insert, 30N yank) & 50N Omron rear stop",
            vm2 <= 20.0 and u2 <= 0.10,
            f"{r2['elems']} C3D4 elems: max von Mises={vm2:.2f} MPa (limit 20.0), "
            f"max disp={u2:.3f} mm (limit 0.100)",
        )
    )

    # 3. LC3: Full Upper_Shell under 100N (~10 kgf) downward top-dome & louver crush load
    sh = upper_shell.get_shape()
    r3 = solve_calculix(
        "LC3_UPPER_SHELL_DOME_100N",
        sh,
        clmin=1.10,
        clmax=2.80,
        fix_pred=lambda x, y, z: z <= 13.20,
        loads=[
            (
                lambda x, y, z: -28.0 <= x <= 28.0 and -35.0 <= y <= 10.0 and z >= 31.0,
                (0.0, 0.0, -100.0),
            ),
        ],
        out_dir=out_dir,
    )
    vm3 = float(r3["max_vm_mpa"])
    u3 = float(r3["max_u_mm"])
    uc3 = float(r3["max_chimney_xy_u_mm"])
    rows.append(
        (
            "FEM_LC3   upper_shell 100N top-dome crush across 25 louvers & button chimneys",
            vm3 <= 25.0 and u3 <= 0.50 and uc3 <= 0.08,
            f"{r3['elems']} C3D4 elems: max von Mises={vm3:.2f} MPa, "
            f"dome sag={u3:.3f} mm, chimney XY={uc3:.3f} mm (clear 0.22 mm)",
        )
    )

    # 4. LC4: Lower_Tub rear half (4x Radxa + 2x RJ45 standoffs under 30N -Y push + 60N -Z preload)
    tub_rear = tub.intersect(cq.Solid.makeBox(132.0, 63.0, 16.0, cq.Vector(-66.0, -12.0, -0.5)))
    r4 = solve_calculix(
        "LC4_RADXA_RJ45_STANDOFFS",
        tub_rear,
        clmin=1.00,
        clmax=2.80,
        fix_pred=lambda x, y, z: z <= 0.95 or y <= -11.8,
        loads=[
            (
                lambda x, y, z: (
                    (z >= 7.8 and (-49.0 <= x <= 18.0) and (-10.0 <= y <= 48.0))
                    or (z >= 5.2 and 38.0 <= x <= 55.0 and 20.0 <= y <= 33.0)
                ),
                (0.0, -30.0, -60.0),
            ),
        ],
        out_dir=out_dir,
    )
    vm4 = float(r4["max_vm_mpa"])
    u4 = float(r4["max_u_mm"])
    rows.append(
        (
            "FEM_LC4   lower_tub Radxa X4 & RJ45 standoffs (30N -Y plug push + 60N preload)",
            vm4 <= 15.0 and u4 <= 0.10,
            f"{r4['elems']} C3D4 elems: max von Mises={vm4:.2f} MPa (limit 15.0), "
            f"max disp={u4:.3f} mm (limit 0.100)",
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
