"""Checks `lib/variant/<name>.py` against the `lib/part/<name>.py` or `lib/step/<name>.py` base.

Adapted from `GBA/CAD/lib/testing/variant_manifest.py`:
- FDM/Laser part variants (`PROCESS in ("fdm", "laser")`) derive from `lib/part/<name>.py`.
- Bought-component & reference cleanup variants (`PROCESS in ("component", "reference")`)
  derive from `lib/step/<name>.py` (for example stripping tall USB/RJ45/GPIO headers off
  `step/radxa_x4.py`, or stripping external power/AV cables off `step/n64_console_raw.py`).
- Every chunk of geometry that differs (`removed = base - variant`, `added = variant - base`)
  must be claimed by a declared `DEVIATIONS` entry of the matching `kind`, inside its `bbox`,
  and within `volume_mm3 +- tolerance_mm3` (or `area_mm2 +- tolerance_mm2` for open-shell
  reference assemblies).
"""

import os
from collections import Counter

LIB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VARIANT_DIR = os.path.join(LIB_DIR, "variant")
PART_DIR = os.path.join(LIB_DIR, "part")
STEP_DIR = os.path.join(LIB_DIR, "step")

CHUNK_IGNORE_MM3 = 0.001  # boolean sliver noise threshold
FUZZY_MM = 1e-4


def variant_names():
    if not os.path.isdir(VARIANT_DIR):
        return []
    return sorted(
        f[:-3] for f in os.listdir(VARIANT_DIR) if f.endswith(".py") and not f.startswith("_")
    )


def _solid_key(s) -> tuple:
    """A solid's geometry, to the micron: faces, volume, centre and bounding box."""
    c, b = s.Center(), s.BoundingBox()
    return (
        len(s.Faces()),
        round(s.Volume(), 3),
        *(round(v, 3) for v in (c.x, c.y, c.z, b.xmin, b.ymin, b.zmin, b.xmax, b.ymax, b.zmax)),
    )


def _overlaps(p, q) -> bool:
    """Whether bounding boxes `p` and `q` touch."""
    return all(
        lo_p <= hi_q and lo_q <= hi_p
        for lo_p, hi_p, lo_q, hi_q in (
            (p.xmin, p.xmax, q.xmin, q.xmax),
            (p.ymin, p.ymax, q.ymin, q.ymax),
            (p.zmin, p.zmax, q.zmin, q.zmax),
        )
    )


def _chunks(a, b):
    """Solids of `a` that are not in `b`, biggest first, noise dropped.

    A component variant keeps most of its reference's solids unchanged (Radxa's board: 357 of
    363). An unchanged solid subtracts to nothing, so only the solids of `a` that `b` lacks are
    cut, each against the solids of `b` near it: the same result as `a.cut(b)` without one
    boolean over hundreds of solids, which outran the gate's timeout. Solids are matched by
    geometry, not identity: the base and the variant each import the STEP, so the same solid is
    two different shapes.
    """
    import cadquery as cq  # noqa: PLC0415

    a_solids, b_solids = a.Solids(), b.Solids()
    unmatched = Counter(_solid_key(t) for t in b_solids)
    rest = []
    for s in a_solids:
        k = _solid_key(s)
        if unmatched[k] > 0:
            unmatched[k] -= 1
        else:
            rest.append(s)
    try:
        if len(rest) == len(a_solids):
            out = a.cut(b).Solids()
        else:
            boxes = [s.BoundingBox() for s in rest]
            near = [t for t in b_solids if any(_overlaps(sb, t.BoundingBox()) for sb in boxes)]
            changed = cq.Compound.makeCompound(rest)
            out = changed.cut(*near).Solids() if near else changed.Solids()
    except Exception as exc:
        print(f"variant_manifest: _chunks cut failed: {exc}")
        return None
    return sorted(
        (s for s in out if s.Volume() > CHUNK_IGNORE_MM3),
        key=lambda s: -s.Volume(),
    )


