"""Analytic and BSpline 2D/3D contour builders for the 50%-scale Nintendo 64 enclosure.

All curves and surfaces are pure native OpenCascade/CadQuery primitives measured directly
from the 50%-scaled `Console N64` CAD (`lib/step/n64_console_raw.py` / `lib/step/n64_shell.py`).
Contains zero `.step` imports so every `lib/part/*.py` remains 100% native CadQuery.
"""

import functools
import math

import cadquery as cq
from assembly import datum as D
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCP.BRepOffsetAPI import BRepOffsetAPI_MakeOffset, BRepOffsetAPI_ThruSections
from OCP.Geom import Geom_BSplineSurface
from OCP.GeomAbs import GeomAbs_Arc
from OCP.gp import gp_Pnt
from OCP.TColgp import TColgp_Array2OfPnt
from OCP.TColStd import TColStd_Array1OfInteger, TColStd_Array1OfReal

# Exact 50%-scale 25 cooling louver slots in the parabolic saddle ramp (`Console_N64.step` 0.5x):
# 25 slots of width 1.425 mm on 2.675 mm pitch across X = [-32.8125, +32.8125], rear Y = +3.4461
TOP_LOUVER_BOXES_50: tuple[tuple[float, float, float, float], ...] = (
    (-32.8125, 2.2564, -31.3875, 3.4461),
    (-30.1375, 0.4361, -28.7125, 3.4461),
    (-27.4625, -1.1636, -26.0375, 3.4461),
    (-24.7875, -2.5621, -23.3625, 3.4461),
    (-22.1125, -3.7736, -20.6875, 3.4461),
    (-19.4375, -4.8091, -18.0125, 3.4461),
    (-16.7625, -5.6775, -15.3375, 3.4461),
    (-14.0875, -6.3863, -12.6625, 3.4461),
    (-11.4125, -6.9415, -9.9875, 3.4461),
    (-8.7375, -7.3484, -7.3125, 3.4461),
    (-6.0625, -7.6114, -4.6375, 3.4461),
    (-3.3875, -7.7340, -1.9625, 3.4461),
    (-0.7125, -7.7495, 0.7125, 3.4461),
    (1.9625, -7.7340, 3.3875, 3.4461),
    (4.6375, -7.6114, 6.0625, 3.4461),
    (7.3125, -7.3484, 8.7375, 3.4461),
    (9.9875, -6.9415, 11.4125, 3.4461),
    (12.6625, -6.3863, 14.0875, 3.4461),
    (15.3375, -5.6775, 16.7625, 3.4461),
    (18.0125, -4.8091, 19.4375, 3.4461),
    (20.6875, -3.7736, 22.1125, 3.4461),
    (23.3625, -2.5621, 24.7875, 3.4461),
    (26.0375, -1.1636, 27.4625, 3.4461),
    (28.7125, 0.4361, 30.1375, 3.4461),
    (31.3875, 2.2564, 32.8125, 3.4461),
)


def _outer_pod_tangent(cx: float, cy: float, r: float, px: float, py: float) -> tuple[float, float]:
    """Point on `+X` outer side of circle `(cx, cy, r)` whose tangent hits `(px, py)`."""
    dx = px - cx
    dy = py - cy
    dist = math.sqrt(dx * dx + dy * dy)
    alpha = math.atan2(dy, dx)
    beta = math.acos(r / dist)
    theta = alpha - beta
    return (cx + r * math.cos(theta), cy + r * math.sin(theta))


def _circle_arc_mid(
    cx: float,
    cy: float,
    r: float,
    a0_rad: float,
    a1_rad: float,
) -> tuple[float, float]:
    """Midpoint along circle `(cx, cy, r)` from angle `a0_rad` to `a1_rad`."""
    amid = 0.5 * (a0_rad + a1_rad)
    return (cx + r * math.cos(amid), cy + r * math.sin(amid))


def _offset_wire_xy(base_wire: cq.Wire, inset: float, z: float) -> cq.Wire:
    """Offset `base_wire` inward by `inset` mm and translate to height `z`."""
    if abs(inset) > 1e-6:
        mk = BRepOffsetAPI_MakeOffset()
        mk.Init(GeomAbs_Arc)
        mk.AddWire(base_wire.wrapped)
        mk.Perform(-inset)
        off_shape = cq.Shape.cast(mk.Shape())
        wires = off_shape.Wires()
        base_wire = wires[0] if len(wires) == 1 else max(wires, key=lambda w: w.Length())
    if abs(z) > 1e-9:
        base_wire = base_wire.moved(cq.Location(cq.Vector(0.0, 0.0, z)))
    return base_wire


