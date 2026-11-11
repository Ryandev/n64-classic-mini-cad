# Design rules

Each rule here came out of a real fault or a published process limit. The automated subset runs as `lib/cad_lint.py`; the rest is enforced by `*_check.py` rows in `lib/gate.py`.

---

## 1. Datums and fits

From [`TOLERANCES.md`](TOLERANCES.md), in four lines:

- **One feature holds an axis.** Everything else on that axis has clearance. Two features on the same axis is over-constraint.
- **Clearance beats the stack, not one edge.** Count the cut/printed edges in the gap, take RSS (`sqrt(N) x tol`), and allow at least 3x.
- **Never draw male and female at the same nominal.** That is a 50% interference rate per feature; across four corners it seats one time in sixteen.
- **Don't chain.** Reference every part in a group to one shared datum, not each to its neighbour.

When a mating pair is added or changed, its row goes into the Joint Register in [`TOLERANCES.md`](TOLERANCES.md) in the same edit. If you cannot write the row, the joint is not designed yet.

---

## 2. Process limits

### FDM, Bambu X2D / P1S, PETG & PLA

- **Minimum wall: 0.8 mm** (two perimeters at a 0.4 mm nozzle). That is the **process floor** — the thinnest feature the nozzle can lay down at all, for a local detail such as a badge stroke or a small lip. It is **not** a structural wall thickness. A shell wall, a bracket arm, a boss ring, or a floor that carries screw preload or switch reaction force needs **>= 1.5–2.0 mm** (4–5 perimeters), checked against the load it actually sees.
- **G1 — Unribbed span / flexural stiffness (`L / t <= 20`):** Any flat plate or bracket floor carrying a mechanical load (button stop, switch actuation, insert pull-out, or spring reaction) with free span `L` and thickness `t` exceeding `L / t > 20` must either be thickened or stiffened with ribs of height `>= 2t`.
- **G2 — Declared visible faces & print orientation priority:** Every printed part must declare which of its faces are **visible in the finished console** (`VISIBLE_FACES`) alongside its `PRINT_NORMAL`. Print orientation is chosen in this strict order:
  1. **Cosmetic:** visible faces must never take support scars and should avoid raw staircase stepping on shallow domes (`10–35 deg` from horizontal -> use adaptive layer height `0.08–0.12 mm` or orient steeper).
  2. **Structural:** primary tensile/bending or pin-tearout loads run along XY perimeters, not across Z layer lines.
  3. **Support minimization:** overhang area `> 50 deg` from vertical is minimized after (1) and (2) are satisfied.
- **G3 — Bed contact & footprint stability:** A printed part's first-layer contact area on the build plate at `z_min` must be `>= 15%` of its XY bounding-box footprint (or use a flat parting face on the bed), and its height-to-minimum-base-span ratio `H / min(W_bed, D_bed)` must be `<= 3.0`.
- **G11 — Two locators per split:** Any split part joined at bench assembly (`>= 2` pieces) requires **at least 2 locating features** (pins, dowels, or stepped lip corners) separated by `>= 2x` feature diameter to constrain rotation in the split plane, or a closed perimeter tongue-and-groove lip.
- **G12 — No support inside sliding bores or blind counterbores:** Any bore or guide track that mates with a moving plunger, slider, or dowel must either run within `<= 45 deg` of vertical in the print orientation, use a teardrop/bridged crown, or be reamed post-print.
- **G13 — Zero bought-part interference on the printed solid:** Every bought component (`Radxa X4`, `USB-A` jacks, `RJ45` keystone/panel mount, tactile switches, heat-set inserts, magnets, fasteners) must be boolean-checked (`BRepAlgoAPI_Common`) against the mating printed solid at rest and across full travel (`intersection volume == 0.00 mm^3`).
- **Overhang: 50 deg** from vertical before the slicer adds support (`lib/printable.py`).
- **XY tolerance: +/-0.2 mm.** Fits narrower than ~0.4 mm total are inside the process band and must be verified by a physical print coupon.

### Laser, 3 mm cast acrylic (optional fixtures / templates)

- **Minimum wall: 1.5 mm** between any two cuts (`lib/min_wall.py`).
- **Nothing narrower than `KERF / 2` (0.15 mm)** can exist at all.
- **Internal corners:** the beam leaves `r = KERF / 2 = 0.15 mm` when you draw a sharp corner. Relieve internal corners where a square male feature seats to `0.2–0.5 mm`.

---

## 3. Model discipline

- **Every part declares `PROCESS = "fdm" | "laser"` and `MANUFACTURE = "fdm" | "laser"`** at the top of `lib/part/<name>.py`. Checked by `lib/cad_lint.py` and `lib/testing/export_validate.py`.
- **Single source of truth.** A dimension that appears in two files lives in `lib/assembly/datum.py` (or the owning module) and is imported by the other.
- **A rigid motion has determinant +1.** Any coordinate change is a rotation + translation, never a reflection (`det == -1`). Checked by `lib/assembly/datum_check.py`.
- **Nominal and measured are different quantities.** Do not "fix" a nominal model to match a one-off sheet or filament shrinkage; record both and name which is which.

---

## 4. Check-writing rules

1. **Write the failing row first.** Run `lib/gate.py`, watch it print `FAIL` for the right reason, then fix the geometry. Confirm with `lib/gate_selftest.py`.
2. **A row that checks nothing is a failing row.** If a check finds 0 parts or 0 features, it must return `False`, never `True`.
3. **Measure the outcome, not the constant.** Do not import a constant from the module under test and compare it to itself. Measure the resulting `cq.Shape` (`BoundingBox()`, `Volume()`, `BRepAlgoAPI_Common`, `BRepExtrema_DistShapeShape`, or `BRepClass3d_SolidClassifier`).
4. **Never treat a bounding box as a surface.** Curved shells and sloped N64 decks are not axis-aligned boxes; use boolean intersection or point classification on the actual solid.
