"""Single source of truth for the N64 Classic Mini coordinate frame, scale, and datums.

Coordinate frame (`det == +1`, right-handed tabletop convention):
    +X   Right across the front of the console (-65.00 .. +65.00 mm across front pods)
    +Y   Rear into the console (-49.94 mm front pod tangent .. +49.94 mm rear bowed wall)
    +Z   Up from the desk/foot plane (0.00 mm bottom feet .. +33.50 mm centre dome crest)

All linear dimensions are in millimetres (`mm`). Angles carry a `_DEG` suffix.
Derived directly from the 50%-scaled `Console N64` CAD (`lib/step/n64_console_raw.py` /
`lib/step/n64_shell.py`), grounded in the owner's local research notes
(`docs/references/research/03-…`).
"""

# ---------------------------------------------------------------------------
# 1. Coordinate frame (right-handed: X right, Y rear, Z up -> X x Y = Z)
# ---------------------------------------------------------------------------
FRAME_BASIS = (
    (1.0, 0.0, 0.0),  # +X: right
    (0.0, 1.0, 0.0),  # +Y: rear
    (0.0, 0.0, 1.0),  # +Z: up
)


def determinant_3x3(m: tuple[tuple[float, float, float], ...]) -> float:
    """Determinant of a 3x3 basis matrix (`+1.0` for a proper rotation, `-1.0` for reflection)."""
    (a, b, c), (d, e, f), (g, h, i) = m
    return a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)


# ---------------------------------------------------------------------------
# 2. Original N64 vs 50% N64 Classic Mini outer envelope & sculpted contours (REQ-01)
# ---------------------------------------------------------------------------
N64_ORIG_W = 260.00
N64_ORIG_D = 199.76
N64_ORIG_H = 67.00

SCALE = 0.50

SHELL_W = N64_ORIG_W * SCALE  # 130.00 mm (-65.00 .. +65.00 across twin front pods)
SHELL_D = N64_ORIG_D * SCALE  # 99.88 mm  (-49.94 front pod tangent .. +49.94 rear bow)
SHELL_H = N64_ORIG_H * SCALE  # 33.50 mm  (0.00 bottom feet .. +33.50 front barrel dome crest)

# Exact 50%-scale N64 planform primitives measured from `Console_N64.step` (`0.5x`)
FRONT_POD_X = 52.50  # +/-52.50 mm cylindrical front corner pod centres
FRONT_POD_Y = -37.44  # -37.44 - 12.50 = -49.94 mm front pod tangent
FRONT_POD_R = 12.50  # 52.50 + 12.50 = 65.00 mm outer half-width
WING_SHOULDER_X = 47.50  # +/-47.50 mm upper wing front cylindrical shoulders
WING_SHOULDER_Y = -32.47  # tangent to X = +/-60.00 mm waist & R = 721.25 mm front wall
WING_SHOULDER_R = 12.50
FRONT_WALL_R = 721.25  # front bowed wall radius centred at (0.0, +674.69)
FRONT_APRON_Y0 = -46.56  # central -Y bow of the front wall at X = 0.0
WAIST_HALF_W = 60.00  # 120.00 mm main wing waist width (5.00 mm/side inset from front pods)
WAIST_Y0 = -12.44  # where outer tapered pod flank meets straight X = +/-60.00 waist
REAR_CORNER_X = 50.00
REAR_CORNER_Y = 38.89
REAR_CORNER_R = 10.00  # tangent to X = +/-60.00 waist & R = 1200.75 mm rear wall
REAR_WALL_R = 1200.75  # rear bowed wall radius centred at (0.0, -1150.81)
REAR_WALL_Y1 = 49.94  # central +Y bow of the rear I/O wall at X = 0.0
CORNER_R = FRONT_POD_R

