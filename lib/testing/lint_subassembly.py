"""The subassembly/ pattern, enforced rather than documented.

Every `<name>_mech.py` that builds geometry (`get_shape()`) must have a matching
`<name>_check.py` exposing `check_all()`.
"""

import ast
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(HERE)
SUB = os.path.join(LIB, "subassembly")


def _functions(path: str) -> set:
    with open(path) as fh:
        tree = ast.parse(fh.read(), filename=path)
    return {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def main() -> int:
    if not os.path.isdir(SUB):
        print(f"  FAIL  no {SUB}")
        return 1
    files = [f for f in sorted(os.listdir(SUB)) if f.endswith(".py") and not f.startswith("_")]
    mechs = {f[: -len("_mech.py")] for f in files if f.endswith("_mech.py")}
    checks = {f[: -len("_check.py")] for f in files if f.endswith("_check.py")}
    bad = []

    for name in sorted(mechs):
        path = os.path.join(SUB, f"{name}_mech.py")
        fns = _functions(path)
        builds = "get_shape" in fns
        if not builds:
            continue
        if name not in checks:
            bad.append(f"{name}_mech.py builds geometry but has no {name}_check.py")

    for name in sorted(checks):
        fns = _functions(os.path.join(SUB, f"{name}_check.py"))
        if "check_all" not in fns:
            bad.append(f"{name}_check.py does not expose check_all()")

    builders = sorted(
        n for n in mechs if "get_shape" in _functions(os.path.join(SUB, f"{n}_mech.py"))
    )
    shared = sorted(n for n in mechs if n not in builders)
    if not builders and not checks:
        bad.append("no mechanisms or checks found in subassembly/")
    print(f"  {len(builders)} mechanism(s): {', '.join(builders) or '-'}")
    print(f"  {len(shared)} shared module(s): {', '.join(shared) or '-'}")
    print(f"  {len(checks)} check(s): {', '.join(sorted(checks)) or '-'}")
    for b in bad:
        print(f"  FAIL  {b}")
    print(f"\n  {'PASS' if not bad else 'FAIL'}  subassembly/ pattern")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
