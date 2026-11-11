"""Structural + geometry-practice rule checker for `lib/step/`, `lib/part/`, and `lib/subassembly/`.

AST-based: walks parsed Python trees and excludes module docstrings before checking.
"""

import ast
import os
from dataclasses import dataclass

FORBIDDEN_IN_STEP_PY = {
    "circle",
    "rect",
    "box",
    "sphere",
    "cylinder",
    "extrude",
    "fillet",
    "chamfer",
    "union",
    "cut",
    "intersect",
    "loft",
    "sweep",
    "polyline",
    "spline",
    "polygon",
    "slot2D",
}

REFERENCE_LOADERS = {"importStep", "Read"}
BOOLEAN_OPS = {"union", "cut", "fuse", "intersect"}
FILLET_OPS = {"fillet", "chamfer"}
GEOMETRY_OPS = (
    BOOLEAN_OPS
    | FILLET_OPS
    | {
        "makeLoft",
        "extrudeLinear",
        "loft",
        "sweep",
        "shell",
        "revolve",
    }
)
SELECTOR_METHODS = {"faces", "edges", "vertices", "solids", "shells", "wires"}

LIB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STEP_DIR = os.path.join(LIB_DIR, "step")
PART_DIR = os.path.join(LIB_DIR, "part")
VARIANT_DIR = os.path.join(LIB_DIR, "variant")
SUB_DIR = os.path.join(LIB_DIR, "subassembly")
TESTING_DIR = os.path.dirname(os.path.abspath(__file__))


@dataclass
class Finding:
    rule: str
    line: int
    message: str


def _parse(path):
    with open(path) as f:
        src = f.read()
    return ast.parse(src, filename=path)


def _call_names(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute):
                names.add(func.attr)
            elif isinstance(func, ast.Name):
                names.add(func.id)
    return names


def _docstring_node(tree):
    if (
        tree.body
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(tree.body[0].value, ast.Constant)
        and isinstance(tree.body[0].value.value, str)
    ):
        return tree.body[0].value
    return None


def _step_string_literals(tree):
    docstring_node = _docstring_node(tree)
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node is docstring_node:
                continue
            if ".step" in node.value.lower():
                found.append(node.value)
    return found


def lint_step_file(path):
    tree = _parse(path)
    calls = _call_names(tree)
    errors = []
    if not (calls & REFERENCE_LOADERS):
        errors.append(f"missing a reference-loading call, one of: {sorted(REFERENCE_LOADERS)}")
    forbidden = calls & FORBIDDEN_IN_STEP_PY
    if forbidden:
        errors.append(f"contains construction ops not allowed in step/ files: {sorted(forbidden)}")
    return errors


def lint_part_file(path):
    tree = _parse(path)
    calls = _call_names(tree)
    errors = []
    if "importStep" in calls:
        errors.append("calls importStep(...) -- part/ files must be pure native construction")
    step_refs = _step_string_literals(tree)
    if step_refs:
        errors.append(f"references a .step path: {step_refs}")
    return errors


def _attr(node):
    return (
        node.func.attr
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        else None
    )


def _calls_in(node):
    return [n for n in ast.walk(node) if isinstance(n, ast.Call)]


def _contains_call_named(node, names):
    return any(
        _attr(c) in names or (isinstance(c.func, ast.Name) and c.func.id in names)
        for c in _calls_in(node)
    )


def _rule_isvalid_as_gate(tree, is_testing):
    if "BRepAlgoAPI_Check" in {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {
        n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)
    }:
        return []
    out = []
    gating = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.While, ast.Assert)):
            gating.update(id(c) for c in _calls_in(node.test))
        elif isinstance(node, ast.BoolOp):
            gating.update(id(c) for c in _calls_in(node))
        elif isinstance(node, ast.Return) and node.value is not None:
            gating.update(id(c) for c in _calls_in(node.value))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _attr(node) == "isValid":
            if id(node) in gating or is_testing:
                out.append(
                    Finding(
                        "isvalid-as-gate",
                        node.lineno,
                        "isValid() decides here, but it wraps BRepCheck_Analyzer which returns "
                        "True on self-intersecting shapes. Use "
                        "cadquery.occ_impl.shapes.check() (BRepAlgoAPI_Check) to gate.",
                    )
                )
    return out


def _rule_silent_sliver_discard(tree):
    out = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
            continue
        if node.func.id != "max":
            continue
        for kw in node.keywords:
            if kw.arg == "key" and _contains_call_named(kw.value, {"Volume"}):
                out.append(
                    Finding(
                        "silent-sliver-discard",
                        node.lineno,
                        "max(..., key=...Volume()) discards every solid but the largest with no "
                        "threshold. Assert the discarded volume is negligible and fail loudly "
                        "above it.",
                    )
                )
    return out


def _rule_boolean_in_loop(tree):
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.For, ast.While)):
            continue
        for c in _calls_in(node):
            if _attr(c) in BOOLEAN_OPS:
                out.append(
                    Finding(
                        "boolean-in-loop",
                        c.lineno,
                        f".{_attr(c)}() inside a loop. Booleans are the dominant runtime cost; "
                        "build a compound and fuse once instead.",
                    )
                )
                break
    return out


