"""Are the exported files actually manufacturable?

`export_harness.py` writes the files into `export/<name>/`. This reads them back
from disk and checks that every part declared its process, wrote its expected
output file(s), round-trips its 3D geometry (volume and bounding box within 0.1%
after re-importing the `.step` from disk), passes `BRepAlgoAPI_Check`, and fits
the Bambu X2D / P1S `256 x 256 x 256 mm` build volume.
"""

import importlib.util
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
import plate  # noqa: E402
from cadquery.occ_impl.shapes import check as bop_check  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXPORT_DIR = os.path.join(REPO, "export")
PART_DIRS = ("part", "variant")
FDM_BED = (256.0, 256.0, 256.0)


def _part_modules():
    out = []
    for d in PART_DIRS:
        p = os.path.join(REPO, "lib", d)
        if not os.path.isdir(p):
            continue
        for f in sorted(os.listdir(p)):
            if f.endswith(".py") and not f.startswith("_"):
                out.append((d, f[:-3]))
    return out


def _load(d, name):
    path = os.path.join(REPO, "lib", d, name + ".py")
    spec = importlib.util.spec_from_file_location(f"{d}_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.join(REPO, "lib", d))
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.pop(0)
    return mod


def check_all():
    """Rows in `(label, passed, message)` shape."""
    out = []
    parts = _part_modules()

    if not parts:
        return [("EXPORT    there are parts to validate", False, "no part modules found at all")]

    undeclared, laser, fdm, aux = [], [], [], []
    for d, name in parts:
        try:
            mod = _load(d, name)
        except Exception as exc:
            undeclared.append(f"{d}/{name} (failed to import: {type(exc).__name__})")
            continue
        proc = getattr(mod, "PROCESS", None)
        mfg = getattr(mod, "MANUFACTURE", None)
        if proc is None or mfg != proc:
            undeclared.append(f"{d}/{name} (PROCESS={proc!r}, MANUFACTURE={mfg!r})")
        elif proc == "laser":
            laser.append((d, name, mod))
        elif proc == "fdm":
            fdm.append((d, name, mod))
        elif proc in ("component", "reference"):
            aux.append((d, name, mod))
        else:
            undeclared.append(
                f"{d}/{name} (PROCESS={proc!r}, not 'laser', 'fdm', 'component', or 'reference')"
            )

    out.append(
        (
            "DECLARED  every part declares matching PROCESS and MANUFACTURE",
            not undeclared and bool(fdm or laser),
            f"{len(fdm)} fdm, {len(laser)} laser, {len(aux)} component/ref, "
            f"{len(undeclared)} undeclared/mismatched"
            + (f": {', '.join(undeclared[:8])}" if undeclared else ""),
        )
    )

    if not os.path.isdir(EXPORT_DIR):
        out.append(
            ("PRESENT   every part has its exported file(s)", False, "export/ does not exist")
        )
        return out

    # When both part/<name>.py and variant/<name>.py exist, export/<name>/<name>.step
    # holds the variant solid (since variant supersedes faithful part for fabrication).
    by_name = {}
    for d, name, mod in fdm:
        by_name[name] = (d, name, mod)
    fdm_exported = list(by_name.values())

    # --- PRESENT (FDM STEP files) -----------------------------------------
    missing = []
    for d, name, mod in fdm_exported:
        step_path = os.path.join(EXPORT_DIR, name, f"{name}.step")
        if not os.path.isfile(step_path) or os.path.getsize(step_path) == 0:
            missing.append(f"{name}.step missing or empty")

    missing_aux = []
    for d, name, mod in aux:
        step_path = os.path.join(EXPORT_DIR, name, f"{name}.step")
        if not os.path.isfile(step_path) or os.path.getsize(step_path) == 0:
            missing_aux.append(f"{name}.step missing or empty")

    out.append(
        (
            "PRESENT   every FDM & component/ref module has a non-empty .step file in export/",
            bool(fdm_exported) and not missing and not missing_aux,
            f"{len(fdm_exported)} FDM + {len(aux)} component/ref export(s); "
            + ("; ".join(missing + missing_aux) if (missing or missing_aux) else "all present"),
        )
    )

    # --- ROUNDTRIP & MANIFOLD & BED ---------------------------------------
    bad_roundtrip = []
    bad_manifold = []
    bad_bed = []

    for d, name, mod in fdm_exported:
        step_path = os.path.join(EXPORT_DIR, name, f"{name}.step")
        if not os.path.isfile(step_path):
            bad_roundtrip.append(f"{name}: missing .step")
            continue
        try:
            native = mod.get_shape()
            imported = cq.importers.importStep(step_path).val()
        except Exception as exc:
            bad_roundtrip.append(f"{name}: importStep failed ({type(exc).__name__}: {exc})")
            continue

        v_nat = native.Volume()
        v_imp = imported.Volume()
        if v_nat <= 0 or abs(v_imp - v_nat) / v_nat > 0.001:
            bad_roundtrip.append(f"{name}: STEP volume {v_imp:.2f} vs native {v_nat:.2f} mm^3")

        bn = native.BoundingBox()
        bi = imported.BoundingBox()
        for axis, s_imp, s_nat in (
            ("x", bi.xlen, bn.xlen),
            ("y", bi.ylen, bn.ylen),
            ("z", bi.zlen, bn.zlen),
        ):
            if abs(s_imp - s_nat) > 0.05:
                bad_roundtrip.append(
                    f"{name} {axis}-span: STEP {s_imp:.2f} vs native {s_nat:.2f} mm"
                )

        ok_m = bool(bop_check(imported))
        if not ok_m or len(imported.Solids()) != 1:
            bad_manifold.append(
                f"{name}: BRepAlgoAPI_Check={ok_m}, solids={len(imported.Solids())}"
            )

        if bi.xlen > FDM_BED[0] or bi.ylen > FDM_BED[1] or bi.zlen > FDM_BED[2]:
            bad_bed.append(f"{name}: {bi.xlen:.1f} x {bi.ylen:.1f} x {bi.zlen:.1f} mm")

    out.append(
        (
            "ROUNDTRIP re-imported STEP matches native solid volume (<0.1%) and spans (<0.05mm)",
            bool(fdm_exported) and not bad_roundtrip,
            "; ".join(bad_roundtrip)
            if bad_roundtrip
            else f"{len(fdm_exported)} STEP file(s) re-imported and verified against get_shape()",
        )
    )
    out.append(
        (
            "MANIFOLD  every re-imported STEP is a single manifold solid (BRepAlgoAPI_Check)",
            bool(fdm_exported) and not bad_manifold,
            "; ".join(bad_manifold)
            if bad_manifold
            else f"{len(fdm_exported)} STEP file(s) pass BRepAlgoAPI_Check with 1 solid each",
        )
    )
    out.append(
        (
            "BED       every exported FDM part fits the 256 x 256 x 256 mm build volume",
            bool(fdm_exported) and not bad_bed,
            "; ".join(bad_bed)
            if bad_bed
            else (
                f"{len(fdm_exported)} FDM part(s) fit inside "
                f"{FDM_BED[0]:.0f}x{FDM_BED[1]:.0f}x{FDM_BED[2]:.0f} mm"
            ),
        )
    )

    # --- PRINT PLATE (11 oriented FDM bodies on Z=0 inside 256 x 256 mm) ---
    expected_bodies = sum(qty for _, _, qty in plate.PLATE_BOM)
    plate_label = (
        f"PLATE     export/plate/print_plate.step packs all {expected_bodies} FDM parts on Z=0"
    )
    if not os.path.isfile(plate.PLATE_STEP):
        out.append(
            (
                plate_label,
                False,
                "export/plate/print_plate.step missing",
            )
        )
    else:
        plate_imp = cq.importers.importStep(plate.PLATE_STEP).val()
        p_solids = plate_imp.Solids()
        p_bb = plate_imp.BoundingBox()
        _, placements = plate.build_plate()
        overlaps = []
        for i, a in enumerate(placements):
            for b in placements[i + 1 :]:
                ox = min(float(a["xmax"]), float(b["xmax"])) - max(
                    float(a["xmin"]), float(b["xmin"])
                )
                oy = min(float(a["ymax"]), float(b["ymax"])) - max(
                    float(a["ymin"]), float(b["ymin"])
                )
                if ox > -1.0 and oy > -1.0:
                    overlaps.append(f"{a['label']}/{b['label']}")
        z_bad = [s for s in p_solids if abs(s.BoundingBox().zmin) > 0.05]
        plate_ok = (
            len(p_solids) == expected_bodies
            and not z_bad
            and not overlaps
            and p_bb.xlen <= FDM_BED[0]
            and p_bb.ylen <= FDM_BED[1]
            and p_bb.zlen <= FDM_BED[2]
        )
        out.append(
            (
                plate_label,
                plate_ok,
                f"{len(p_solids)}/{expected_bodies} solids on Z=0, "
                f"plate {p_bb.xlen:.1f}x{p_bb.ylen:.1f}x{p_bb.zlen:.1f} mm, "
                f"overlaps={len(overlaps)}",
            )
        )

    return out


def main():
    rows = check_all()
    bad = 0
    for label, ok, msg in rows:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
        print(f"        {msg}")
        if not ok:
            bad += 1
    print(f"\n{len(rows) - bad}/{len(rows)} passed, {bad} failed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
