"""Part verification harness (`./run test [part_names...]`).

Runs structural lint, subassembly pattern lint, and `lib/printable.py` checks on
every native part in `lib/part/`.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import printable  # noqa: E402
from testing.lint_structure import run as run_lint  # noqa: E402
from testing.lint_subassembly import main as run_sub_lint  # noqa: E402
from testing.load import load_by_path  # noqa: E402

LIB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PART_DIR = os.path.join(LIB_DIR, "part")


def _names_in(dir_path):
    if not os.path.isdir(dir_path):
        return []
    return sorted(
        f[:-3] for f in os.listdir(dir_path) if f.endswith(".py") and not f.startswith("_")
    )


def run(only=None):
    print("=== structural lint ===\n")
    if not run_lint():
        print("\nlint failed -- fix structural violations before trusting geometry checks")
        return False
    print()

    print("=== subassembly/ pattern (mech <-> check) ===\n")
    if run_sub_lint() != 0:
        print("\nsubassembly lint failed")
        return False
    print()

    names = _names_in(PART_DIR)
    if only:
        unknown = [n for n in only if n not in names]
        if unknown:
            print(f"unknown part name(s): {', '.join(unknown)}")
            print(f"available: {', '.join(names)}")
            return False
        names = [n for n in names if n in only]

    if not names:
        print("FAIL: no parts found in lib/part/")
        return False

    print(f"=== {len(names)} part(s) to check ===\n")
    all_passed = True
    for name in names:
        mod = load_by_path(os.path.join(PART_DIR, f"{name}.py"), f"part_{name}")
        shape = mod.get_shape()
        up = getattr(mod, "PRINT_NORMAL", (0, 0, 1))
        rows = printable.check_part(name, shape, up=up, min_bed_ratio=0.15)
        part_ok = all(ok for _, ok, _ in rows)
        print(f"[{'PASS' if part_ok else 'FAIL'}] {name}")
        for label, ok, msg in rows:
            print(f"    [{'pass' if ok else 'FAIL'}] {label}: {msg}")
        if not part_ok:
            all_passed = False
        print()

    print(f"overall: {'PASS' if all_passed else 'FAIL'} ({len(names)} part(s))")
    return all_passed


if __name__ == "__main__":
    sys.exit(0 if run(only=sys.argv[1:] or None) else 1)