# Exact 50%-scale N64 upper deck, front pod domes, G1 barrel dome & concave cartridge cradle
FRONT_POD_RIM_Z = 22.75  # top of R = 5.00 mm convex front-pod dome (Z = 17.75 .. 22.75 mm)
FRONT_POD_DOME_R = 5.00  # authentic R = 5.00 mm dome fillet on top of front corner pods
WING_SLOPE_DEG = 10.275  # exact 10.275 deg lateral slope of left/right N64 wing planes
WING_INNER_X = 28.75  # G1-tangent X junction between 10.275 deg wings and R = 161.18 barrel
WING_INNER_Z = 30.915  # wing/barrel Z at |X| = 28.75 mm
WING_OUTER_Z = 25.25  # wing plane Z at |X| = 60.00 mm (before R = 1.00 mm top edge fillet)
DECK_H = 29.00  # sculpted control-well floor Z at X = +/-32.32 mm (Z = 28.36 .. 29.64 mm)
DOME_W = 57.50  # X = -28.75 .. +28.75 mm central N64 front barrel dome
DOME_D = 96.50  # Y = -46.56 .. +49.94 mm central spine length
DOME_ARCH_R = 161.1762  # G1-tangent convex front barrel radius peaking at Z = 33.50 mm
CARTRIDGE_CRADLE_Z = 27.33  # centreline Z of the rear concave cartridge cradle (Face[1451])
CARTRIDGE_FLAP_Z = 26.75  # top Z of recessed dual cartridge dust flaps (Z = 25.40 .. 26.75 mm)
CARTRIDGE_FLAP_W = 57.50  # exact 50%-scale Shell[1]+Shell[2] cartridge dust flap width
CARTRIDGE_FLAP_D = 10.00  # exact 50%-scale Shell[1]+Shell[2] combined depth (Y = 11.439..21.439)
CARTRIDGE_FLAP_Y = 16.439  # Y centreline of the dual cartridge dust flaps
CARTRIDGE_FLAP_T = 1.35  # printable insert thickness (Z = 25.40 .. 26.75 mm)
CARTRIDGE_FLAP_Z0 = CARTRIDGE_FLAP_Z - CARTRIDGE_FLAP_T  # 25.40 mm
CARTRIDGE_FLAP_CLEAR = 0.15  # J-09: 0.15 mm/side XY locating clearance in upper_shell pocket
CARTRIDGE_POCKET_Z0 = 25.35  # 0.05 mm bottom glue film gap below CARTRIDGE_FLAP_Z0

# Enclosure wall & authentic N64 parting plane (J-01)
SHELL_WALL_T = 2.0  # 5 perimeters at 0.4 mm nozzle (notes/TOLERANCES.md)
FLOOR_T = 1.6  # lower tub floor thickness (Z = 0.0 .. 1.6 mm)
ROOF_T = 1.8  # upper deck & dome minimum roof thickness
SPLIT_Z = 12.94  # exact 50%-scale N64 parting plane between lower_tub and upper_shell
PARTING_GROOVE_H = 0.38  # authentic Z = 12.56 .. 12.94 mm exterior shadow-line groove
LIP_H = 1.8  # Z height of perimeter locating step lip
LIP_CLEAR = 0.15  # locating clearance per side on perimeter lip (J-01)
LIP_OUTER_INSET = 1.15  # lower_tub lip outer face inset from outer shell (1.00 skirt + 0.15 gap)
RABBET_INSET = 1.00  # upper_shell rabbet inner face inset from outer shell (1.00 mm skirt wall)
UPPER_FLANGE_W = 6.5  # internal stiffening & flat Z = SPLIT_Z bed-contact rim on upper_shell

# 4x M3 enclosure corner bosses (J-01), coaxial with front pods and rear rounded corners
CORNER_BOSS_XS = (-52.8, 52.8)
CORNER_BOSS_YS = (-37.44, 38.89)
CORNER_BOSS_OD = 8.4
M3_CLEAR_D = 3.4
M3_CBORE_D = 6.5
M3_CBORE_H = 3.5
INSERT_M3_BORE_D = 4.0
INSERT_M3_DEPTH = 5.8

# ---------------------------------------------------------------------------
# 3. Radxa X4 SBC mounting datum (REQ-03, REQ-04, J-02)
# ---------------------------------------------------------------------------
RADXA_W = 85.0
RADXA_D = 56.0
RADXA_PCB_T = 1.6
RADXA_HOLE_DX = 58.0
RADXA_HOLE_DY = 49.0
RADXA_HOLE_D = 2.7  # 4x M2.5 mounting holes

