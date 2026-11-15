"""Slice FDM parts with Bambu Studio's command line, applying the parts' manufacturing profile.

The CAD is nominal (fits drawn as the finished gap); this is where a profile's measured
allowances go in: Bambu's `xy_hole_compensation` opens every hole by the profile's hole shrink
and `xy_contour_compensation` pulls every outside face in by its contour growth, layer by layer.
Every plate is one profile. `check_sliced` reads the sliced file's own settings and refuses one
that doesn't carry its profile, or breaks the support rules learned on the coupons
(notes/PRINTING.md): PETG body, PLA interface on the right nozzle, prime tower, a brim.

Adapted from the owner's GBA project (`GBA/CAD/lib/slicing/slicer_queue.py`). Machine-specific
paths come from the environment, with this workstation's as defaults; missing ones fail loud.
"""

import json
import os
import re
import subprocess
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from process.profiles import PROFILES, Profile  # noqa: E402

BAMBU_EXE = os.environ.get("N64_BAMBU_EXE", "/mnt/c/Program Files/Bambu Studio/bambu-studio.exe")
PROFILE_DIRS = tuple(
    os.environ.get(
        "N64_BAMBU_PROFILE_DIRS",
        "/mnt/c/Users/ryan/AppData/Roaming/BambuStudio/system/BBL:"
        "/mnt/c/Program Files/Bambu Studio/resources/profiles/BBL",
    ).split(":")
)
# Slicer jobs run here: Bambu Studio is a Windows program and reads Windows paths.
WORK_DIR = os.environ.get("N64_SLICE_DIR", "/mnt/c/Users/ryan/Documents/n64_coupons/slicing")

BRIM_MM = 8.0  # GBA's printer check refuses under 7 mm on a plate spanning ~100 mm
SUPPORT_HIDDEN, SUPPORT_VISIBLE = "hidden", "visible"

# What each Bambu key must read in the sliced file, per profile family and support kind
FDM_SETTINGS = {
    "machine": "Bambu Lab X2D 0.4 nozzle",
    "process": "0.20mm Standard @BBL X2D",
    "body": "Bambu PETG Basic @BBL X2D 0.4 nozzle",
    "interface": "Bambu PLA Basic @BBL X2D 0.4 nozzle",
}


# The X2D settings proven on the owner's prints, from the GBA project's build_slicing_profiles
# (PETG first layer 255 C then 250, textured bed 85 then 80, fans low for PETG, Normal Lift z-hop).
# Bambu's raw system filaments fail its own command line (nil z-hop entries).
PROCESS_PROVEN = {
    "initial_layer_line_width": "0.55",
    "detect_thin_wall": "1",
    "small_perimeter_threshold": ["6.5"] * 6,
    "initial_layer_speed": ["20"] * 6,
    "initial_layer_infill_speed": ["45"] * 6,
    "reduce_infill_retraction_mode": "Disabled",
    "reduce_crossing_wall": "1",
    "avoid_crossing_wall_includes_support": "1",
    "travel_speed": ["500"] * 6,
    "travel_acceleration": ["8000"] * 6,
    "outer_wall_speed": ["70"] * 6,
    "top_surface_speed": ["80"] * 6,
    "outer_wall_jerk": "9",
    "inner_wall_jerk": "9",
    "seam_placement_away_from_overhangs": "1",
}
MACHINE_PROVEN = {"z_hop": ["0.4"] * 6, "z_hop_types": ["Normal Lift"] * 6}
_FILAMENT_COMMON = {
    "textured_plate_temp": ["80"],
    "textured_plate_temp_initial_layer": ["85"],
    "additional_cooling_fan_speed": ["0"],
    "first_x_layer_fan_speed": ["0"],
    "close_fan_the_first_x_layers": ["4"],
    "filament_z_hop_types": ["Normal Lift"] * 6,
    "filament_z_hop": ["0.4"] * 6,
    "filament_retraction_length": ["0.8"] * 6,
}
FILAMENT_PROVEN = {
    "body": {
        **_FILAMENT_COMMON,
        "nozzle_temperature_initial_layer": ["255"],
        "nozzle_temperature": ["250"],
        "fan_max_speed": ["30"],
        "fan_min_speed": ["10"],
        "overhang_fan_speed": ["80"],
        "filament_max_volumetric_speed": ["13"],
        "default_filament_colour": ["#000000"],
        "filament_colour": ["#000000"],
    },
    "interface": {
        **_FILAMENT_COMMON,
        "default_filament_colour": ["#F72323"],
        "filament_colour": ["#F72323"],
    },
}


