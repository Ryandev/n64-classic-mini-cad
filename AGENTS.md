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

## Lessons (Radxa reference, C10, 2026-11-12)

- **A reference model is built by a script, never by hand.** `lib/step/radxa_x4.step` had been
  assembled by hand: connectors picked by index, an invented HDMI shield, a USB-C socket with a
  corner cut away "to clear the standoff". Every clearance row graded the case against a board
  edited to pass. `./run radxa-ref` now builds it from Radxa's download (SHA-256 pinned), whole,
  moved only onto the datum's hole pattern; `RADXA_REF` holds it to Radxa's 363 solids. On the
  real board the duct, the upper shell and a Radxa standoff all touched parts the edited model
  lacked (G13_COOL, G13_FULL, G13_CLEAR); each got a relief, and the standoffs a Ø6.4 top step.
- **A boolean that never finishes is a failing check, not a slow one.** The variant manifest cut
  the whole 363-solid board in one boolean: 887 s, then "Null TopoDS_Shape". Unchanged solids are
  now matched by geometry and only the changed ones are cut (147 s). Matching by identity
  (`isSame`) silently matched nothing: the base and variant each import the STEP.
- **One number, one meaning.** A deviation's `volume_mm3` is what the manifest measures removed
  (a header less its pins inside the PCB). Reusing it to *find* the header solid broke both; the
  header is now the dominant solid in its box, and an ambiguous box fails loud.

## Lessons (port doors, C1, 2026-11-12)

- **A moving part's check must move everything attached to it, through the whole arc.** J05 swung
  the bare doors at 30 and 80 deg and passed; the glued port bezels, which stand 2.47 mm proud of
  the hinge, hit the sill from 13 deg. J05 now swings doors + bezels every 5 deg to 90 deg and
  requires 0.3 mm clear when open flat (red-confirmed: 48.9 mm3 with the old hinge).
- **The owner's idea beat the agent's options.** Asked to fix it, the agent offered a sill notch,
  an external hinge or trimmed bezels, and argued a lower hinge couldn't help (it only looked at
  how far the bezel drops below the pin, not that the case front is ~1 mm ahead of it). The owner's
  lower hinge with a taller door clears with no visible change. Model a suggestion before arguing.

## Running the heavy checks (the owner's laptop)

- `./run gate` takes ~5–10 min at full load; `N64_GATE_JOBS=2 ./run gate` caps the workers.
- `./run selftest` reruns a 3–6 min check per mutation (hours in all): after a change, run the
  mutations for the rows it touched with `./run selftest --only ROW [ROW...]`.
- Run heavy jobs one at a time, say when each starts and ends, and leave nothing running.
- Never `pkill -f NAME` from a shell whose own command line contains NAME: it kills itself.

## Lessons (switch actuation, C3, 2026-11-12)

- **A mechanism check must move the real parts.** `OMRON_ACT` multiplied constants (a 0.72 lever
  ratio, a 3.2 mm preload) and passed while the button's flat underside actually met the lever's
  raised tip, 1:1 and 4 mm off-centre, so a nominal switch never clicked. It now lowers each real
  button onto the real lever and reads off where the tip sits (red-confirmed: the old 1.9 mm
  travel fails).
- **Check the agent's arithmetic before the owner decides on it.** The agent told the owner the
  ridge would keep every switch within Omron's guaranteed overtravel; it can't, because the OP
  spread (1.6 mm) exceeds OT (1.2 mm) whatever the ratio. Corrected before building.

## Lessons (self-graded rows, C8, 2026-11-13)

- **A planted defect must change the geometry the row measures.** Two C8 mutations proved
  nothing: one changed `LED_SHAFT_D`, which no part uses (it only fed the old constant-based J07),
  and one swapped the button X datums, which crashed the part builds instead of making a wrong
  console. Mutate something a part is built from, and confirm the row (not the build) fails.
- **Measuring finds what constants hide.** On the solids: the light pipe's tightest gap is
  0.06 mm (the datum claimed 0.10), the RJ45 jack is 1.7 mm from the wall (constants said 3.0),
  and the M3x12 corner screws engaged only 2.8 mm of their insert (now M3x14, J01_SCREW).

## Lessons (published pictures, 2026-11-14)

- On the owner's machine `cad/local/` holds the owner's own plaque lettering, and every local build
  engraves it. A README re-render from a local export came out with the private lettering on
  the plaque; it was caught by looking before committing. Anything rendered for the published
  repo is built with **`N64_PUBLIC=1`**, which forces the public CLASSIC lettering
  (`part/shared/n64_text._local_glyphs`). CI never has `cad/local/`, so released files are
  public by construction. Look at every picture before committing it.
