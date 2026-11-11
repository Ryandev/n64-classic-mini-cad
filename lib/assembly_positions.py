"""Recorded assembly placements extracted from `N64.SLDASM` and Radxa X4 vendor CAD.

Mirrors `GBA/CAD/lib/assembly_positions.py`: maps each standalone `lib/step/<name>.py`
reference part from its local Z-up origin into the 1:1 Nintendo 64 tabletop coordinate
frame (`+X` right, `+Y` rear, `-Y` front, `+Z` up, console bottom feet on `Z = 0.0 mm`).
"""

# 1:1 SolidWorks assembly placements rotated +90 deg about +X and centred on console Y/Z
ASSEMBLY_POSITIONS_1TO1: dict[str, dict[str, object]] = {
    "n64_shell": {
        "translation_mm": (0.0, 0.0, 0.0),
        "rotation_deg": (0.0, 0.0, 0.0),
        "bbox_1to1_mm": (-130.00, -99.88, 0.00, 130.00, 99.88, 67.00),
    },
    "power_slider": {
        "translation_mm": (-64.65, -58.22, 56.48),
        "rotation_deg": (0.0, 0.0, 0.0),
        "bbox_1to1_mm": (-73.53, -73.22, 56.48, -55.77, -43.22, 65.58),
    },
    "reset_button": {
        "translation_mm": (64.63, -57.76, 56.48),
        "rotation_deg": (0.0, 0.0, 0.0),
        "bbox_1to1_mm": (55.75, -72.76, 56.48, 73.50, -42.76, 62.59),
    },
    "n64_power_brick": {
        "translation_mm": (-37.5591, 84.6284, 29.0000),
        "rotation_deg": (0.0, 0.0, 0.0),
    },
    "n64_av_cable": {
        "translation_mm": (80.0000, 94.6780, 32.1250),
        "rotation_deg": (0.0, 0.0, 0.0),
    },
}

# Uniform 0.50 scale factors mapping the 1:1 GrabCAD reference (260.0 x 199.76 x 67.00 mm)
# into the 50% N64 Classic Mini envelope (130.00 x 99.88 x 33.50 mm).
REF_TO_MINI_SCALE_XYZ = (
    0.50,
    0.50,
    0.50,
)

# Bought front USB-A receptacle (`lib/step/usb_a_te_292303_7.py`, TE Connectivity 292303-7)
FRONT_USB_A_SPEC = {
    "part": "TE Connectivity 292303-7 (Farnell 1240559 / Mouser 571-292303-7)",
    "step_ymin_mm": -7.635,
    "mouth_y_mm": -42.90,
    "seat_z_mm": 9.69,
}
