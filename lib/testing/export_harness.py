"""Export every part in `lib/part/` and `lib/variant/` to `export/<name>/`.

`--printable-only` exports just the FDM and laser parts and the print plate. It needs none of the
third-party reference STEPs (git-ignored, see CREDITS.md), so it is what a fresh clone and CI run.
"""

import hashlib
import os
import re
import sys

import cadquery as cq
from cadquery.occ_impl.exporters.svg import getSVG
from cadquery.occ_impl.shapes import Shape
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.gp import gp_Dir, gp_Pln, gp_Pnt, gp_Trsf, gp_Vec

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plate  # noqa: E402
from assembly import n64_mini  # noqa: E402
from testing.load import load_by_path  # noqa: E402

PART_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "part")
VARIANT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "variant")
EXPORT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "export"
)


def export_shape(mod):
    """The shape `export/<name>/<name>.step` holds: placed in the console if the module places it.

    export_validate.py re-imports each file against this same function (D4: it compared placed
    exports with `get_shape()`, so a placed component could be written wrong and still pass).
    """
    return mod.placed() if hasattr(mod, "placed") else mod.get_shape()


def _names_in(dir_path):
    if not os.path.exists(dir_path):
        return []
    return sorted(
        f[:-3] for f in os.listdir(dir_path) if f.endswith(".py") and not f.startswith("_")
    )


def inject_mm_units(svg_str, b):
    svg_str = re.sub(
        r"<svg[^>]*>",
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{b.xlen:.3f}mm" height="{b.ylen:.3f}mm" '
        f'viewBox="0 0 {b.xlen:.3f} {b.ylen:.3f}">',
        svg_str,
    )
    svg_str = re.sub(
        r'<g transform="[^"]*"',
        f'<g transform="scale(1, -1) translate({-b.xmin:.3f}, {-b.ymax:.3f})"',
        svg_str,
    )
    return svg_str


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    printable_only = "--printable-only" in args
    part_names = _names_in(PART_DIR)
    variant_names = _names_in(VARIANT_DIR)

    # When a variant/<name>.py exists, it supersedes part/<name>.py for export/<name>/<name>.step
    all_modules = [
        (n, os.path.join(PART_DIR, f"{n}.py")) for n in part_names if n not in variant_names
    ] + [(n, os.path.join(VARIANT_DIR, f"{n}.py")) for n in variant_names]

    if not all_modules:
        print("FAIL: no part modules found in lib/part/ or lib/variant/")
        sys.exit(1)

    has_errors = False
    print("=== EXPORT HARNESS ===")

    for name, path in all_modules:
        mod = load_by_path(path, f"export_mod_{name}")
        process = getattr(mod, "PROCESS", None)

        if not process:
            print(f"FAIL: {name} declares no PROCESS.")
            has_errors = True
            continue
        if printable_only and process not in ("fdm", "laser"):
            print(f"Skipping {name} ({process}): --printable-only")
            continue

        print(f"Exporting {name} ({process})...")
        out_dir = os.path.join(EXPORT_DIR, name)
        os.makedirs(out_dir, exist_ok=True)

        if not hasattr(mod, "get_shape"):
            print(f"  -> WARNING: {name} has no get_shape(), skipping export.")
            continue

        if process in ("fdm", "component", "reference"):
            shape = export_shape(mod)
            out_path = os.path.join(out_dir, f"{name}.step")
            cq.exporters.export(shape, out_path)
            print(f"  -> Wrote {out_path}")

        elif process == "laser":
            layers = getattr(mod, "LAYERS", None)
            sheet_t = getattr(mod, "SHEET_T", None)
            if layers is None or sheet_t is None:
                print(f"FAIL: {name} declares PROCESS='laser' but lacks SHEET_T or LAYERS.")
                has_errors = True
                continue

            shape = mod.get_shape()
            unique_svgs = {}
            written_files = 0

            for l_idx, z in enumerate(layers):
                layer_shapes = []
                for solid in shape.Solids():
                    pln = gp_Pln(gp_Pnt(0, 0, z), gp_Dir(0, 0, 1))
                    sec = BRepAlgoAPI_Section(solid.wrapped, pln)
                    sec.Build()
                    if sec.IsDone():
                        sec_shape = Shape(sec.Shape())
                        if not sec_shape.wrapped.IsNull():
                            try:
                                b = sec_shape.BoundingBox()
                                if b.xmin != b.xmax or b.ymin != b.ymax:
                                    layer_shapes.append(sec_shape)
                            except Exception as exc:
                                print(f"  -> section bbox warning: {exc}")

                if not layer_shapes:
                    continue

                if len(layer_shapes) > 1:
                    c_wrapped = layer_shapes[0].wrapped
                    for s in layer_shapes[1:]:
                        c_wrapped = cq.occ_impl.shapes.Compound.makeCompound(
                            [Shape(c_wrapped), s]
                        ).wrapped
                    combined = Shape(c_wrapped)
                else:
                    combined = layer_shapes[0]

                trsf = gp_Trsf()
                trsf.SetTranslation(gp_Vec(0, 0, -z))
                flat = Shape(BRepBuilderAPI_Transform(combined.wrapped, trsf).Shape())

                b = flat.BoundingBox()
                opts = {
                    "width": b.xlen,
                    "height": b.ylen,
                    "marginLeft": 0,
                    "marginTop": 0,
                    "showAxes": False,
                    "projectionDir": (0, 0, 1),
                }

                svg_str = getSVG(flat, opts)
                svg_str = inject_mm_units(svg_str, b)
                h = hashlib.md5(svg_str.encode("utf-8")).hexdigest()

                if h in unique_svgs:
                    shared_idx = unique_svgs[h]
                    print(
                        f"  -> Layer {l_idx} (z={z}) shares identical profile "
                        f"with layer {shared_idx}. Skipped writing."
                    )
                else:
                    unique_svgs[h] = l_idx
                    out_path = os.path.join(out_dir, f"{name}_{l_idx}.svg")
                    with open(out_path, "w") as f:
                        f.write(svg_str)
                    print(f"  -> Wrote {out_path} (Layer {l_idx} at z={z})")
                    written_files += 1

            if written_files == 0:
                print(f"  -> WARNING: No cross-sections found for {name}.")

    if has_errors:
        sys.exit(1)

    compound, placements = plate.export_plate()
    pbb = compound.BoundingBox()
    print(
        f"Exported {len(placements)}-part print plate ({len(placements)} bodies, "
        f"{pbb.xlen:.1f} x {pbb.ylen:.1f} x {pbb.zlen:.1f} mm) -> {plate.PLATE_STEP}"
    )
    if printable_only:
        print("Skipping the console assembly: it embeds the third-party reference models")
        return
    asm_path = n64_mini.export()
    print(f"Exported complete console assembly -> {asm_path}")


if __name__ == "__main__":
    main()
