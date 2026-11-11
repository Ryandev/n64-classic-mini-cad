# CadQuery & OCCT troubleshooting

## 1. String selectors on curved or boolean geometry

CadQuery string selectors such as `.faces(">Z")` or `.edges("|Z")` evaluate face centres of mass and skip non-linear edges. On the N64's curved side swoops and sloped decks they silently select the wrong face.

- **Fix:** Select faces and edges by measured coordinates (`min/max(shape.Faces(), key=lambda f: f.Center().z)`) or construct solids directly in `cq.Workplane("XY")` at explicit `Z` offsets and combine with `.union()` / `.cut()`.
- **Enforced by:** `string-selector` rule in `lib/testing/lint_structure.py`.

## 2. `isValid()` is not a self-intersection check

`shape.isValid()` wraps `BRepCheck_Analyzer`, which returns `True` even when two solids self-intersect.

- **Fix:** Always run `BRepAlgoAPI_Check` (`lib/printable.py:check_manifold`) or explicit boolean intersection (`BRepAlgoAPI_Common`) when checking interferences.
- **Enforced by:** `isvalid-as-gate` rule in `lib/testing/lint_structure.py`.

## 3. Fillets before booleans

Applying `.fillet()` or `.chamfer()` before `.union()` or `.cut()` creates tangent sliver faces that cause later OCCT booleans to fail or drop solids.

- **Fix:** Apply all booleans first, then fillet final edges last.
- **Enforced by:** `fillet-before-boolean` rule in `lib/testing/lint_structure.py`.