def _rule_fillet_before_boolean(tree):
    out = []
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        fillets = [c.lineno for c in _calls_in(fn) if _attr(c) in FILLET_OPS]
        booleans = [c.lineno for c in _calls_in(fn) if _attr(c) in BOOLEAN_OPS]
        if fillets and booleans and min(fillets) < max(booleans):
            out.append(
                Finding(
                    "fillet-before-boolean",
                    min(fillets),
                    f"fillet/chamfer at line {min(fillets)} precedes a boolean at line "
                    f"{max(booleans)} in {fn.name}(). Apply fillets last.",
                )
            )
    return out


def _rule_clean_false(tree):
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for kw in node.keywords:
            if kw.arg == "clean" and isinstance(kw.value, ast.Constant) and kw.value.value is False:
                out.append(
                    Finding(
                        "clean-false",
                        node.lineno,
                        "clean=False is documented to break downstream fillet operations.",
                    )
                )
    return out


def _rule_swallowed_geometry_error(tree):
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue
        if not _contains_call_named(node, GEOMETRY_OPS):
            continue
        for handler in node.handlers:
            body = ast.Module(body=handler.body, type_ignores=[])
            has_raise = any(isinstance(n, ast.Raise) for n in ast.walk(body))
            reports = _contains_call_named(body, {"print", "warn", "warning", "error", "append"})
            if not has_raise and not reports:
                out.append(
                    Finding(
                        "swallowed-geometry-error",
                        handler.lineno,
                        "except around a geometry op neither re-raises nor reports -- a kernel "
                        "failure becomes a silent no-op. Record it at minimum.",
                    )
                )
    return out


def _rule_string_selector(tree):
    out = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and _attr(node) in SELECTOR_METHODS):
            continue
        if (
            node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            out.append(
                Finding(
                    "string-selector",
                    node.lineno,
                    f'.{_attr(node)}("{node.args[0].value}") -- string selectors are documented '
                    "as unreliable on non-planar faces and skip non-linear edges. Select by "
                    "measured coordinates instead.",
                )
            )
    return out


def lint_geometry_practice(path, is_testing=False):
    tree = _parse(path)
    findings = []
    findings += _rule_isvalid_as_gate(tree, is_testing)
    findings += _rule_silent_sliver_discard(tree)
    findings += _rule_boolean_in_loop(tree)
    findings += _rule_fillet_before_boolean(tree)
    findings += _rule_clean_false(tree)
    findings += _rule_swallowed_geometry_error(tree)
    findings += _rule_string_selector(tree)
    return sorted(findings, key=lambda f: f.line)


def _names_in(dir_path):
    if not os.path.isdir(dir_path):
        return []
    return sorted(
        f[:-3] for f in os.listdir(dir_path) if f.endswith(".py") and not f.startswith("_")
    )


def run(show_warnings=True):
    all_errors = {}
    all_warnings = {}

    for name in _names_in(STEP_DIR):
        errors = lint_step_file(os.path.join(STEP_DIR, f"{name}.py"))
        if errors:
            all_errors[f"step/{name}.py"] = errors

    for name in _names_in(PART_DIR):
        path = os.path.join(PART_DIR, f"{name}.py")
        errors = lint_part_file(path)
        if errors:
            all_errors[f"part/{name}.py"] = errors
        warnings = lint_geometry_practice(path)
        if warnings:
            all_warnings[f"part/{name}.py"] = warnings

    for name in _names_in(VARIANT_DIR):
        path = os.path.join(VARIANT_DIR, f"{name}.py")
        errors = lint_part_file(path)
        if errors:
            all_errors[f"variant/{name}.py"] = errors
        warnings = lint_geometry_practice(path)
        if warnings:
            all_warnings[f"variant/{name}.py"] = warnings

    for name in _names_in(SUB_DIR):
        path = os.path.join(SUB_DIR, f"{name}.py")
        warnings = lint_geometry_practice(path, is_testing=name.endswith("_check"))
        if warnings:
            all_warnings[f"subassembly/{name}.py"] = warnings

    for fname in sorted(os.listdir(TESTING_DIR)):
        if not fname.endswith(".py") or fname.startswith("_"):
            continue
        warnings = lint_geometry_practice(os.path.join(TESTING_DIR, fname), is_testing=True)
        if warnings:
            all_warnings[f"testing/{fname}"] = warnings

    if show_warnings and all_warnings:
        total = sum(len(v) for v in all_warnings.values())
        print(f"lint: {total} geometry-practice warning(s) in {len(all_warnings)} file(s)")
        for file, findings in all_warnings.items():
            print(f"  {file}")
            for f in findings:
                print(f"    line {f.line}: [{f.rule}] {f.message}")
        print()

    if not all_errors:
        print("lint: OK -- no structural violations")
        return True

    print(f"lint: {len(all_errors)} file(s) with violations\n")
    for file, errors in all_errors.items():
        print(f"  {file}")
        for e in errors:
            print(f"    - {e}")
    return False


if __name__ == "__main__":
    import sys

    sys.exit(0 if run() else 1)