def n64_plan_wire(inset: float = 0.0, z: float = 0.0) -> cq.Wire:
    """Closed 2D XY contour wire of the N64 console at height `z`, offset inward by `inset` mm.

    At `inset = 0.0`, spans `X in [-65.00, +65.00]` (`130.00 mm`) and `Y in [-49.94, +49.94]`
    (`99.88 mm`) matching the 50%-scaled `Console_N64.step` outer footprint:
      - Twin protruding `R = 12.50 mm` front cylindrical corner pods at `(+/-52.50, -37.44)`
      - Recessed bowed `R = 721.25 mm` front controller apron (`Y = -46.56 mm` at `X = 0`)
      - Tapered pod-to-waist flanks narrowing inward to `X = +/-60.00 mm` (`120.00 mm` waist)
      - Straight waist side walls (`Y = -12.44 .. +38.89 mm`)
      - `R = 10.00 mm` rounded rear corners + `R = 1200.75 mm` bowed rear wall (`Y = +49.94 mm`)
    """
    r_fp = D.FRONT_POD_R
    cx_fp = D.FRONT_POD_X
    cy_fp = D.FRONT_POD_Y

    # Front apron junction with the inner side of the front pods: (x = +/-42.77, y = -45.286)
    x_jun_f = 42.77
    y_jun_f = cy_fp - math.sqrt(r_fp * r_fp - (cx_fp - x_jun_f) ** 2)

    # Outer tangent from waist start (+60.00, -12.44) to front-right pod (+52.50, -37.44)
    xt_fp, yt_fp = _outer_pod_tangent(cx_fp, cy_fp, r_fp, D.WAIST_HALF_W, D.WAIST_Y0)

    ang_fr_0 = math.atan2(y_jun_f - cy_fp, x_jun_f - cx_fp)
    ang_fr_1 = math.atan2(yt_fp - cy_fp, xt_fp - cx_fp)
    mid_fr = _circle_arc_mid(cx_fp, cy_fp, r_fp, ang_fr_0, ang_fr_1)

    cx_rc = D.REAR_CORNER_X
    cy_rc = D.REAR_CORNER_Y
    r_rc = D.REAR_CORNER_R
    x_jun_r = 50.420
    y_jun_r = cy_rc + math.sqrt(r_rc * r_rc - (x_jun_r - cx_rc) ** 2)
    ang_rr_0 = 0.0
    ang_rr_1 = math.atan2(y_jun_r - cy_rc, x_jun_r - cx_rc)
    mid_rr = _circle_arc_mid(cx_rc, cy_rc, r_rc, ang_rr_0, ang_rr_1)

    ang_rl_0 = math.pi - ang_rr_1
    ang_rl_1 = math.pi
    mid_rl = _circle_arc_mid(-cx_rc, cy_rc, r_rc, ang_rl_0, ang_rl_1)

    ang_fl_0 = math.pi - ang_fr_1
    ang_fl_1 = math.pi - ang_fr_0
    if ang_fl_1 < ang_fl_0:
        ang_fl_1 += 2.0 * math.pi
    mid_fl = _circle_arc_mid(-cx_fp, cy_fp, r_fp, ang_fl_0, ang_fl_1)

    wp = (
        cq.Workplane("XY", origin=(0.0, 0.0, 0.0))
        .moveTo(-x_jun_f, y_jun_f)
        .threePointArc((0.0, D.FRONT_APRON_Y0), (x_jun_f, y_jun_f))
        .threePointArc(mid_fr, (xt_fp, yt_fp))
        .lineTo(D.WAIST_HALF_W, D.WAIST_Y0)
        .lineTo(D.WAIST_HALF_W, cy_rc)
        .threePointArc(mid_rr, (x_jun_r, y_jun_r))
        .threePointArc((0.0, D.REAR_WALL_Y1), (-x_jun_r, y_jun_r))
        .threePointArc(mid_rl, (-D.WAIST_HALF_W, cy_rc))
        .lineTo(-D.WAIST_HALF_W, D.WAIST_Y0)
        .lineTo(-xt_fp, yt_fp)
        .threePointArc(mid_fl, (-x_jun_f, y_jun_f))
        .close()
    )
    return _offset_wire_xy(wp.wire().val(), inset=inset, z=z)