RADXA_HOLE_LEFT_MARGIN = 3.5
RADXA_HOLE_Y_MARGIN = 3.5

RADXA_X_CENTRE = -5.5  # X = -48.0 .. +37.0 mm -> clears rear-left M3 boss & opens 21mm +X RJ45 bay
RADXA_Y_CENTRE = 18.80  # Y = -9.20 .. +46.80 mm -> flush with +Y rear wall; I/O protrudes through!

RADXA_STANDOFF_H = 6.6  # clears 5.53 mm M.2 2230 NVMe + vendor STEP underside by >= 1.07 mm
RADXA_PCB_Z0 = FLOOR_T + RADXA_STANDOFF_H  # Z = 8.2 mm standoff top datum (J-02)
RADXA_PCB_Z1 = RADXA_PCB_Z0 + RADXA_PCB_T  # Z = 9.8 mm
RADXA_M2_H = 5.53  # underside M.2 2230 NVMe socket + SSD envelope (Z = 2.67 .. 8.20 mm)
RADXA_COOLER_H = 11.5  # low-profile finned heatsink + blower above PCB (Z = 9.80 .. 21.30 mm)
MIN_PLENUM_H = 8.0  # required air plenum above cooler inside the 33.5 mm dome (REQ-04)

STANDOFF_M25_OD = 7.0
INSERT_M25_BORE_D = 3.2  # Ruthex RX-M2.5x4.0 heat-set insert bore
INSERT_M25_DEPTH = 4.2


def radxa_bbox() -> dict[str, tuple[float, float]]:
    """Axis-aligned PCB span of the placed Radxa X4 in console coordinates."""
    x0 = RADXA_X_CENTRE - RADXA_W / 2.0
    x1 = RADXA_X_CENTRE + RADXA_W / 2.0
    y0 = RADXA_Y_CENTRE - RADXA_D / 2.0
    y1 = RADXA_Y_CENTRE + RADXA_D / 2.0
    return {"x": (x0, x1), "y": (y0, y1), "z": (RADXA_PCB_Z0, RADXA_PCB_Z1)}


def radxa_hole_centres() -> list[tuple[float, float]]:
    """XY coordinates of the 4 Radxa X4 M2.5 mounting holes (`58.0 x 49.0 mm` pattern)."""
    x_left = (RADXA_X_CENTRE - RADXA_W / 2.0) + RADXA_HOLE_LEFT_MARGIN
    x_right = x_left + RADXA_HOLE_DX
    y_front = (RADXA_Y_CENTRE - RADXA_D / 2.0) + RADXA_HOLE_Y_MARGIN
    y_rear = y_front + RADXA_HOLE_DY
    return [
        (x_left, y_front),
        (x_right, y_front),
        (x_left, y_rear),
        (x_right, y_rear),
    ]


# ---------------------------------------------------------------------------
# 4. Rear I/O bay datum (REQ-05, aligned to flush-rear Radxa X4 STEP connectors)
# ---------------------------------------------------------------------------
REAR_USBC_X = -36.783  # USB-C 12V PD power port (Shell[1146])
REAR_USBC_W = 9.54
REAR_USBC_H = 3.60

REAR_HDMI1_HIDDEN_X = -21.99  # Second Micro-HDMI port (hidden behind 1.69mm solid rear wall)
REAR_HDMI_X = -8.385  # Primary visible Micro-HDMI port (Solid[2])
REAR_HDMI_W = 7.10
REAR_HDMI_H = 3.30

REAR_AUDIO_X = 5.986  # 3.5mm audio jack circular barrel (Solid[3], Ø6.00 mm at Z=5.95 mm)
REAR_AUDIO_W = 6.60
REAR_AUDIO_H = 6.60

REAR_IO_Z_CENTRE = 6.55

# Rear-right panel-mount RJ45 Ethernet bay (to the +X right of the Radxa X4 PCB)
REAR_RJ45_X = 43.2
REAR_RJ45_BAY_W = 20.5
REAR_RJ45_W = 10.4
REAR_RJ45_D = 19.5
REAR_RJ45_H = 10.4
REAR_RJ45_Z_CENTRE = 7.2
RJ45_SEAT_Z = 5.60  # top of 2x Ruthex RX-M2.5x4.0 standoffs in lower_tub for RJ45 carrier ears
RJ45_MOUNT_HOLES = ((43.20, 23.00), (52.00, 28.50))  # 2x M2.5 mounting holes for RJ45 module

