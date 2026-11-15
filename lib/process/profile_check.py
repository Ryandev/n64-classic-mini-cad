"""Every part that is made names a manufacturing profile, and that profile is proven.

A made part (`PROCESS` "fdm" or "resin", in `part/` or `variant/`) must declare `PROFILE`, naming
a profile in `process/profiles.py` of the same family whose allowances come from measured prints.
A part moved to an unproven process (resin before a resin print has been measured) fails here
until a print of it has been measured.
"""

import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from process.profiles import PROFILES  # noqa: E402

LIB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MADE = ("fdm", "resin")


def _modules():
    for pkg in ("part", "variant"):
        for f in sorted(os.listdir(os.path.join(LIB, pkg))):
            if f.endswith(".py") and not f.startswith("_"):
                yield pkg, f[:-3]


def check_all():
    rows = []
    for name, p in PROFILES.items():
        rows.append(
            (
                f"PROFILE {name} allowances",
                True,
                f"hole {p.hole_shrink if p.hole_shrink is None else round(p.hole_shrink, 3)} "
                f"mm/side, contour "
                f"{p.contour_growth if p.contour_growth is None else round(p.contour_growth, 3)} "
                "mm/side from "
                f"{len(p.measurements)} measured feature(s)"
                + ("" if p.proven else " -- UNPROVEN: no part may use it yet"),
            )
        )
    for pkg, mod_name in _modules():
        mod = importlib.import_module(f"{pkg}.{mod_name}")
        family = getattr(mod, "PROCESS", None)
        if family not in MADE:
            continue
        key = getattr(mod, "PROFILE", None)
        profile = PROFILES.get(key)
        if profile is None:
            ok, msg = False, f"PROCESS={family!r} but PROFILE={key!r} names no profile"
        elif profile.family != family:
            ok, msg = False, f"PROFILE {key!r} is a {profile.family} profile, part is {family!r}"
        elif not profile.proven:
            ok, msg = False, f"PROFILE {key!r} has no measured print behind it"
        else:
            ok = True
            msg = (
                f"{key}: holes -{profile.hole_shrink:.2f}, outside faces "
                f"{profile.contour_growth:+.2f} mm/side"
            )
        rows.append((f"PROFILE {pkg}/{mod_name}", ok, msg))
    return rows


def main():
    rows = check_all()
    for label, ok, msg in rows:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
        print(f"        {msg}")
    return 0 if all(ok for _l, ok, _m in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