def n64_plan_prism(z0: float, height: float, inset: float = 0.0) -> cq.Shape:
    """Extrude the exact 2D N64 planform wire from `z0` to `z0 + height`."""
    wire = n64_plan_wire(inset=inset, z=z0)
    face = cq.Face.cast(BRepBuilderAPI_MakeFace(wire.wrapped, True).Face())
    return cq.Solid.extrudeLinear(face, cq.Vector(0.0, 0.0, height))


def main_wing_wire(inset: float = 0.0, z: float = 0.0) -> cq.Wire:
    """8-segment `G1`-tangent 2D contour wire of the N64 upper main wing body (`X = -60..+60`).

    Measured from `Console_N64.step` (`0.5x`):
      - Straight waist side walls at `X = +/-60.00 mm` (`Y = -32.467 .. +38.888 mm`)
      - `R = 12.50 mm` front wing shoulders at `(+/-47.50, -32.467)` tangent to `R = 721.25 mm`
        front bowed wall (`Y = -46.561 mm` at `X = 0`)
      - `R = 10.00 mm` rear corners at `(+/-50.00, +38.888)` tangent to `R = 1200.75 mm` rear
        bowed wall (`Y = +49.939 mm` at `X = 0`)
    """
    xf_c = D.WING_SHOULDER_X
    yf_c = -32.4673
    rf_c = D.WING_SHOULDER_R
    xf_j = 48.3442
    yf_j = -44.9388
    af0 = math.atan2(yf_j - yf_c, xf_j - xf_c)
    af1 = 0.0
    mf_r = _circle_arc_mid(xf_c, yf_c, rf_c, af0, af1)
    mf_l = (-mf_r[0], mf_r[1])

    xr_c = D.REAR_CORNER_X
    yr_c = 38.8880
    rr_c = D.REAR_CORNER_R
    xr_j = 50.4222
    yr_j = 48.8791
    ar0 = 0.0
    ar1 = math.atan2(yr_j - yr_c, xr_j - xr_c)
    mr_r = _circle_arc_mid(xr_c, yr_c, rr_c, ar0, ar1)
    mr_l = (-mr_r[0], mr_r[1])

    wp = (
        cq.Workplane("XY", origin=(0.0, 0.0, 0.0))
        .moveTo(-xf_j, yf_j)
        .threePointArc((0.0, -46.5611), (xf_j, yf_j))
        .threePointArc(mf_r, (D.WAIST_HALF_W, yf_c))
        .lineTo(D.WAIST_HALF_W, yr_c)
        .threePointArc(mr_r, (xr_j, yr_j))
        .threePointArc((0.0, 49.9389), (-xr_j, yr_j))
        .threePointArc(mr_l, (-D.WAIST_HALF_W, yr_c))
        .lineTo(-D.WAIST_HALF_W, yf_c)
        .threePointArc(mf_l, (-xf_j, yf_j))
        .close()
    )
    return _offset_wire_xy(wp.wire().val(), inset=inset, z=z)


def main_wing_prism(z0: float, height: float, inset: float = 0.0) -> cq.Shape:
    """Extrude the 8-segment `G1`-tangent main wing planform wire from `z0` to `z0 + height`."""
    wire = main_wing_wire(inset=inset, z=z0)
    face = cq.Face.cast(BRepBuilderAPI_MakeFace(wire.wrapped, True).Face())
    return cq.Solid.extrudeLinear(face, cq.Vector(0.0, 0.0, height))


def _pod_wire_at(s: float, tx: float, ty: float, z: float) -> cq.Wire:
    """Closed 2D XY wire of the front pod lobe at blend parameters `(tx, ty)` and height `z`."""
    rp = D.FRONT_POD_R
    xp_c = s * ((1.0 - tx) * D.FRONT_POD_X + tx * 46.80)
    yp_c = (1.0 - ty) * (-37.4389) + ty * (-31.50)
    xw_f = s * (D.WAIST_HALF_W - tx * 0.80)
    yw_f = -12.4389
    xt_f, yt_f = _outer_pod_tangent(abs(xp_c), yp_c, rp, abs(xw_f), yw_f)
    xt_f *= s
    xi_p = s * ((1.0 - tx) * 42.7700 + tx * 43.50)
    yi_p = yp_c - math.sqrt(rp * rp - (abs(xp_c) - abs(xi_p)) ** 2)

    ap0 = math.atan2(yi_p - yp_c, xi_p - xp_c)
    ap1 = math.atan2(yt_f - yp_c, xt_f - xp_c)
    if s < 0.0 and ap0 < ap1:
        ap0 += 2.0 * math.pi
    mp = _circle_arc_mid(xp_c, yp_c, rp, ap0, ap1)

    wp = (
        cq.Workplane("XY", origin=(0.0, 0.0, z))
        .moveTo(s * 35.0, -35.0)
        .lineTo(xi_p, yi_p)
        .threePointArc(mp, (xt_f, yt_f))
        .lineTo(xw_f, yw_f)
        .lineTo(s * 35.0, yw_f)
        .close()
    )
    return wp.wire().val()