# ---------------------------------------------------------------------------
# 5. Twin-port front controller covers (P1+P2 left, P3+P4 right) at authentic Z = 13.19 mm
#    split line, covering 4x TE Connectivity 292303-7 USB-A ports (REQ-06, J-05, J-07, J-08)
# ---------------------------------------------------------------------------
FRONT_PORT_XS = (-32.6, -17.4, 17.4, 32.6)
PORT_INSERT_XS = (-32.34, -18.34, 18.34, 32.34)  # exact 50%-scale Console_N64.step port X centres
USB_A_W = 13.14  # TE Connectivity 292303-7 barrel width (`15.13 mm` across front EMI ground lip)
USB_A_FLANGE_W = 15.13
USB_A_D = 15.36  # TE Connectivity 292303-7 front-to-back depth (`Y = -41.70 .. -26.34 mm`)
USB_A_H = 7.76  # TE Connectivity 292303-7 height above seating plane (`+3.61 mm` pins below)
USB_A_Z_CENTRE = 13.19  # exact authentic N64 controller port Z centreline (straddles Z = 12.94)
USB_A_SEAT_Z = 9.69  # seating plane (`zmin = 6.08 mm`, `zmax = 17.45 mm`, mouth at `13.19 mm`)
USB_A_RECESS_Y = 2.62
USB_A_Y0 = -41.70  # TE 292303-7 mouth `2.62 mm` behind closed twin cover & `4.34 mm` ahead of PCB

FRONT_BAY_XS = (-25.0, 25.0)  # Left (`P1+P2`) and Right (`P3+P4`) twin-port bay centres
FRONT_BAY_X = -25.0  # Left (`P1+P2`) bay centre (`part/front_port_cover.py` canonical instance)
FRONT_BAY_W = 28.4  # X = +-10.8 .. +-39.2 mm -> keeps central 21.6 mm front apron 100% untouched!
FRONT_BAY_H = 11.4  # Z = 7.49 .. 18.89 mm centred on Z = 13.19 mm
FRONT_BAY_Y0 = -46.12  # flush with the curved N64 front wall across the twin controller bays
FRONT_COVER_CLEAR = 0.20  # J-05 XZ locating clearance per side in each twin-port bay
FRONT_COVER_T = 2.0  # nominal bay seat depth (each twin hinge cover is 1.8 mm thick)

# Bottom coaxial flip-hinge pins on each `front_port_cover` & sockets in `lower_tub` (J-05)
HINGE_PIN_D = 1.8
HINGE_SOCKET_D = 2.4  # 0.30 mm/side radial pivot clearance
HINGE_PIN_EXT = 0.8  # pin extension beyond each end of a twin-port cover
HINGE_SOCKET_DEPTH = 1.2  # blind socket depth in `lower_tub` bay cheeks
HINGE_Y = FRONT_BAY_Y0 + (FRONT_COVER_T - 0.2) - HINGE_PIN_D / 2.0  # -45.22 mm, flush on +Y bed
HINGE_Z = 8.59  # bottom pivot axis (0.90 mm above z0 = 7.69 mm bottom edge, inside lower_tub)

# Top-centre fingernail slit on each twin-port cover (-Y/+Z edge at X = +-25.0 mm)
FINGER_SLIT_W = 6.4
FINGER_SLIT_H = 0.85
FINGER_SLIT_D = 0.70

# Magnetic catch behind the twin hinged covers (2x Ø3x1 mm magnets per cover + 2x in shell = 8x)
MAGNET_D = 3.0
MAGNET_T = 1.0
MAGNET_BORE_D = 3.2
MAGNET_BORE_DEPTH = 1.15
MAGNET_XS = (-25.0, 25.0)
MAGNET_ZS = (9.9, 15.3)
MAGNET_PILLAR_W = 2.06  # central keeper bridge between the 2 USB-A windows of each twin bay

