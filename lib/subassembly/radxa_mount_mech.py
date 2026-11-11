"""Radxa X4 & I/O Mounting Subassembly inside the N64 Classic Mini Lower Tub.

Pairs with `lib/subassembly/radxa_mount_check.py`.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from component import radxa_x4  # noqa: E402
from variant import lower_tub  # noqa: E402


def get_shape() -> cq.Shape:
    """Return the compound of the lower tub and all mounted internal electronics."""
    return cq.Compound.makeCompound(
        [
            lower_tub.get_shape(),
            radxa_x4.get_shape(),
        ]
    )