def front_pod_lobe(
    side: float,
    z0: float = D.SPLIT_Z,
    z_top: float = D.FRONT_POD_RIM_Z,
    dome_r: float = D.FRONT_POD_DOME_R,
) -> cq.Shape:
    """Build the left (`side = -1`) or right (`side = +1`) N64 front corner pod lobe.

    Matches `Face[58..60]` of `Console_N64.step` (`0.5x`):
      - `R = 12.50 mm` cylinder centred at `(side * 52.50, -37.439)` (`Z = 12.94 .. 17.75 mm`)
      - Tapered flank plane from `(side * 64.731, -34.859)` to `(side * 60.00, -12.439)`
      - Smooth cubic B-spline dome (`Z = 17.75 .. 22.75 mm`) blending into the main wing shoulder
    """
    s = 1.0 if side >= 0.0 else -1.0
    w0 = _pod_wire_at(s, 0.0, 0.0, z0)
    f0 = cq.Face.cast(BRepBuilderAPI_MakeFace(w0.wrapped, True).Face())
    if dome_r <= 1e-6:
        return cq.Solid.extrudeLinear(f0, cq.Vector(0.0, 0.0, z_top - z0))

    z_rim = z_top - dome_r  # 17.75 mm
    cyl_base = cq.Solid.extrudeLinear(f0, cq.Vector(0.0, 0.0, z_rim - z0))
    loft = BRepOffsetAPI_ThruSections(True, False)
    for tx, ty, z in (
        (0.00, 0.00, z_rim),
        (0.16, 0.32, z_rim + 0.474 * dome_r),
        (0.48, 0.66, z_rim + 0.850 * dome_r),
        (1.00, 1.00, z_top),
    ):
        loft.AddWire(_pod_wire_at(s, tx, ty, z).wrapped)
    loft.Build()
    return cyl_base.fuse(cq.Shape.cast(loft.Shape()))


def _make_bspline_face(
    poles_xyz: list[list[tuple[float, float, float]]],
    u_knots: list[float],
    u_mults: list[int],
    v_knots: list[float],
    v_mults: list[int],
    u_deg: int,
    v_deg: int,
) -> cq.Face:
    """Construct a `cq.Face` from a `Geom_BSplineSurface` pole grid and knot vectors."""
    nu = len(poles_xyz)
    nv = len(poles_xyz[0])
    arr = TColgp_Array2OfPnt(1, nu, 1, nv)
    for i, row in enumerate(poles_xyz, start=1):
        for j, (x, y, z) in enumerate(row, start=1):
            arr.SetValue(i, j, gp_Pnt(x, y, z))
    uk = TColStd_Array1OfReal(1, len(u_knots))
    um = TColStd_Array1OfInteger(1, len(u_mults))
    for i, (k, m) in enumerate(zip(u_knots, u_mults, strict=True), start=1):
        uk.SetValue(i, k)
        um.SetValue(i, m)
    vk = TColStd_Array1OfReal(1, len(v_knots))
    vm = TColStd_Array1OfInteger(1, len(v_mults))
    for i, (k, m) in enumerate(zip(v_knots, v_mults, strict=True), start=1):
        vk.SetValue(i, k)
        vm.SetValue(i, m)
    surf = Geom_BSplineSurface(arr, uk, vk, um, vm, u_deg, v_deg)
    return cq.Face.cast(BRepBuilderAPI_MakeFace(surf, 1e-6).Face())