# Separately-printed shallow N64 controller port inserts glued onto twin covers (J-08)
PORT_POCKET_D = 8.2  # shallow locating pocket on -Y face of `front_port_cover`
PORT_POCKET_DEPTH = 0.45
PORT_INSERT_BOSS_D = 7.8  # 0.20 mm/side radial locating fit inside `PORT_POCKET_D`
PORT_INSERT_BOSS_H = 0.40  # 0.05 mm glue gap inside `PORT_POCKET_DEPTH`
PORT_INSERT_OD = 10.88  # exact 50%-scale `Console_N64.step` circular port bezel diameter
PORT_INSERT_BEZEL_H = 1.52  # shallow 1.52 mm front projection (y_front = -47.69 mm matching orig50)
PORT_INSERT_GAP_Y = 0.05  # nominal glue film clearance between insert and cover

# Authentic lenticular N64 front Power LED lens, Clear PETG light-pipe & wired-LED holder (J-07)
LED_PIPE_X = 0.0
LED_PIPE_Y0 = FRONT_APRON_Y0  # -46.56 mm flush at centre of untouched N64 front apron
LED_PIPE_Z = 8.24  # exact 50%-scale `Console_N64.step` (`Face[1823]`) Power LED Z centreline
LED_OVAL_W = 6.36  # authentic 6.36 x 1.76 mm horizontal lenticular/almond N64 Power LED lens
LED_OVAL_H = 1.76
LED_CLEAR = 0.10  # J-07: 0.10 mm/side perimeter clearance around lenticular lens in front wall
LED_WINDOW_D = 3.5
LED_BORE_D = 3.2
LED_SHAFT_D = 3.0  # J-07: 0.10 mm/side radial clearance datum
LED_FLANGE_W = 7.80  # rear retention collar width on Clear PETG light pipe
LED_FLANGE_D = 3.80  # vertical height of retention collar & optical barrel (Z = 6.34..10.14 mm)
LED_FLANGE_T = 1.50
LED_GUIDE_W = 5.20  # rear optical light-guide barrel width (seats into internal LED holder)
LED_GUIDE_D = 3.30  # rear optical barrel length (total light pipe depth = 7.00 mm)
LED_3MM_D = 3.00  # legacy 3 mm LED diameter datum
LED_3MM_BORE_D = 3.40  # legacy 3 mm cradle bore datum
LED_BICOLOUR_D = 10.00  # Kingbright L-819EGW (Rapid 55-0380) 10mm Red/Green bi-colour 3-lead LED
LED_BICOLOUR_BORE_D = 10.40  # 0.20 mm/side U-cradle bore in lower_tub for Kingbright L-819EGW
LED_BICOLOUR_RIM_D = 11.00  # Ø11.0 x 2.0 mm base rim on Kingbright L-819EGW
LED_LEAD_PITCH = 2.54  # 3x 0.5 mm leads on 2.54 mm pitch (Red, Common Cathode, Green)

# ---------------------------------------------------------------------------
# 6. Clear Acrylic Front N64 Jewel (+ Rear Cricut Decal) & Sculpted Top Controls
# ---------------------------------------------------------------------------
BEZEL_W = 24.14  # exact 50%-scale `Face[1799]` front jewel top width (tapers to 15.04 mm at base)
BEZEL_H = 15.50  # exact 50%-scale `Face[1799]` front jewel height (Z = 15.00 .. 30.50 mm)
BEZEL_T = 2.00  # standard 2.0 mm cast clear acrylic sheet with Cricut vinyl decal on +Y back
BEZEL_POCKET_CLEAR = 0.15  # J-06: 0.15 mm/side perimeter clearance in flush front nose pocket
BEZEL_Y0 = FRONT_APRON_Y0  # -46.56 mm flush with curved N64 front wall (zero protruding brow!)
BEZEL_Z_CENTRE = 22.75  # Z = 15.00 .. 30.50 mm on the untouched central front wall