def _fuzzy_cut(a, b):
    """`a` minus `b` with a small fuzzy tolerance."""
    import cadquery as cq  # noqa: PLC0415
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut  # noqa: PLC0415
    from OCP.TopTools import TopTools_ListOfShape  # noqa: PLC0415

    op = BRepAlgoAPI_Cut()
    args, tools = TopTools_ListOfShape(), TopTools_ListOfShape()
    args.Append(a.wrapped)
    tools.Append(b.wrapped)
    op.SetArguments(args)
    op.SetTools(tools)
    op.SetFuzzyValue(FUZZY_MM)
    op.Build()
    if not op.IsDone():
        return None
    return cq.Shape.cast(op.Shape())


def _in_box_fallback(minuend, subtrahend, bbox):
    """Volume of `(minuend - subtrahend)` inside `bbox` using a fuzzy boolean."""
    import cadquery as cq  # noqa: PLC0415

    x0, y0, z0, x1, y1, z1 = bbox
    box = cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))
    try:
        cut = _fuzzy_cut(minuend.intersect(box), subtrahend.intersect(box))
    except Exception as exc:
        print(f"variant_manifest: _in_box_fallback failed: {exc}")
        return None
    if cut is None:
        return None
    return sum(s.Volume() for s in cut.Solids() if s.Volume() > CHUNK_IGNORE_MM3)


def _inside(chunk, bbox):
    c = chunk.BoundingBox()
    x0, y0, z0, x1, y1, z1 = bbox
    return (
        c.xmin >= x0 - 1e-6
        and c.xmax <= x1 + 1e-6
        and c.ymin >= y0 - 1e-6
        and c.ymax <= y1 + 1e-6
        and c.zmin >= z0 - 1e-6
        and c.zmax <= z1 + 1e-6
    )


def _subshape_key(sh) -> tuple[int, float, float, float]:
    c = sh.Center()
    return (len(sh.Faces()), round(abs(sh.Area()), 1), round(c.x, 1), round(c.y, 1))


def _check_reference_shells(name, declared, vs, ps):
    """Manifest check for open-shell reference CAD cleanup (`PROCESS == 'reference'`)."""
    rows = []
    p_items = list(ps)
    v_items = list(vs)
    v_keys = {_subshape_key(it) for it in v_items}
    p_keys = {_subshape_key(it) for it in p_items}

    removed = [it for it in p_items if _subshape_key(it) not in v_keys]
    added = [it for it in v_items if _subshape_key(it) not in p_keys]

    unclaimed = []
    tally = {k: {"removed": 0.0, "added": 0.0} for k in declared}
    for kind, items in (("removed", removed), ("added", added)):
        for ch in items:
            owner = next(
                (
                    k
                    for k, d in declared.items()
                    if d.get("kind") == kind and _inside(ch, d["bbox"])
                ),
                None,
            )
            area = abs(ch.Area())
            if owner is None:
                b = ch.BoundingBox()
                unclaimed.append(
                    f"{kind} {area:.2f}mm2 at x {b.xmin:.2f}..{b.xmax:.2f} "
                    f"y {b.ymin:.2f}..{b.ymax:.2f} z {b.zmin:.2f}..{b.zmax:.2f}"
                )
            else:
                tally[owner][kind] += area

    rows.append(
        (
            f"VARIANT   {name} changes nothing it did not declare",
            not unclaimed,
            (
                f"{len(removed)} removed and {len(added)} added subshape(s) against "
                f"lib/step/{name}.py, every one claimed by a DEVIATIONS entry"
                if not unclaimed
                else "UNDECLARED GEOMETRY: " + "; ".join(unclaimed[:4])
            ),
        )
    )
    for k, d in declared.items():
        got = tally[k][d.get("kind", "removed")]
        want = d.get("area_mm2")
        tol = d.get("tolerance_mm2", 5.0)
        if want is None:
            continue
        rows.append(
            (
                f"VARIANT   {name}.{k} is the size it claims",
                abs(got - want) <= tol,
                f"{d.get('kind')} {got:.2f}mm2 against declared {want} +-{tol} "
                f"({d.get('why', 'no reason')})",
            )
        )
    return rows