class SliceError(RuntimeError):
    """A slice that must not reach the printer."""


def _flat(name: str, sub: str) -> dict:
    for base in PROFILE_DIRS:
        path = os.path.join(base, sub, f"{name}.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            merged: dict = {}
            for parent in [data.get("inherits")] + list(data.get("include", [])):
                if parent:
                    merged.update(_flat(parent, sub))
            merged.update(data)
            merged.pop("inherits", None)
            merged.pop("include", None)
            return merged
    raise FileNotFoundError(f"Bambu profile {sub}/{name}.json not under {PROFILE_DIRS}")


def compensation(profile: Profile) -> dict[str, str]:
    """Bambu's compensation settings for `profile`: holes opened, outside faces pulled in."""
    if not profile.proven:
        raise SliceError(f"profile {profile.key} has no measured print behind it")
    return {
        "xy_hole_compensation": f"{profile.hole_shrink:.2f}",
        "xy_contour_compensation": f"{-profile.contour_growth:.2f}",
    }


def process_settings(profile: Profile, support: str | None) -> dict[str, object]:
    """The process overrides for a plate of `profile` parts; `support` None, hidden or visible."""
    p: dict[str, object] = {
        "wall_loops": "4",
        "sparse_infill_density": "30%",
        "sparse_infill_pattern": "gyroid",
        "top_shell_layers": "5",
        "bottom_shell_layers": "4",
        "curr_bed_type": "Textured PEI Plate",
        "brim_type": "outer_only",
        "brim_width": f"{BRIM_MM:g}",
        "brim_object_gap": "0.0",
        "initial_layer_print_height": "0.24",
        "elefant_foot_compensation": "0.2",
        "enable_prime_tower": "0",
        **compensation(profile),
    }
    if support is not None:
        if support not in (SUPPORT_HIDDEN, SUPPORT_VISIBLE):
            raise SliceError(f"support must be None, {SUPPORT_HIDDEN!r} or {SUPPORT_VISIBLE!r}")
        p.update(
            {
                "enable_support": "1",
                # Tree tips each get their own PLA patch: fine for hidden faces only. A face
                # with a finish gets normal supports under one continuous PLA interface
                # (owner, 2026-11-15; coupon plate 3).
                "support_type": "tree(auto)" if support == SUPPORT_HIDDEN else "normal(auto)",
                "support_on_build_plate_only": "1",
                "bridge_no_support": "1",
                "support_object_xy_distance": "0.4",
                "support_filament": "0",
                "support_interface_filament": "2",
                "support_top_z_distance": "0",
                "support_bottom_z_distance": "0",
                "support_interface_top_layers": "3",
                "support_interface_bottom_layers": "0",
                "support_interface_spacing": "0",
                "support_interface_pattern": "rectilinear",
                "enable_prime_tower": "1",
                "wipe_tower_x": ["200"],
                "wipe_tower_y": ["210"],
            }
        )
    return p


def expected(profile: Profile, support: str | None) -> dict[str, str]:
    """What the sliced file's own header must say for this plate."""
    want = {**compensation(profile), "brim_type": "outer_only"}
    if support is None:
        want["enable_support"] = "0"
    else:
        want.update(
            {
                "enable_support": "1",
                "support_type": "tree(auto)" if support == SUPPORT_HIDDEN else "normal(auto)",
                "support_interface_filament": "2",
                "filament_type": "PETG;PLA",
                "filament_map": "1,2",
                "enable_prime_tower": "1",
            }
        )
    return want


def header_settings(text: str) -> dict[str, str]:
    """The `; key = value` settings block of a G-code file."""
    return dict(re.findall(r"^; ([a-z0-9_]+) = (.*)$", text, re.MULTILINE))


def check_sliced(settings: dict[str, str], profile: Profile, support: str | None) -> list[str]:
    """Every way the sliced settings differ from what this plate needs (empty: send it)."""
    problems = []
    for key, want in expected(profile, support).items():
        got = settings.get(key)
        if key.startswith("xy_") and got is not None:
            ok = abs(float(got) - float(want)) < 0.005
        else:
            ok = got == want
        if not ok:
            problems.append(f"{key} = {got!r}, want {want!r}")
    brim = settings.get("brim_width")
    if brim is None or float(brim) < BRIM_MM - 1e-6:
        problems.append(f"brim_width = {brim!r}, want >= {BRIM_MM:g}")
    return problems


def _win(path: str) -> str:
    path = os.path.abspath(path)
    if not path.startswith("/mnt/c/"):
        raise SliceError(f"{path}: Bambu Studio only sees the Windows drive (/mnt/c)")
    return "C:\\" + path[len("/mnt/c/") :].replace("/", "\\")


def slice_plate(name: str, stls: list[str], profile_key: str, support: str | None) -> str:
    """Slice `stls` (all of `profile_key`) to `<WORK_DIR>/<name>.gcode.3mf`; check it; return it."""
    profile = PROFILES[profile_key]
    if profile.family != "fdm":
        raise SliceError(f"{profile_key} is a {profile.family} profile; this slices fdm")
    if not os.path.exists(BAMBU_EXE):
        raise SliceError(f"Bambu Studio not found at {BAMBU_EXE} (set N64_BAMBU_EXE)")
    os.makedirs(WORK_DIR, exist_ok=True)
    m = _flat(FDM_SETTINGS["machine"], "machine")
    m.update(MACHINE_PROVEN)
    p = _flat(FDM_SETTINGS["process"], "process")
    p.update(PROCESS_PROVEN)
    p.update(process_settings(profile, support))
    p["from"] = "system"
    roles = ["body"] + (["interface"] if support is not None else [])
    fils = []
    for role in roles:
        f = _flat(FDM_SETTINGS[role], "filament")
        f.update(FILAMENT_PROVEN[role])
        fils.append(f)
    paths = {}
    for key, obj in (("machine", m), ("process", p)):
        paths[key] = os.path.join(WORK_DIR, f"{name}_{key}.json")
        with open(paths[key], "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2)
    fil_paths = []
    for i, f in enumerate(fils):
        f["from"] = "system"
        fp = os.path.join(WORK_DIR, f"{name}_filament{i}.json")
        with open(fp, "w", encoding="utf-8") as fh:
            json.dump(f, fh, indent=2)
        fil_paths.append(fp)
    out = os.path.join(WORK_DIR, f"{name}.gcode.3mf")
    if os.path.exists(out):
        os.remove(out)
    res = subprocess.run(
        [
            BAMBU_EXE,
            "--arrange",
            "1",
            "--orient",
            "0",
            "--load-settings",
            f"{_win(paths['machine'])};{_win(paths['process'])}",
            "--load-filaments",
            ";".join(_win(f) for f in fil_paths),
            "--slice",
            "0",
            "--export-3mf",
            _win(out),
            *[_win(s) for s in stls],
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=WORK_DIR,  # a Windows program can't start in a Linux folder
    )
    if res.returncode != 0 or not os.path.exists(out):
        raise SliceError(f"Bambu Studio failed (rc={res.returncode}): {res.stderr or res.stdout}")
    with zipfile.ZipFile(out) as zf:
        gcodes = [n for n in zf.namelist() if re.fullmatch(r"Metadata/plate_\d+\.gcode", n)]
        if not gcodes:
            raise SliceError(f"{out}: no sliced plate inside")
        for g in gcodes:
            problems = check_sliced(header_settings(zf.read(g).decode()), profile, support)
            if problems:
                raise SliceError(f"{out} {g}: " + "; ".join(problems))
    return out


def main(argv: list[str]) -> int:
    """`./run slice NAME PROFILE [--support hidden|visible] STL...`"""
    if len(argv) < 3:
        print(main.__doc__)
        return 2
    name, profile_key, rest = argv[0], argv[1], argv[2:]
    support = None
    if rest[:1] == ["--support"]:
        support, rest = rest[1], rest[2:]
    try:
        print(slice_plate(name, rest, profile_key, support))
    except (SliceError, FileNotFoundError) as e:
        print(f"REFUSED: {e}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
