"""Proves `lib/gate.py` can FAIL (`./run selftest`).

For each check module in `lib/assembly/` and `lib/subassembly/`:
  1. Builds a temporary symlink farm (`N64_CAD_LIB_DIR`) mirroring `lib/`.
  2. Replaces one target module with a mutated copy containing a real geometric
     or datum defect.
  3. Runs `lib/gate.py` against that farm and asserts the gate exits non-zero
     and prints `FAIL` on the expected row.
"""

import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GATE = os.path.join(HERE, "gate.py")

# (check_filter, target_relpath, old_snippet, new_snippet, expected_failed_row_prefix)
MUTATIONS = [
    # C8: every row that measures the solids has a planted defect it must catch
    (
        "console_check",
        "assembly/datum.py",
        "CORNER_SCREW_L = 14.0",
        "CORNER_SCREW_L = 12.0",
        "J01_SCREW",
    ),
    (
        "datum_check",
        "assembly/datum.py",
        "RADXA_X_CENTRE = -5.5",
        "RADXA_X_CENTRE = -6.5",
        "RADXA_FIT",
    ),
    (
        "radxa_mount_check",
        "assembly/datum.py",
        "RADXA_STANDOFF_H = 6.6",
        "RADXA_STANDOFF_H = 6.0",
        "M2_CLEAR",
    ),
    (
        "console_check",
        "assembly/datum.py",
        "RADXA_STANDOFF_H = 6.6",
        "RADXA_STANDOFF_H = 9.6",
        "G13_FULL",
    ),
    (
        "top_controls_check",
        "assembly/datum.py",
        "RESET_FLANGE_W = 11.0",
        "RESET_FLANGE_W = 14.0",
        "G13_TOP",
    ),
    (
        "top_controls_check",
        "part/reset_button.py",
        "        D.RESET_SHAFT_W,\n",
        "        D.RESET_SHAFT_W + 0.6,\n",
        "J04_RESET",
    ),
    (
        "top_controls_check",
        "part/front_bezel.py",
        "y0=D.BEZEL_Y0,",
        "y0=D.BEZEL_Y0 + 1.5,",
        "J06_BEZEL",
    ),
    (
        "front_panel_check",
        "part/led_light_pipe.py",
        "width_x=D.LED_FLANGE_W,",
        "width_x=D.LED_FLANGE_W + 0.6,",
        "J07_PIPE",
    ),
    (
        "front_panel_check",
        "part/front_port_cover.py",
        "t = D.FRONT_COVER_T - 0.2",
        "t = D.FRONT_COVER_T + 0.6",
        "G13_FRONT",
    ),
    (
        "datum_check",
        "component/radxa_x4.py",
        "cq.Solid.makeBox(10.40, 20.80, 10.40, cq.Vector(38.00, 27.50, 2.00))",
        "cq.Solid.makeBox(10.40, 20.80, 10.40, cq.Vector(36.50, 27.50, 2.00))",
        "REAR_IO",
    ),
    (
        "datum_check",
        "assembly/datum.py",
        "SCALE = 0.50",
        "SCALE = 0.65",
        "SCALE",
    ),
    (
        "datum_check",
        "subassembly/front_panel_mech.py",
        "    return cq.Compound.makeCompound(covers())\n",
        '    return cq.Compound.makeCompound(covers()).mirror("XZ")\n',
        "HANDED",
    ),
    (
        "radxa_mount_check",
        "assembly/datum.py",
        "RADXA_STANDOFF_H = 6.6",
        "RADXA_STANDOFF_H = 2.0",
        "G13_CLEAR",
    ),
    (
        "radxa_mount_check",
        "variant/lower_tub.py",
        "bore_dia=D.INSERT_M25_BORE_D,",
        "bore_dia=0.01,",
        "J02_SEAT",
    ),
    (
        "radxa_mount_check",
        "variant/lower_tub.py",
        '"volume_mm3": 281.25,',
        '"volume_mm3": 999.00,',
        "VARIANT   lower_tub.rear_rj45_cutout",
    ),
    (
        "top_controls_check",
        "variant/upper_shell.py",
        '"volume_mm3": 52.45,',
        '"volume_mm3": 999.00,',
        "VARIANT   upper_shell.rear_dome_exhaust_l",
    ),
    (
        "top_controls_check",
        "part/upper_shell.py",
        "T.memory_expansion_prisms(z0=25.0, height=10.0)",
        "T.memory_expansion_prisms(z0=35.0, height=1.0)",
        "DOME_TOP",
    ),
    (
        "top_controls_check",
        "assembly/datum.py",
        "CARTRIDGE_FLAP_CLEAR = 0.15",
        "CARTRIDGE_FLAP_CLEAR = 0.01",
        "J09_FLAPS",
    ),
    (
        "top_controls_check",
        "part/upper_shell.py",
        "22.10,",
        "27.20,",
        "J03_SLIDE",
    ),
    (
        "top_controls_check",
        "assembly/datum.py",
        "OMRON_SCREW_L = 10.0",
        "OMRON_SCREW_L = 12.0",
        "OMRON_SCREW",
    ),
    (
        "top_controls_check",
        "assembly/datum.py",
        "BUTTON_UNDERSIDE_Z = RESET_Z0 - 0.33",
        "BUTTON_UNDERSIDE_Z = RESET_Z0 - 0.60",
        "OMRON_ACT",
    ),
    (
        "top_controls_check",
        "assembly/datum.py",
        "RESET_STROKE_Z = 2.10",
        "RESET_STROKE_Z = 1.90",
        "OMRON_ACT",
    ),
    (
        "front_panel_check",
        "assembly/datum.py",
        "FRONT_COVER_CLEAR = 0.20",
        "FRONT_COVER_CLEAR = 0.01",
        "J05_COVER",
    ),
    (
        "front_panel_check",
        "assembly/datum.py",
        "FRONT_BAY_DROP = 2.5",
        "FRONT_BAY_DROP = 0.0",
        "J05_COVER",
    ),
    (
        "front_panel_check",
        "assembly/datum.py",
        "PORT_INSERT_BOSS_D = 7.8",
        "PORT_INSERT_BOSS_D = 8.18",
        "J08_PORT",
    ),
    (
        "radxa_mount_check",
        "assembly/datum.py",
        "RADXA_STANDOFF_TOP_D, RADXA_STANDOFF_TOP_H = 6.4, 1.0",
        "RADXA_STANDOFF_TOP_D, RADXA_STANDOFF_TOP_H = 7.0, 1.0",
        "G13_CLEAR",
    ),
    (
        "radxa_mount_check",
        "step/build_radxa_x4.py",
        "SOLIDS = 363",
        "SOLIDS = 357",
        "RADXA_REF",
    ),
    (
        "radxa_mount_check",
        "variant/radxa_x4.py",
        '"volume_mm3": 2445.58,',
        '"volume_mm3": 9999.00,',
        "VARIANT   radxa_x4.usb3_dual_stack",
    ),
    (
        "console_check",
        "assembly/datum.py",
        "WAIST_HALF_W = 60.00",
        "WAIST_HALF_W = 64.50",
        "SH_OUTSIDE",
    ),
    (
        "console_check",
        "assembly/datum.py",
        "RABBET_INSET = 1.00",
        "RABBET_INSET = 1.80",
        "J01_SPLIT",
    ),
    (
        "radxa_mount_check",
        "part/usb_retainer_bracket.py",
        "BRIDGE_Z0 = 16.85",
        "BRIDGE_Z0 = 18.00",
        "USB_LOCK",
    ),
    (
        "radxa_mount_check",
        "variant/lower_tub.py",
        "12.80, 6.80, 48.40, 3.60",
        "9.60, 3.70, 48.40, 3.60",
        "REAR_PLUGS",
    ),
    (
        "top_controls_check",
        "part/shared/n64_text.py",
        "PLAQUE_FONT_SIZE = 2.6",
        "PLAQUE_FONT_SIZE = 4.0",
        "PLAQUE",
    ),
    # Cooling (REQ-04): a vent that stops being a vent, a fan that drops into the retainer
    # bridge, a weaker fan, and a cover that no longer clamps the heat sink.
    (
        "cooling_check",
        "variant/upper_shell.py",
        "for x0, y0, x1, y1 in C.TOP_LOUVER_BOXES_50:",
        "for x0, y0, x1, y1 in C.TOP_LOUVER_BOXES_50[:3]:",
        "COOL_VENT",
    ),
    (
        "cooling_check",
        "assembly/datum.py",
        "FAN_Z0 = 18.6",
        "FAN_Z0 = 16.0",
        "G13_COOL",
    ),
    (
        "cooling_check",
        "component/sunon_mf30060v2.py",
        "P_MAX_PA = 0.110 * INH2O_PA",
        "P_MAX_PA = 0.030 * INH2O_PA",
        "THERMAL",
    ),
    (
        "cooling_check",
        "part/cooling_duct.py",
        "Z_COVER0 = D.HS_Z1  # cover rests on the pin tips",
        "Z_COVER0 = D.HS_Z1 + 0.5  # cover rests on the pin tips",
        "COOL_SEAT",
    ),
    (
        "cooling_check",
        "part/cooling_duct.py",
        # No pocket floor: the plenum opens down into the case under the fan's front strip.
        "        _box(-X_POCKET, X_POCKET, Y_POCKET_OUT, Y_FRONT_OUT, Z_HIGH, Z_HIGH + W),"
        "  # floor\n",
        "",
        "COOL_SEAL",
    ),
    (
        "cooling_check",
        "part/cooling_duct.py",
        "X_POCKET = 9.0",
        "X_POCKET = 4.0",
        "COOL_FAN",
    ),
    (
        "cooling_check",
        "assembly/datum.py",
        "DUCT_COVER_T = 2.1",
        "DUCT_COVER_T = 1.6",
        "CLAMP",
    ),
]