@functools.lru_cache(maxsize=2)
def upper_outer_body() -> cq.Shape:
    """Authentic 50%-scale N64 upper shell exterior solid (`Z = 12.94 .. 33.50 mm`).

    Faithfully reconstructs the exterior topology of `Console_N64.step` (`0.5x`):
      1. `G1`-tangent `XZ` roof profile: `10.275 deg` sloped left/right wings (`|X| = 28.75..60`)
         meeting the `R = 161.1762 mm` convex front barrel dome (`X = -28.75..+28.75`, crest
         `Z = 33.50 mm`) at `Z = 30.915 mm`, intersected with the 8-segment `G1`-tangent main
         wing planform (`main_wing_prism`).
      2. `R = 1.00 mm` top perimeter fillet around the front barrel nose, front wing shoulders,
         and side wing rails (`Face[7..12]`).
      3. Concave rear cartridge cradle (`Face[1451]`, `Z = 27.33 mm` centreline with `R = 1.0 mm`
         rear edge roll-off) + parabolic vent saddle ramp (`Face[41]`, `Y = -8.75..+3.45 mm`).
      4. Left and right protruding `R = 12.50 mm` front corner pod lobes (`Z = 12.94..22.75 mm`)
         with `R = 5.00 mm` convex top dome fillets (`Face[28..35]`).
    """
    z0 = D.SPLIT_Z
    wp_xz = (
        cq.Workplane("XZ", origin=(0.0, -52.0, 0.0))
        .moveTo(-62.0, z0)
        .lineTo(62.0, z0)
        .lineTo(62.0, 24.8871)
        .lineTo(D.WING_INNER_X, D.WING_INNER_Z)
        .threePointArc((0.0, D.SHELL_H), (-D.WING_INNER_X, D.WING_INNER_Z))
        .lineTo(-62.0, 24.8871)
        .close()
    )
    f_xz = cq.Face.cast(BRepBuilderAPI_MakeFace(wp_xz.wire().val().wrapped, True).Face())
    roof_slab = cq.Solid.extrudeLinear(f_xz, cq.Vector(0.0, 105.0, 0.0))
    body = main_wing_prism(z0, D.SHELL_H - z0 + 2.0).intersect(roof_slab)

    # Apply the authentic R = 1.00 mm top perimeter fillet around the front nose and side wings
    mk1 = BRepFilletAPI_MakeFillet(body.wrapped)
    for e in body.Edges():
        bb = e.BoundingBox()
        if bb.zmin > 24.5 and (bb.ymax - bb.ymin > 3.0 or bb.xmax - bb.xmin > 3.0):
            if not (abs(bb.xmin + D.WING_INNER_X) < 0.2 and abs(bb.xmax + D.WING_INNER_X) < 0.2):
                if not (
                    abs(bb.xmin - D.WING_INNER_X) < 0.2 and abs(bb.xmax - D.WING_INNER_X) < 0.2
                ):
                    mk1.Add(1.0, e.wrapped)
    mk1.Build()
    body_f1 = cq.Shape.cast(mk1.Shape())

    # Concave rear cartridge cradle (Face[1451], Y = +3.4461 .. +50.4 mm):
    # Exact quadratic X profile Z(X, Y) = z0(Y) + 0.0017122 * X^2 on [-36.25, +36.25]
    def _cradle_row(y_val: float, z0_val: float) -> list[tuple[float, float, float]]:
        return [
            (-36.2500, y_val, z0_val + 2.2500),
            (-24.1667, y_val, z0_val + 0.7500),
            (0.0000, y_val, z0_val - 0.3750),
            (24.1667, y_val, z0_val + 0.7500),
            (36.2500, y_val, z0_val + 2.2500),
        ]

    cradle_poles = [
        _cradle_row(3.4461, 28.0851),
        _cradle_row(18.6107, 27.8223),
        _cradle_row(33.7754, 27.5595),
        _cradle_row(48.9400, 27.2967),
        _cradle_row(50.5000, 26.2000),
    ]
    f_cradle = _make_bspline_face(
        cradle_poles,
        [0.0, 0.92, 1.0],
        [4, 1, 4],
        [0.0, 0.5, 1.0],
        [4, 1, 4],
        3,
        3,
    )
    sol_cradle = cq.Solid.extrudeLinear(f_cradle, cq.Vector(0.0, 0.0, 12.0))

    # Parabolic vent saddle ramp (Face[41], Y = -9.50 .. +3.4461 mm):
    # Exact G1 parabolic saddle: Z(X,Y) = 28.0851 + 0.017331*dy + 0.0328*dy^2 + 0.0017122*X^2
    y_r0 = -9.5000
    y_r1 = 3.4461
    l_ramp = y_r1 - y_r0  # 12.9461 mm
    a0_r = 28.0851
    a1_l = 0.017331 * l_ramp
    a2_l2 = 0.032800 * l_ramp * l_ramp
    ramp_poles = [
        _cradle_row(y_r0, a0_r + a1_l + a2_l2),
        _cradle_row(y_r0 + l_ramp / 3.0, a0_r + (2.0 / 3.0) * a1_l + (1.0 / 3.0) * a2_l2),
        _cradle_row(y_r0 + 2.0 * l_ramp / 3.0, a0_r + (1.0 / 3.0) * a1_l),
        _cradle_row(y_r1, a0_r),
    ]
    f_ramp = _make_bspline_face(
        ramp_poles,
        [0.0, 1.0],
        [4, 4],
        [0.0, 0.5, 1.0],
        [4, 1, 4],
        3,
        3,
    )
    sol_ramp = cq.Solid.extrudeLinear(f_ramp, cq.Vector(0.0, 0.0, 12.0))

    sculpted = body_f1.cut(sol_cradle.fuse(sol_ramp))
    pod_r = front_pod_lobe(+1.0, z0=z0, z_top=D.FRONT_POD_RIM_Z, dome_r=D.FRONT_POD_DOME_R)
    pod_l = front_pod_lobe(-1.0, z0=z0, z_top=D.FRONT_POD_RIM_Z, dome_r=D.FRONT_POD_DOME_R)
    return sculpted.fuse(pod_r, pod_l)


