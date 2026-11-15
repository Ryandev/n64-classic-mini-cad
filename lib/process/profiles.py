"""Manufacturing profiles: what a process does to a part's size, measured.

The design stays nominal: every part at true size, every fit drawn as the finished gap (owner,
2026-11-15). A profile says what one process (a material on a machine) does to that geometry, so
the allowances are added at print time and a part can change process by changing its `PROFILE`,
not its shape. Each part that is made (not bought) names its profile with `PROFILE = "<key>"`.

A profile's allowances come only from `Measurement`s of real prints. A profile with none is
declared but unproven: `profile_check.py` fails any part that uses it.

Sign convention, per side: `hole` is how much a hole's wall moves inward (a positive value means
the hole prints small); `contour` is how much an outside face moves outward (positive: the part
prints big).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Measurement:
    """One feature measured on a real print."""

    feature: str
    kind: str  # "hole" or "contour"
    drawn_mm: float  # across the feature, as drawn
    printed_mm: float  # across the feature, as printed (callipers)
    source: str  # which print, when, who measured

    @property
    def per_side(self) -> float:
        """How far each wall moved, signed by the convention in the module docstring."""
        change = (self.printed_mm - self.drawn_mm) / 2.0
        return -change if self.kind == "hole" else change


@dataclass(frozen=True)
class Profile:
    """A process: a material on a machine, with what it does to sizes."""

    key: str
    family: str  # the part's PROCESS family this profile serves ("fdm", "resin")
    machine: str
    material: str
    measurements: tuple[Measurement, ...] = ()

    def _worst(self, kind: str) -> float | None:
        values = [m.per_side for m in self.measurements if m.kind == kind]
        return max(values) if values else None

    @property
    def hole_shrink(self) -> float | None:
        """Worst measured inward move of a hole wall, per side; None if never measured."""
        return self._worst("hole")

    @property
    def contour_growth(self) -> float | None:
        """Worst measured outward move of an outside face, per side; None if never measured."""
        return self._worst("contour")

    @property
    def proven(self) -> bool:
        """Both allowances backed by at least one measured print."""
        return self.hole_shrink is not None and self.contour_growth is not None


FDM_PETG_X2D = Profile(
    key="fdm_petg_x2d",
    family="fdm",
    machine="Bambu Lab X2D, 0.4 mm nozzle, 0.20 mm layers",
    material="PETG Basic (PLA support interface where needed)",
    measurements=(
        Measurement(
            "power button's flange pocket in the shell, short side",
            "hole",
            11.44,
            11.0,
            "coupon plate 1 shell chimney, measured by the owner 2026-11-15",
        ),
        Measurement(
            "power button's base lip, short side",
            "contour",
            11.0,
            11.1,
            "coupon plate 1 power button, measured by the owner 2026-11-15",
        ),
        Measurement(
            "power button's plunger, straight sides at the base",
            "contour",
            8.5,
            8.2,
            "coupon plate 1 power button, measured by the owner 2026-11-15",
        ),
    ),
)

RESIN_MARS = Profile(
    key="resin_mars",
    family="resin",
    machine="Elegoo Mars (MSLA)",
    material="resin, to be chosen",
    # Unproven: print one resin button and measure its lip and plunger first.
)

PROFILES = {p.key: p for p in (FDM_PETG_X2D, RESIN_MARS)}
