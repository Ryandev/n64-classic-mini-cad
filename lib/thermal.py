"""Steady-state flow and heat model of the active cooling (REQ-04). Pure Python: no CAD imports.

Flow path (series): room -> top louvers -> hood -> fan -> plenum -> turning chamber -> pin fins ->
case -> exhaust (floor vents behind the feet gap || waist slots || rear slits) -> room. The fan's
operating point is where its pressure-flow line (published shut-off and free-air figures, derated
25 %: real curves sag mid-range) meets the system loss.

Grounding, strongest first:
- Heat sink: R(v) interpolated from the Same Sky datasheet's measured table (free-stream; the
  ducted sink here does better at the same approach velocity, so this is conservative).
- Pin bank loss: in-line bank, f = 0.45 per row on the gap velocity (Zukauskas in-line ~0.3,
  x1.5 for square pins), plus 1.0 entry/exit.
- Openings: sharp-edged orifices, Cd = 0.6; bends and plenums K = 1.0-1.5. Estimates: the
  on-device load test is the real check.
- Junction to sink base: 1.0 K/W budget (paste on the bare die, die spreading).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

RHO, CP = 1.16, 1007.0  # air at ~30 C
AMBIENT_C = 30.0  # a warm room
TJ_MAX_C = 105.0  # Intel N100
TJ_TARGET_C = 85.0  # 20 K below the throttle point
R_CONTACT = 1.0
DERATE = 0.75
PIN_F = 0.45
LFM = 0.00508


@dataclass(frozen=True)
class Inputs:
    """Everything the model needs; the gate fills the areas from measured geometry."""

    fan_q_max: float  # m3/s
    fan_p_max: float  # Pa
    hs_r_by_v: dict[float, float]  # m/s -> K/W (datasheet)
    hs_width: float  # mm
    hs_fin_h: float  # mm
    hs_rows: int
    hs_pin: float  # mm
    a_louver: float  # mm2, open louver area inside the hood
    a_hood: float  # mm2, narrowest hood passage to the fan
    a_turn: float  # mm2, narrowest passage plenum -> chamber -> fins
    a_floor: float  # mm2, open floor vents
    a_feet_gap: float  # mm2, perimeter x feet height
    a_side: float  # mm2, open waist slots
    a_rear: float  # mm2, open rear slits


@dataclass(frozen=True)
class Result:
    q: float  # m3/s
    dp: float  # Pa
    v_approach: float  # m/s
    r_hs: float  # K/W
    tj: float  # C
    t_exhaust: float  # C, case air leaving (what the SSD and RAM sit in)


def _orifice(q: float, a_mm2: float, cd: float = 0.6) -> float:
    return 0.5 * RHO * (q / (cd * a_mm2 * 1e-6)) ** 2


def _k(q: float, a_mm2: float, k: float) -> float:
    return k * 0.5 * RHO * (q / (a_mm2 * 1e-6)) ** 2


def pin_bank_dp(q: float, i: Inputs) -> float:
    pitch = (i.hs_width - i.hs_pin) / (i.hs_rows - 1)
    v_max = q / (i.hs_width * i.hs_fin_h * 1e-6) * pitch / (pitch - i.hs_pin)
    return (i.hs_rows * PIN_F + 1.0) * 0.5 * RHO * v_max**2


def system_dp(q: float, i: Inputs) -> float:
    floor_eq = 1.0 / math.sqrt(1.0 / i.a_floor**2 + 1.0 / i.a_feet_gap**2) if i.a_floor else 0.0
    a_exhaust = floor_eq + i.a_side + i.a_rear
    return (
        _orifice(q, i.a_louver)
        + _k(q, i.a_hood, 1.0)
        + _k(q, i.a_turn, 1.5)
        + pin_bank_dp(q, i)
        + _orifice(q, a_exhaust)
    )


def hs_resistance(v: float, table: dict[float, float]) -> float:
    (v1, r1), (v2, r2) = sorted((k, r) for k, r in table.items() if k > 0)
    r0 = table[0.0]
    if v <= 0:
        return r0
    n = math.log(r1 / r2) / math.log(v2 / v1)
    return min(r0, r1 * (v1 / v) ** n)


def operating_point(i: Inputs) -> float:
    q_free, p_shut = i.fan_q_max * DERATE, i.fan_p_max * DERATE
    lo, hi = 0.0, q_free
    for _ in range(80):
        q = (lo + hi) / 2.0
        if p_shut * (1.0 - q / q_free) > system_dp(q, i):
            lo = q
        else:
            hi = q
    return lo


def solve(i: Inputs, p_soc: float, p_other: float = 3.0) -> Result:
    """Junction temperature with fresh room air at the fan (intake through the louvers)."""
    q = operating_point(i)
    if q <= 0:
        raise ValueError("no flow: the fan cannot overcome the system at all")
    v = q / (i.hs_width * i.hs_fin_h * 1e-6)
    r = hs_resistance(v, i.hs_r_by_v)
    mean_air = AMBIENT_C + p_soc / (2.0 * RHO * CP * q)
    tj = mean_air + p_soc * (r + R_CONTACT)
    t_exhaust = AMBIENT_C + (p_soc + p_other) / (RHO * CP * q)
    return Result(q=q, dp=system_dp(q, i), v_approach=v, r_hs=r, tj=tj, t_exhaust=t_exhaust)
