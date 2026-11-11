"""Clear Cast Acrylic Front N64 Emblem Jewel (`lib/part/front_bezel.py`, `REQ-07`, `J-06`).

Cut from **`2.0 mm` Clear Cast Acrylic (PMMA)** using the Diode-Laser Plywood Jig
(`lib/part/bezel_laser_jig.py` / `export/2d/bezel_laser_jig.svg`), with a **Cricut-cut vinyl
N64 emblem decal applied to the flat rear (`+Y`) inside surface** (second-surface application)
before gluing into the flush pocket on `upper_shell` (`J-06`, `0.15 mm/side` clearance):
  - Outer contour (`24.14 x 15.50 mm` at `Z = 15.00 .. 30.50 mm`): Exact 50%-scale `Face[1799]`
    N64 front jewel contour (`C.n64_shield_prism`), tapering to `15.04 mm` at the base so it
    sits cleanly on the untouched central front apron between the twin controller bays
  - Flat rear `+Y` face (`Y = -44.56 mm`): 100% planar second-surface decal backing for a
    Cricut multi-layer vinyl N64 logo sticker + black background shield
  - Also FDM-printable (`PRINT_NORMAL = (0, 1, 0)`) and exported as 1:1 2D SVG
    (`export/2d/front_bezel.svg`) for both the Cricut vinyl cutter and acrylic template
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402
from shared import n64_contours as C  # noqa: E402

PROCESS = "fdm"
MANUFACTURE = "fdm"
MATERIAL = "2.0mm Clear Cast Acrylic + Rear Cricut Vinyl Decal"
PRINT_NORMAL = (0, 1, 0)
VISIBLE_FACES = ("-Y",)


def get_shape() -> cq.Shape:
    """Construct the 2.0 mm Clear Acrylic N64 front emblem jewel solid."""
    return C.n64_shield_prism(
        y0=D.BEZEL_Y0,
        depth_y=D.BEZEL_T,
        width_x=D.BEZEL_W,
        height_z=D.BEZEL_H,
        z_centre=D.BEZEL_Z_CENTRE,
    )