# Exact 50%-scale N64 momentary Power Button (left wing, J-03) and Reset Button (right wing, J-04)
# Both share the exact same smooth R = 19.391 mm cylindrical-crowned stadium button profile (nub
# removed from Power) and actuate 2x Omron SS-5GL hinge-lever microswitches (shared GBA BOM).
POWER_SLIDER_X = -32.32
RESET_BTN_X = 32.32
CONTROLS_Y = -28.88  # exact 50%-scale Console_N64.step Power/Reset Y centre (Y = -36.38..-21.38)
CONTROL_WELL_Y = -25.81  # stadium thumb well Y centre (`Y = -37.06 .. -14.56 mm`, 22.50 mm long)
CONTROLS_Z = DECK_H
CONTROL_WELL_W = 11.00  # exact `Face[45]` stadium thumb depression width (`X = +-27.00 .. +-38.00`)
CONTROL_WELL_D = 22.50  # exact `Face[45]` stadium thumb depression length (`Y = -37.06 .. -14.56`)

# Momentary Power button stadium plunger (J-03, REQ-08) -- identical profile to Reset (J-04)
SLIDER_TRAVEL_Y = 0.0  # momentary vertical plunger (no longitudinal Y sliding slot)
SLIDER_TRAVEL_X = 0.0
SLIDER_CLEAR = 0.22  # J-03: 0.22 mm/side radial sliding clearance (matches GBA TOLERANCES.md §4)
SLIDER_CAP_W = 8.50
SLIDER_CAP_D = 14.50
SLIDER_NECK_W = 8.50  # stadium plunger X width matching Reset button
SLIDER_NECK_D = 14.50  # stadium plunger Y length matching Reset button
SLIDER_SLOT_W = SLIDER_NECK_W + 2.0 * SLIDER_CLEAR  # 8.94 mm stadium bore X width
SLIDER_SLOT_D = SLIDER_NECK_D + 2.0 * SLIDER_CLEAR  # 14.94 mm stadium bore Y length
SLIDER_FLANGE_W = 11.0
SLIDER_FLANGE_D = 17.2
SLIDER_FLANGE_T = 1.6
SLIDER_STROKE_Z = 1.90
SLIDER_Z0 = DECK_H - ROOF_T - SLIDER_FLANGE_T - 0.2  # Z = 25.40 mm

# Momentary Reset button stadium plunger (J-04, AC-T18)
RESET_CLEAR = 0.22  # J-04: 0.22 mm/side radial sliding clearance (matches GBA TOLERANCES.md §4)
RESET_SHAFT_W = 8.50  # stadium shaft X width matching 50% Console_N64.step Solid[0]
RESET_SHAFT_D = 14.50  # stadium shaft Y length matching 50% Console_N64.step Solid[0]
RESET_BORE_W = RESET_SHAFT_W + 2.0 * RESET_CLEAR  # 8.94 mm stadium bore X width
RESET_BORE_D = RESET_BORE_W  # radial width datum for clearance check
RESET_BORE_LEN_Y = RESET_SHAFT_D + 2.0 * RESET_CLEAR  # 14.94 mm stadium bore Y length
RESET_FLANGE_W = 11.0
RESET_FLANGE_D = 17.2
RESET_FLANGE_T = 1.6
RESET_STROKE_Z = 1.90  # 1.90 mm vertical stroke arrested by M3x6 ISO 4026 set-screw stop
RESET_Z0 = DECK_H - ROOF_T - RESET_FLANGE_T - 0.2  # Z = 25.40 mm

# 2x Omron SS-5GL subminiature hinge-lever microswitches under Power (J-03) and Reset (J-04)
OMRON_Y = (
    -24.15
)  # seated under the 14.5 mm button plungers (Y=-27.35..-20.95, clears USB-A housing)
OMRON_HOLE_Z = 14.60  # mounting-hole Z datum (body Z=11.70..21.90, lever rest Z=25.30)
OMRON_PIN_D = 2.20  # Ø2.20 mm printed locator pins in Ø2.35 mm switch holes (0.075 mm/side)
OMRON_HOLE_D = 2.35
OMRON_HOLE_PITCH = 9.50
OMRON_LEVER_RATIO = 0.72  # plunger contacts lever at r = 0.72 from hinge (X_local = +3.44 mm)
OMRON_REST_DEFLECTION = 3.20  # pre-loaded rest tip deflection -> h_rest = 13.6 - 3.2 = 10.40 mm

TACT_SWITCH_W = 19.8
TACT_SWITCH_D = 6.4
TACT_SWITCH_H = 10.2
TACT_SWITCH_Z0 = 12.10