def top_louver_prisms(z0: float = 24.0, height: float = 12.0) -> list[cq.Shape]:
    """25 vertical louver slot prisms matching `Console_N64.step` (`0.5x`)."""
    return [
        cq.Solid.makeBox(x1 - x0, y1 - y0, height, cq.Vector(x0, y0, z0))
        for (x0, y0, x1, y1) in TOP_LOUVER_BOXES_50
    ]


def cartridge_slot_throat_cutter() -> cq.Shape:
    """Authentic N64 recessed cartridge slot throat & pocket for `cartridge_flaps` (`J-09`).

    Instead of a raised ring, the real N64 has a recessed rectangular/filleted cartridge throat
    (`X = -29.25 .. +29.25 mm`, `Y = 10.94 .. 21.94 mm`) stepping down to `Z = 26.75 mm`, with a
    `57.80 x 10.30 mm` inner locating pocket (`Z = 25.35 mm` floor, `0.15 mm/side` XY clearance)
    that receives the separately-printed Light Cool Grey `part/cartridge_flaps.py` insert.
    """
    # Outer beveled cartridge throat recess stepping down to Z = 26.75 mm rim
    wp_throat = (
        cq.Workplane("XY", origin=(0.0, D.CARTRIDGE_FLAP_Y, D.CARTRIDGE_FLAP_Z))
        .rect(58.50, 11.00)
        .extrude(8.0)
    )
    throat_box = wp_throat.val()
    mk = BRepFilletAPI_MakeFillet(throat_box.wrapped)
    for e in throat_box.Edges():
        bb = e.BoundingBox()
        if bb.zmax - bb.zmin > 5.0:
            if bb.ymin < 11.5:
                mk.Add(4.5, e.wrapped)
            else:
                mk.Add(0.8, e.wrapped)
    mk.Build()
    throat = cq.Shape.cast(mk.Shape())

    # Inner locating pocket (Z = 25.35 mm floor, 0.15 mm/side XY clearance) for cartridge_flaps
    pkt_w = D.CARTRIDGE_FLAP_W + 2.0 * D.CARTRIDGE_FLAP_CLEAR
    pkt_d = D.CARTRIDGE_FLAP_D + 2.0 * D.CARTRIDGE_FLAP_CLEAR
    wp_pkt = (
        cq.Workplane("XY", origin=(0.0, D.CARTRIDGE_FLAP_Y, D.CARTRIDGE_POCKET_Z0))
        .rect(pkt_w, pkt_d)
        .extrude(9.0)
    )
    pkt_box = wp_pkt.val()
    mk_pkt = BRepFilletAPI_MakeFillet(pkt_box.wrapped)
    for e in pkt_box.Edges():
        bb = e.BoundingBox()
        if bb.zmax - bb.zmin > 5.0:
            if bb.ymin < 11.6:
                mk_pkt.Add(4.25 + D.CARTRIDGE_FLAP_CLEAR, e.wrapped)
            else:
                mk_pkt.Add(0.50 + D.CARTRIDGE_FLAP_CLEAR, e.wrapped)
    mk_pkt.Build()
    pocket = cq.Shape.cast(mk_pkt.Shape())
    return throat.fuse(pocket)