def _make_farm(root: str) -> str:
    """Create a symlink farm of `lib/` inside `root/lib`."""
    farm = os.path.join(root, "lib")
    for dirpath, dirnames, filenames in os.walk(HERE):
        rel = os.path.relpath(dirpath, HERE)
        if "__pycache__" in rel:
            continue
        dest_dir = farm if rel == "." else os.path.join(farm, rel)
        os.makedirs(dest_dir, exist_ok=True)
        for fn in filenames:
            if fn.endswith(".pyc"):
                continue
            src = os.path.join(dirpath, fn)
            dst = os.path.join(dest_dir, fn)
            os.symlink(src, dst)
    # Symlink notes/ beside lib/ so datum_check can find notes/TOLERANCES.md
    repo_notes = os.path.join(os.path.dirname(HERE), "notes")
    if os.path.isdir(repo_notes):
        os.symlink(repo_notes, os.path.join(root, "notes"))
    return farm


def main(argv: list[str]) -> int:
    """Run every mutation, or with `--only ROW [ROW...]` those expected to fail rows ROW*."""
    only = argv[argv.index("--only") + 1 :] if "--only" in argv else []
    chosen = [m for m in MUTATIONS if not only or any(m[4].startswith(r) for r in only)]
    if not chosen:
        print(f"no mutation expects a failure on {only}")
        return 2
    print(f"=== GATE MUTATION SELF-TEST (REQ-12): {len(chosen)}/{len(MUTATIONS)} ===\n")
    failed = 0
    for check_filter, target_rel, old_s, new_s, expected_row in chosen:
        with tempfile.TemporaryDirectory(prefix="n64_selftest_") as tmp:
            farm = _make_farm(tmp)
            target_path = os.path.join(farm, target_rel)
            real_src = open(os.path.join(HERE, target_rel), encoding="utf-8").read()
            if old_s not in real_src:
                print(f"  FAIL  [{check_filter}] snippet {old_s!r} not found in {target_rel}")
                failed += 1
                continue
            os.unlink(target_path)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(real_src.replace(old_s, new_s, 1))

            env = os.environ.copy()
            env["N64_CAD_LIB_DIR"] = farm
            proc = subprocess.run(
                [sys.executable, GATE, check_filter],
                cwd=HERE,
                env=env,
                capture_output=True,
                text=True,
                timeout=600,
            )
            caught = proc.returncode != 0 and f"FAIL  {expected_row}" in proc.stdout
            tag = "PASS" if caught else "FAIL"
            print(
                f"  {tag}  {check_filter:20s} mutate {target_rel} ({old_s} -> {new_s}) "
                f"=> caught by {expected_row}"
            )
            if not caught:
                failed += 1
                print(f"        gate exit={proc.returncode}")
                for ln in proc.stdout.splitlines()[-10:]:
                    print(f"        {ln}")

    print(f"\n{len(chosen) - failed}/{len(chosen)} mutations caught by gate.py")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