def check_variant(name, load):
    """Return `(label, passed, message)` rows for `lib/variant/<name>.py`."""
    rows = []
    vpath = os.path.join(VARIANT_DIR, f"{name}.py")
    try:
        vmod = load(vpath, f"variant_{name}")
    except Exception as exc:
        rows.append((f"VARIANT   {name} builds", False, f"RAISED {exc}"))
        return rows

    proc = getattr(vmod, "PROCESS", "fdm")
    base_name = getattr(vmod, "DERIVES_FROM", name)
    if proc in ("component", "reference"):
        bpath = os.path.join(STEP_DIR, f"{base_name}.py")
        base_label = f"lib/step/{base_name}.py"
    else:
        bpath = os.path.join(PART_DIR, f"{base_name}.py")
        base_label = f"lib/part/{base_name}.py"

    if not os.path.exists(bpath):
        rows.append(
            (
                f"VARIANT   {name} derives from a real base",
                False,
                f"lib/variant/{name}.py has no {base_label} to derive from",
            )
        )
        return rows

    try:
        pmod = load(bpath, f"base_{base_name}")
        declared = getattr(vmod, "DEVIATIONS", None)
    except Exception as exc:
        rows.append((f"VARIANT   {name} builds", False, f"RAISED {exc}"))
        return rows

    if not declared:
        rows.append(
            (
                f"VARIANT   {name} declares what it changes",
                False,
                "no DEVIATIONS dict declared on variant module",
            )
        )
        return rows

    try:
        vs, ps = vmod.get_shape(), pmod.get_shape()
    except Exception as exc:
        rows.append((f"VARIANT   {name} differences measurable", False, f"RAISED {exc}"))
        return rows

    if proc == "reference":
        return _check_reference_shells(base_name if base_name != name else name, declared, vs, ps)

    try:
        removed = _chunks(ps, vs)
        added = _chunks(vs, ps)
    except Exception as exc:
        rows.append((f"VARIANT   {name} differences measurable", False, f"RAISED {exc}"))
        return rows

    if removed is None or added is None:
        rows.append(
            (
                f"VARIANT   {name} differences measurable",
                False,
                f"boolean difference against {base_label} failed to compute",
            )
        )
        return rows

    unclaimed = []
    tally = {k: {"removed": 0.0, "added": 0.0} for k in declared}
    for kind, chunks in (("removed", removed), ("added", added)):
        for ch in chunks:
            owner = next(
                (
                    k
                    for k, d in declared.items()
                    if d.get("kind") == kind and _inside(ch, d["bbox"])
                ),
                None,
            )
            if owner is None:
                b = ch.BoundingBox()
                unclaimed.append(
                    f"{kind} {ch.Volume():.4f}mm3 at x {b.xmin:.2f}..{b.xmax:.2f} "
                    f"y {b.ymin:.2f}..{b.ymax:.2f} z {b.zmin:.2f}..{b.zmax:.2f}"
                )
            else:
                tally[owner][kind] += ch.Volume()

    rows.append(
        (
            f"VARIANT   {name} changes nothing it did not declare",
            not unclaimed,
            (
                f"{len(removed)} removed and {len(added)} added chunk(s) against "
                f"{base_label}, every one claimed by a DEVIATIONS entry"
                if not unclaimed
                else "UNDECLARED GEOMETRY: "
                + "; ".join(unclaimed[:4])
                + (f" (+{len(unclaimed) - 4} more)" if len(unclaimed) > 4 else "")
            ),
        )
    )

    for k, d in declared.items():
        got = tally[k][d.get("kind", "removed")]
        want, tol = d.get("volume_mm3"), d.get("tolerance_mm3", 1.0)
        if want is None:
            continue
        how = ""
        if got == 0.0 and want > 0.0:
            a, b = (vs, ps) if d.get("kind") == "added" else (ps, vs)
            fb = _in_box_fallback(a, b, d["bbox"])
            if fb is not None:
                got, how = fb, " (fuzzy re-measure in its bbox)"
        rows.append(
            (
                f"VARIANT   {name}.{k} is the size it claims",
                abs(got - want) <= tol,
                f"{d.get('kind')} {got:.4f}mm3{how} against declared {want} +-{tol} "
                f"({d.get('why', 'no reason')})",
            )
        )
    return rows


def check_all(load):
    rows = []
    for name in variant_names():
        rows += check_variant(name, load)
    return rows
