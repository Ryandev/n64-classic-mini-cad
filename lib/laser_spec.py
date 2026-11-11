"""Measured laser constants for optional 3 mm cast acrylic fixtures/templates."""

SETTINGS = "80% power, 8 mm/s, 2 passes, focus set for 3mm"
KERF = 0.300
SHEET_T = 2.700


def outer(d: float) -> float:
    """Drawn size for an outer edge that must finish at `d`."""
    return d + KERF


def hole(d: float) -> float:
    """Drawn size for a hole or slot that must finish at `d`."""
    return d - KERF


def pitch(p: float) -> float:
    """Drawn spacing between adjacent cut centrelines for a finished pitch `p`."""
    return p + KERF


def layers(n: int) -> float:
    """Thickness of `n` laminated layers."""
    return n * SHEET_T


def stack(n: int, p: float) -> float:
    """What `n` pieces of finished pitch `p` read when pushed together."""
    return n * p
