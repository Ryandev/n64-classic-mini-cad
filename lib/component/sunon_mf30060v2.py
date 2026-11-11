"""Sunon MF30060V2-1000U-A99 30 x 30 x 6 mm 5 V fan (bought): envelope and published figures.

Distributor data (DigiKey/Future, checked 2026-11-11): 3.7 CFM free air, 0.11 inH2O shut-off,
15.7 dB(A), 7100 rpm, Vapo bearing, 2 wires, 2.5-6 V. The space also takes a 7 mm fan: Same Sky
CFM-3007CF-0110-320 (3.64 CFM, 0.21 inH2O, 32 dB(A)) for more margin at the cost of noise.
Plugs into the Radxa X4's 2-pin 5 V fan header,
which the board speed-controls. Mounted axis vertical, blowing down out of the intake hood.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402

PART = "Sunon MF30060V2-1000U-A99"
CFM_M3S = 0.000471947
INH2O_PA = 249.09
Q_MAX_M3S = 3.7 * CFM_M3S
P_MAX_PA = 0.110 * INH2O_PA
NOISE_DBA = 15.7


def placed() -> cq.Shape:
    """Fan frame with its air bore open, in console coordinates."""
    frame = cq.Solid.makeBox(D.FAN_W, D.FAN_W, D.FAN_H, cq.Vector(D.FAN_X0, D.FAN_Y0, D.FAN_Z0))
    cx, cy = D.FAN_X0 + D.FAN_W / 2.0, D.FAN_Y0 + D.FAN_W / 2.0
    bore = cq.Solid.makeCylinder(D.FAN_BORE_D / 2.0, D.FAN_H, cq.Vector(cx, cy, D.FAN_Z0))
    hub = cq.Solid.makeCylinder(D.FAN_HUB_D / 2.0, D.FAN_H, cq.Vector(cx, cy, D.FAN_Z0))
    return frame.cut(bore).fuse(hub)


def envelope() -> cq.Shape:
    """Solid 30 x 30 x 10 box: nothing else may enter the fan's swept volume."""
    return cq.Solid.makeBox(D.FAN_W, D.FAN_W, D.FAN_H, cq.Vector(D.FAN_X0, D.FAN_Y0, D.FAN_Z0))
