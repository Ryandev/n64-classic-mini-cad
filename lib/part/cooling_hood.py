"""Printed intake hood (REQ-04): seals the 25 top louvers to the fan's intake.

Plan outline = louver field (rect A) joined to the fan top (rect B). Over the fan the walls stand
on the fan frame's rim; elsewhere a floor plate closes the hood off from the case. Wall tops follow
the roof underside (ray-cast against the upper shell variant) less `HOOD_ROOF_GAP`, closed with
foam tape when the shell goes on. Print floor-down in PETG or ASA.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402
from OCP.gp import gp_Dir, gp_Lin, gp_Pnt  # noqa: E402
from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector  # noqa: E402
from part.shared import n64_contours as C  # noqa: E402

PROCESS = "fdm"
MANUFACTURE = "fdm"
PRINT_NORMAL = (0, 0, -1)  # floor plate on the bed
VISIBLE_FACES: tuple[str, ...] = ()

MARGIN = 1.0  # louver field to inner wall face
STEP = 2.0  # wall segment length when following the roof
_LOUVERS = C.TOP_LOUVER_BOXES_50
A_X0 = min(b[0] for b in _LOUVERS) - MARGIN
A_X1 = max(b[2] for b in _LOUVERS) + MARGIN
A_Y0 = min(b[1] for b in _LOUVERS) - MARGIN
A_Y1 = max(b[3] for b in _LOUVERS) + MARGIN
B_X0, B_X1 = D.FAN_X0, D.FAN_X0 + D.FAN_W  # walls stand on the fan rim, inside its footprint
B_Y0, B_Y1 = D.FAN_Y0, D.FAN_Y0 + D.FAN_W
RIM = 0.9  # wall thickness on the fan rim (the 28 mm bore leaves a 1 mm rim mid-side)
Z_FLOOR0 = D.HS_Z1 + D.DUCT_COVER_T + 0.15  # clears the duct cover
Z_FLOOR1 = Z_FLOOR0 + D.DUCT_WALL
Z_FAN_TOP = D.FAN_Z0 + D.FAN_H

_roof_cache: dict[tuple[float, float], float] = {}
_intersector: IntCurvesFace_ShapeIntersector | None = None


def _roof_intersector() -> IntCurvesFace_ShapeIntersector:
    """Ray intersector over the upper shell variant, built once."""
    global _intersector
    if _intersector is None:
        from variant import upper_shell

        _intersector = IntCurvesFace_ShapeIntersector()
        _intersector.Load(upper_shell.get_shape().wrapped, 1e-4)
    return _intersector


_shape_cache: cq.Shape | None = None


def roof_z(x: float, y: float) -> float:
    """Roof underside above (x, y): first upper-shell hit going up from the hood floor."""
    key = (round(x, 2), round(y, 2))
    if key not in _roof_cache:
        it = _roof_intersector()
        it.Perform(gp_Lin(gp_Pnt(x, y, Z_FLOOR1), gp_Dir(0, 0, 1)), 0.0, 40.0)
        zs = [it.Pnt(i).Z() for i in range(1, it.NbPnt() + 1)]
        if not zs:
            raise ValueError(f"no roof above ({x:.2f}, {y:.2f}): hood outline left the shell")
        _roof_cache[key] = min(zs)
    return _roof_cache[key]


def _wall(x0: float, y0: float, x1: float, y1: float, z0: float) -> list[cq.Solid]:
    """Axis-aligned wall from (x0,y0) to (x1,y1) (footprint already thickened), roof-following."""
    along_x = (x1 - x0) >= (y1 - y0)
    length = (x1 - x0) if along_x else (y1 - y0)
    n = max(1, round(length / STEP))
    segs = []
    for i in range(n):
        if along_x:
            sx0, sx1, sy0, sy1 = x0 + i * length / n, x0 + (i + 1) * length / n, y0, y1
        else:
            sx0, sx1, sy0, sy1 = x0, x1, y0 + i * length / n, y0 + (i + 1) * length / n
        top = min(roof_z(px, py) for px in (sx0, sx1) for py in (sy0, sy1)) - D.HOOD_ROOF_GAP
        segs.append(cq.Solid.makeBox(sx1 - sx0, sy1 - sy0, top - z0, cq.Vector(sx0, sy0, z0)))
    return segs


def get_shape() -> cq.Shape:
    """The hood in console coordinates."""
    global _shape_cache
    if _shape_cache is not None:
        return _shape_cache
    w = D.DUCT_WALL
    solids: list[cq.Solid] = []
    # Floor plate over rect A, minus the fan's footprint (the fan rises through it).
    floor = cq.Solid.makeBox(
        A_X1 - A_X0 + 2 * w, A_Y1 - A_Y0 + 2 * w, w, cq.Vector(A_X0 - w, A_Y0 - w, Z_FLOOR0)
    )
    floor = floor.cut(
        cq.Solid.makeBox(
            D.FAN_W + 0.4, D.FAN_W + 0.4, w + 0.2, cq.Vector(B_X0 - 0.2, B_Y0 - 0.2, Z_FLOOR0 - 0.1)
        )
    )
    solids.append(floor)
    # Rect A walls (rear, sides, and the front segments either side of the fan).
    solids += _wall(A_X0 - w, A_Y1, A_X1 + w, A_Y1 + w, Z_FLOOR1)
    solids += _wall(A_X0 - w, A_Y0 - w, A_X0, A_Y1, Z_FLOOR1)
    solids += _wall(A_X1, A_Y0 - w, A_X1 + w, A_Y1, Z_FLOOR1)
    solids += _wall(A_X0 - w, A_Y0 - w, B_X0 - 0.2, A_Y0, Z_FLOOR1)
    solids += _wall(B_X1 + 0.2, A_Y0 - w, A_X1 + w, A_Y0, Z_FLOOR1)
    # Rect B walls on the fan rim (front and the two sides up to rect A).
    solids += _wall(B_X0, B_Y0, B_X1, B_Y0 + RIM, Z_FAN_TOP)
    solids += _wall(B_X0, B_Y0, B_X0 + RIM, A_Y0 - w, Z_FAN_TOP)
    solids += _wall(B_X1 - RIM, B_Y0, B_X1, A_Y0 - w, Z_FAN_TOP)
    # Below the fan top, the fan's own side faces close the gap between rect A's front wall
    # segments and the rim walls; above it, these bridges join the two into one part.
    for xa, xb in ((B_X0 - 0.2, B_X0 + RIM), (B_X1 - RIM, B_X1 + 0.2)):
        solids += _wall(xa, A_Y0 - w, xb, A_Y0, Z_FAN_TOP)
    _shape_cache = solids[0].fuse(*solids[1:]).clean()
    return _shape_cache
