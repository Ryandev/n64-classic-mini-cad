"""Measured 50%-scale cross-section profiles and feature envelopes from `Console_N64.step`.

Extracted from the downloaded `Console N64` SolidWorks assembly (`lib/step/n64_console_raw.py`,
`260.00 x 199.76 x 67.00 mm` at 1:1 scale) scaled uniformly by `SCALE = 0.50` into the N64
Classic Mini console frame:
    +X  Right (-65.00 .. +65.00 mm)
    +Y  Rear  (-49.94 mm front pod tangent .. +49.94 mm rear bowed wall)
    +Z  Up    (0.00 mm bottom foot plane .. +33.50 mm top of centre barrel dome)
"""

# 1. Outer bounding spans measured directly from `Console_N64.step` at 50% scale (mm)
SCAN_SPANS_50_MM: dict[str, tuple[float, float, float]] = {
    "Top.stl": (130.00, 99.88, 20.56),
    "Bottom.stl": (130.00, 99.88, 12.94),
    "PowerSwitch.stl": (8.75, 15.00, 4.55),
    "ResetButton.stl": (8.75, 15.00, 3.06),
    "CartMount.stl": (58.50, 11.00, 3.80),
    "Foot.stl": (25.00, 25.00, 0.90),
    "AV port.stl": (11.75, 8.00, 6.25),
}

# 2. Plan-view half-width profile (y_mm, half_width_x_mm) at 50% scale
TOP_PLAN_HALF_WIDTH_50: tuple[tuple[float, float], ...] = (
    (-46.5, 48.34),
    (-40.0, 64.70),
    (-37.44, 65.00),
    (-34.86, 64.73),
    (-25.0, 62.63),
    (-12.44, 60.00),
    (0.0, 60.00),
    (10.0, 60.00),
    (20.0, 60.00),
    (30.0, 60.00),
    (38.89, 60.00),
    (45.0, 57.92),
    (48.88, 50.42),
)

# 3. Longitudinal elevation profile (y_mm, z_dome_console_mm, z_wing_console_mm) at 50% scale
TOP_ELEVATION_PROFILE_50: tuple[tuple[float, float, float], ...] = (
    (-46.56, 32.50, 22.75),
    (-40.0, 33.50, 22.75),
    (-35.0, 33.50, 29.50),
    (-25.0, 33.50, 29.50),
    (-15.0, 33.50, 29.50),
    (-8.75, 33.50, 29.50),
    (-3.0, 30.20, 29.50),
    (3.45, 27.33, 29.50),
    (16.44, 26.75, 29.50),
    (28.0, 27.33, 29.50),
    (40.0, 27.33, 29.50),
    (48.0, 27.33, 29.00),
)

# 4. Top-deck openings measured from `Console_N64.step` at 50% scale (console XY coordinates, mm)
CARTRIDGE_SLOT_OPENING_50 = {
    "x_centre": 0.0,
    "y_centre": 16.44,
    "width_x": 58.50,  # X = -29.25 .. +29.25 mm
    "depth_y": 11.00,  # Y = +10.94 .. +21.94 mm
}

EXPANSION_PAK_OPENING_50 = {
    "x_centre": 0.0,
    "y_centre": -28.06,
    "width_x": 29.25,  # X = -14.625 .. +14.625 mm
    "depth_y": 20.25,  # Y = -38.189 .. -17.939 mm
}

POWER_SWITCH_RECESS_50 = {
    "x_centre": -32.32,
    "y_centre": -25.81,
    "width_x": 11.00,  # X = -38.00 .. -27.00 mm stadium well
    "depth_y": 22.50,  # Y = -37.06 .. -14.56 mm
}

RESET_BUTTON_RECESS_50 = {
    "x_centre": 32.32,
    "y_centre": -25.81,
    "width_x": 11.00,  # X = +27.00 .. +38.00 mm stadium well
    "depth_y": 22.50,  # Y = -37.06 .. -14.56 mm
}
