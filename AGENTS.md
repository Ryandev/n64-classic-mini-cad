# Working in `cad/`

Repo-wide rules in [`../AGENTS.md`](../AGENTS.md) apply here. This file covers CadQuery, geometry checks, and mechanical design rules for `cad/`.

## Environment & Gate

All Python commands in `cad/` run inside the `cadquery` micromamba environment via `./run`:

```bash
./run all        # lint + gate + export + export-validate
./run gate       # run all *_check.py rows in parallel (cached by recorded file reads)
./run selftest   # plant geometry mutations and prove ./run gate fails on each
./run lint       # ruff check + ruff format --check + AST structural lint
./run export     # write STEP/SVG files into export/
./run bom        # regenerate notes/BOM_COMPLETE.md
```

Also re-run `../frontend/run check` from the repo root before finishing so repo-wide `typos`, `shellcheck`, `detect-secrets`, and `test_docs.py` pass.

## Directory Layout

- `PROJECT.md`: coordinate frame (`+X` right, `+Y` rear, `+Z` up) and `REQ-01..REQ-12`.
- `notes/`:
  - [`notes/DESIGN_RULES.md`](notes/DESIGN_RULES.md): datums, fits, FDM/laser process rules (`G1..G13`), model discipline, and check-writing rules.
  - [`notes/TOLERANCES.md`](notes/TOLERANCES.md): process figures, fit classes, and the **Joint Register**.
  - [`notes/MANUFACTURING.md`](notes/MANUFACTURING.md): printer settings, heat-set insert specs, and post-processing.
  - [`notes/TROUBLESHOOTING.md`](notes/TROUBLESHOOTING.md): OCCT/CadQuery pitfalls and fixes.
- `lib/`:
  - `lib/assembly/datum.py` & `lib/assembly/datum_check.py`: master dimensions, coordinate transforms, and envelope/fitment gate checks.
  - `lib/component/`: bought hardware reference envelopes (`radxa_x4.py`).
  - `lib/part/`: individual parametric parts exposing `PROCESS = "fdm" | "laser"`, `MANUFACTURE = "fdm" | "laser"`, and `get_shape() -> cq.Shape`.
  - `lib/subassembly/`: multi-part mechanisms (`<name>_mech.py` + `<name>_check.py`). Every `*_mech.py` that exposes `get_shape()` **must** have a matching `*_check.py` exposing `check_all()`, enforced by `lib/testing/lint_subassembly.py`.
  - `lib/gate.py` & `lib/gate_selftest.py`: parallel cached gate runner and mutation self-tester.
  - `lib/printable.py`, `lib/min_wall.py`, `lib/standoffs.py`, `lib/cad_lint.py`, `lib/bom.py`: shared geometry checks and helpers.

## Rules

1. **Units:** Millimetres (`mm`) everywhere. Angles carry a `_DEG` suffix.
2. **No string selectors on curved/boolean geometry:** Select faces/edges by measured coordinates instead of `.faces(">Z")` string selectors in `lib/part/` (enforced by `lib/testing/lint_structure.py`).
3. **One feature holds an axis:** Every mating pair in [`notes/TOLERANCES.md`](notes/TOLERANCES.md) names one datum per axis; every other feature on that axis clears the tolerance stack.
4. **Never treat a bounding box as a surface:** Check interference by boolean common volume (`BRepAlgoAPI_Common`) or `BRepExtrema_DistShapeShape` / point classification (`BRepClass3d_SolidClassifier`), not bounding-box arithmetic.
5. **Write the failing row first, and red-confirm it:** Add a mutation case in `lib/gate_selftest.py` for every new check module.

## Lessons (cooling, 2026-11-11)

- **A sampled grid misses thin parts; a boolean doesn't.** A 1 mm occupancy grid placed the fan
  clear of everything; the boolean `G13_COOL` row then found it inside the USB retainer bridge.
  Use grids to search, booleans to decide.
- **A clash bounding box is not geometry.** The duct was designed around "tub structure up to
  Z 11.6" read off an intersection's bounding box; point classification showed the corner was
  empty, and the plenum leaked there. Classify points or measure volumes (rule 4).
- **Airflow parts need a seal check, not just a clash check.** Three leaks (a fan bore cutting the
  plenum's front wall, an open seat strip, a screw-head relief) passed every fit row. `COOL_SEAL`
  floods air through a voxel grid and traces the route of any leak; it found all of them.
- **A check's modelling shortcut is a blind spot; check the shortcut too.** `COOL_SEAL` treats the
  fan as a solid wall, so it never asked where the fan blows. 13 % of the bore overhung the
  plenum's front wall onto open case air, a bypass the thermal model (all flow through the pins)
  couldn't see; the owner spotted it in FreeCAD. `COOL_FAN` now requires every voxel under the
  bore to be wall or flooded plenum (red-confirmed on the old duct: 56 mm2 open).
  The fix made the old `COOL_SEAL` selftest mutation (a slot through the front wall) harmless,
  since that wall now opens into the pocket: the selftest flagged it as uncaught. A planted defect
  must stay a defect after a design change; it now removes the pocket floor instead.