def control_well_cutter(side: float) -> cq.Shape:
    """Concave stadium thumb depression cutter (`Face[45]`, `11.00 x 22.50 mm` at `Y = -25.81`).

    Instead of a flat horizontal pit at `Z = 29.00 mm`, the real N64 `Face[45]` is a smooth
    concave dish whose outer perimeter (`|X| = 27.00 .. 38.00`, `Y = -37.06 .. -14.56`) is
    flush with the `10.275 deg` sloped wing plane and dips `1.48 mm` in the centre (`Z = 28.75`).
    """
    s = 1.0 if side >= 0.0 else -1.0
    slope = math.tan(math.radians(D.WING_SLOPE_DEG))
    ys = (-37.50, -31.65, -25.81, -19.97, -14.12)
    wy = (0.00, 0.92, 1.38, 0.92, 0.00)
    xs_abs = (26.80, 29.65, 32.50, 35.35, 38.20)
    wx = (0.00, 0.92, 1.38, 0.92, 0.00)
    if s < 0.0:
        xs = tuple(-x for x in reversed(xs_abs))
    else:
        xs = xs_abs

    poles = []
    for y_val, dy_w in zip(ys, wy, strict=True):
        row = []
        for x_val, dx_w in zip(xs, wx, strict=True):
            z_wing = D.WING_INNER_Z - (abs(x_val) - D.WING_INNER_X) * slope
            z_val = z_wing - 1.12 * dy_w * dx_w
            row.append((x_val, y_val, z_val))
        poles.append(row)

    f_dish = _make_bspline_face(
        poles,
        [0.0, 0.5, 1.0],
        [4, 1, 4],
        [0.0, 0.5, 1.0],
        [4, 1, 4],
        3,
        3,
    )
    dish_prism = cq.Solid.extrudeLinear(f_dish, cq.Vector(0.0, 0.0, 8.0))
    pill = stadium_prism(
        s * 32.50,
        D.CONTROL_WELL_Y,
        D.CONTROL_WELL_W,
        D.CONTROL_WELL_D,
        26.0,
        10.0,
    )
    return dish_prism.intersect(pill)


def stadium_prism(
    cx: float,
    cy: float,
    width_x: float,
    length_y: float,
    z0: float,
    height: float,
) -> cq.Shape:
    """Vertical stadium (pill) solid centred at `(cx, cy)` spanning `z0 .. z0 + height`."""
    r = 0.5 * min(width_x, length_y)
    if length_y >= width_x:
        dy = 0.5 * (length_y - width_x)
        if dy < 1e-5:
            return cq.Solid.makeCylinder(r, height, cq.Vector(cx, cy, z0))
        c1 = cq.Solid.makeCylinder(r, height, cq.Vector(cx, cy - dy, z0))
        c2 = cq.Solid.makeCylinder(r, height, cq.Vector(cx, cy + dy, z0))
        mid = cq.Solid.makeBox(width_x, 2.0 * dy, height, cq.Vector(cx - r, cy - dy, z0))
        return mid.fuse(c1, c2)
    dx = 0.5 * (width_x - length_y)
    c1 = cq.Solid.makeCylinder(r, height, cq.Vector(cx - dx, cy, z0))
    c2 = cq.Solid.makeCylinder(r, height, cq.Vector(cx + dx, cy, z0))
    mid = cq.Solid.makeBox(2.0 * dx, length_y, height, cq.Vector(cx - dx, cy - r, z0))
    return mid.fuse(c1, c2)


