"""Right (`P3+P4 / Reset`) Removable Front Control & I/O Carrier (`front_io_carrier_r.py`).

Mirror counterpart (`side_sign = +1.0`, `X = +25.0 mm`) to `part/front_io_carrier_l.py`.
Printed upright (`PRINT_NORMAL = (0, 0, 1)`, zero support) on its flat `Z = 2.80 mm` bottom plane
and bolted to `lower_tub`'s 3 right-hand `RX-M2.5x4.0` floor bosses (`(+43.80, -32.20)`,
`(+6.40, -30.20)`, `(+25.00, -15.50)`).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from part import front_io_carrier_l  # noqa: E402

PROCESS = "fdm"
MANUFACTURE = "fdm"
PROFILE = "fdm_petg_x2d"
PRINT_NORMAL = (0, 0, 1)
VISIBLE_FACES = ()


def get_shape() -> cq.Shape:
    """Return the Right (`P3+P4 / Reset`, `X = +25.0 mm`) Front Control & I/O Carrier solid."""
    return front_io_carrier_l.carrier_at(+1.0)