def n64_shield_wire(
    y0: float = 0.0,
    width_x: float = D.BEZEL_W,
    height_z: float = D.BEZEL_H,
    z_centre: float = D.BEZEL_Z_CENTRE,
) -> cq.Wire:
    """Closed 2D XZ wire of the N64 curved-top front jewel (`Face[1798..1806]` at `0.5x`).

    Matches `Console_N64.step`:
      - Tapered sides widening from `|X| = 10.44 mm` at `Z = 18.39 mm` up to `|X| = 12.07 mm`
        at `Z = 26.94 mm` (clearing the `|X| >= 10.80 mm` twin controller port bays below!)
      - Rounded lower corners (`R = 3.0 mm`) meeting the gently bowed bottom arc (`|X| <= 7.52`)
      - Rounded upper shoulders (`R = 3.0 mm`) meeting the domed top arch peaking at `Z = 30.50`
    """
    hw_top = 0.5 * width_x  # 12.07 mm at Z = 26.94 mm
    hw_low = hw_top - 1.63  # 10.44 mm at Z = 18.39 mm
    hw_bot_arc = hw_top - 4.55  # 7.52 mm at Z = 15.56 mm
    hw_top_arc = hw_top - 2.19  # 9.88 mm at Z = 29.88 mm
    z_bot = z_centre - 0.5 * height_z  # 15.00 mm
    z_top = z_centre + 0.5 * height_z  # 30.50 mm
    z_bot_arc = z_bot + 0.56  # 15.56 mm
    z_low_corner = z_bot + 3.39  # 18.39 mm
    z_high_shoulder = z_top - 3.56  # 26.94 mm
    z_top_arc = z_top - 0.62  # 29.88 mm

    wp = (
        cq.Workplane("XZ", origin=(0.0, y0, 0.0))
        .moveTo(-hw_bot_arc, z_bot_arc)
        .threePointArc((0.0, z_bot), (hw_bot_arc, z_bot_arc))
        .threePointArc((hw_low - 0.65, z_bot_arc + 0.95), (hw_low, z_low_corner))
        .lineTo(hw_top, z_high_shoulder)
        .threePointArc((hw_top - 0.85, z_top_arc - 0.85), (hw_top_arc, z_top_arc))
        .threePointArc((0.0, z_top), (-hw_top_arc, z_top_arc))
        .threePointArc((-hw_top + 0.85, z_top_arc - 0.85), (-hw_top, z_high_shoulder))
        .lineTo(-hw_low, z_low_corner)
        .threePointArc((-hw_low + 0.65, z_bot_arc + 0.95), (-hw_bot_arc, z_bot_arc))
        .close()
    )
    return wp.wire().val()


def n64_shield_prism(
    y0: float,
    depth_y: float,
    width_x: float = D.BEZEL_W,
    height_z: float = D.BEZEL_H,
    z_centre: float = D.BEZEL_Z_CENTRE,
    clearance: float = 0.0,
) -> cq.Shape:
    """Extrude the iconic N64 curved-top front emblem jewel along `+Y` (`y0 .. y0 + depth_y`).

    `clearance` offsets the outline outward by that much everywhere (a pocket for the jewel).
    Stretching width and height instead left the sloped sides ~0.8x the gap (PAINT_FIT, C9).
    """
    wire = n64_shield_wire(y0=y0, width_x=width_x, height_z=height_z, z_centre=z_centre)
    if clearance:
        wire = wire.offset2D(clearance, "arc")[0]
    face = cq.Face.cast(BRepBuilderAPI_MakeFace(wire.wrapped, True).Face())
    return cq.Solid.extrudeLinear(face, cq.Vector(0.0, depth_y, 0.0))


def n64_led_lens_prism(
    y0: float,
    depth_y: float,
    clearance: float = 0.0,
    z_centre: float = D.LED_PIPE_Z,
) -> cq.Shape:
    """Extrude the authentic N64 horizontal lenticular Power LED lens (`Face[1823]`, `6.36x1.76`).

    Measured from `Face[1823]` of `Console_N64.step` (`0.5x`):
      - Biconvex horizontal almond/lenticular profile (`6.36 mm` wide x `1.76 mm` tall at `X = 0`)
      - Gently arched top (`Z = 9.12 mm` at `X = 0`) and bottom (`Z = 7.36 mm` at `X = 0`) edges
      - Rounded `R = 0.35 mm` left and right tips at `X = +/-3.18 mm, Z = 8.24 mm`
    """
    hw = 0.5 * D.LED_OVAL_W  # 3.18 mm
    hh = 0.5 * D.LED_OVAL_H  # 0.88 mm
    x_tip = hw - 0.32
    z_tip = 0.35

    wp = (
        cq.Workplane("XZ", origin=(0.0, y0, 0.0))
        .moveTo(-x_tip, z_centre + z_tip)
        .threePointArc((0.0, z_centre + hh), (x_tip, z_centre + z_tip))
        .threePointArc((hw, z_centre), (x_tip, z_centre - z_tip))
        .threePointArc((0.0, z_centre - hh), (-x_tip, z_centre - z_tip))
        .threePointArc((-hw, z_centre), (-x_tip, z_centre + z_tip))
        .close()
    )
    wire = wp.wire().val()
    if clearance:  # a true offset: growing the arc points left the tips ~0.7x the gap (PAINT_FIT)
        wire = wire.offset2D(clearance, "arc")[0]
    face = cq.Face.cast(BRepBuilderAPI_MakeFace(wire.wrapped, True).Face())
    return cq.Solid.extrudeLinear(face, cq.Vector(0.0, depth_y, 0.0))
