# Tolerances and fits

Every figure here is stated with its source (process specification or measured hardware datasheet), aligned with the reference GBA CAD project (`GBA/CAD/notes/TOLERANCES.md` & `BOM_button.md`).

---

## 1. Process capabilities

### FDM, Bambu Lab X2D / P1S, PETG & PLA (0.4 mm nozzle, 0.20 mm layer height)

    XY dimensional band     +/-0.20 mm   nominal process tolerance
    minimum local wall       0.80 mm     two perimeters at 0.4 mm nozzle
    structural shell wall    2.00 mm     five perimeters (enclosure tub & upper shell)
    unsupported overhang    50.0 deg     from vertical (`lib/printable.py`)

### Heat-set brass inserts (Ruthex — shared with GBA BOM)

    RX-M2x4.0 (Kingbright L-819EGW LED clamp; the Omron switches no longer use inserts, C2)
        thread              M2
        insert length       4.0 mm
        printed bore OD     3.2 mm       (`min boss OD 6.0 mm`)
        bore depth          >= 5.0 mm    (`4.0 mm` insert + `1.0 mm` melt relief)

    RX-M2.5x4.0 (Radxa X4 standoffs)
        thread              M2.5
        insert length       4.0 mm
        printed bore OD     3.2 mm       (`INSERT_M25_BORE_D = 3.2`, min boss OD `6.5 mm`)
        bore depth          >= 5.0 mm    (`4.0 mm` insert + `1.0 mm` melt relief)

    RX-M3x5.7 (Upper-to-Lower shell corner bosses)
        thread              M3
        insert length       5.7 mm
        printed bore OD     4.0 mm       (`INSERT_M3_BORE_D = 4.0`, min boss OD `8.0 mm`)
        bore depth          >= 6.7 mm    (`5.7 mm` insert + `1.0 mm` melt relief)

---

## 2. Fit classes (FDM PETG / PLA)

| Class | Radial clearance (per side) | Diametral clearance | Typical use in N64 Mini |
|---|---|---|---|
| **datum / butt** | `0.00 mm` nominal | `0.00 mm` | Flat Z parting faces, PCB bottom on standoff top faces |
| **press / magnet pocket** | `-0.05 .. +0.05 mm` | `0.00 .. 0.10 mm` | Neodymium magnet pockets (`Ø3.0 x 1.0 mm` in `Ø3.2 x 1.15 mm` with glue relief) |
| **switch pin locating** | `0.075 mm` | `0.15 mm` | `Ø2.20 mm` printed locator pins in `Omron SS-5GL` `Ø2.35 mm` holes (`9.50 mm` pitch) |
| **locating (split lip / pocket)** | `0.15 mm` | `0.30 mm` | Upper-to-lower shell perimeter alignment lip (`J-01`), front jewel (`J-06`), cartridge flaps (`J-09`) |
| **sliding (button plunger bore)** | `0.22 mm` | `0.44 mm` | Momentary `POWER` (`J-03`) & `RESET` (`J-04`) stadium plungers (`8.50 x 14.50 mm` in `8.94 x 14.94 mm` bores, matching GBA `TOLERANCES.md` §4 row 5) |
| **fastener clearance** | `0.20 .. 0.25 mm` | `0.40 .. 0.50 mm` | `Ø2.4 mm` bore for M2; `Ø2.9 mm` bore for M2.5; `Ø3.4 mm` bore for M3 screw |
| **free / cable & air plenum** | `>= 1.00 mm` | `>= 2.00 mm` | PCB edge to inner tub wall (`>= 2.0 mm`), heatsink intake/exhaust plenum (`>= 8.0 mm`) |

---

## 3. THE JOINT REGISTER (REQ-10)

Every mating pair names **one datum feature per axis** (`DATUM`) and the clearing features (`CLEARANCE`). Tested by `JOINT_REGISTER` in `lib/assembly/datum_check.py`.

| Joint ID | Mating pair | Axis | DATUM (holds position) | Clearing feature(s) | Nominal clearance |
|---|---|---|---|---|---|
| **J-01** | `upper_shell` to `lower_tub` enclosure split (`SPLIT_Z = 12.94 mm`) | `Z` / `XY` | **Flat `Z = 12.94 mm` perimeter step shoulder** in `Z`; **inner perimeter alignment lip** (`0.15 mm/side` locating fit) in `XY` | 4x corner `M3 x 12 DIN 912` socket cap screws through `Ø3.4 mm` lower-tub counterbores into `RX-M3x5.7` inserts (`Ø4.0 mm` bores) in upper shell | `0.00 mm` butt in `Z`; `0.15 mm/side` at lip; `0.20 mm/side` radial at M3 screws |
| **J-02** | `radxa_x4` (`85.0 x 56.0 mm` PCB, `58.0 x 49.0 mm` hole pattern) to `lower_tub` standoffs | `Z` / `XY` | **4x coplanar standoff top faces at `Z = 8.20 mm`** (`1.60 mm` floor + `6.60 mm` standoff post) in `Z`; **front-left `M2.5` standoff (`Ø2.7 mm` PCB hole on M2.5 screw)** in `XY` | 3x remaining `M2.5 x 6` screws into `RX-M2.5x4.0` brass inserts (`Ø3.2 mm` bores in `Ø7.0 mm` posts, stepped to a `Ø6.4 mm` contact face for the top `1.0 mm` to clear Radxa's parts round the holes); `>= 2.0 mm` perimeter gap from PCB edges to side/front tub walls | `0.00 mm` butt in `Z`; `0.10 mm/side` radial at M2.5 screws; `>= 2.0 mm` PCB-to-wall |
| **J-03** | `power_slider` (`Light Cool Grey` momentary `POWER` stadium plunger, transverse nub removed to match `RESET` profile) to `upper_shell` chimney, `usb_retainer_bracket` pole/stop & left `Omron SS-5GL` (`REQ-08`) | `XY` / `Z` (stroke) | **Upper shell stadium guide chimney (`11.44 x 17.64 mm`)** in `XY` (the one XY datum, rule 3; the `Ø2.80 mm` guide pole sits in a `Ø4.0 mm` hole that clears the `0.57 mm` stack and only backstops, `BTN_DATUM`); **underside stadium up-stop flange (`Z = 25.40 mm`)** at rest and **front (`usb_retainer_bracket`) + rear (`lower_tub`) hard travel stops at `BUTTON_STOP_Z`** (`2.10 mm` stroke) in `Z` | `0.22 mm/side` radial sliding clearance (`0.20 mm/side` on `Ø2.80 mm` guide pole); pre-loaded `Omron SS-5GL` lever at `r = 0.72` | `0.22 mm/side` radial; `1.90 mm` stroke (`clicks at 0.58..1.73 mm`) |
| **J-04** | `reset_button` (`Light Cool Grey` momentary `RESET` stadium plunger) to `upper_shell` chimney, `usb_retainer_bracket` pole/stop & right `Omron SS-5GL` (`AC-T18`) | `XY` / `Z` (stroke) | **Upper shell stadium guide chimney (`11.44 x 17.64 mm`)** in `XY` (the one XY datum, rule 3; the `Ø2.80 mm` guide pole sits in a `Ø4.0 mm` hole that clears the `0.57 mm` stack and only backstops, `BTN_DATUM`); **underside stadium up-stop flange (`Z = 25.40 mm`)** at rest and **front (`usb_retainer_bracket`) + rear (`lower_tub`) hard travel stops at `BUTTON_STOP_Z`** (`2.10 mm` stroke) in `Z` | `0.22 mm/side` radial sliding clearance (`0.20 mm/side` on `Ø2.80 mm` guide pole); pre-loaded `Omron SS-5GL` lever at `r = 0.72` | `0.22 mm/side` radial; `1.90 mm` stroke (`clicks at 0.58..1.73 mm`) |
| **J-05** | `front_port_cover` (`2x` twin-port hinged doors: `P1+P2` left, `P3+P4` right) & `usb_retainer_bracket` (`2x`) to `lower_tub` / `upper_shell` front USB bays | `Y` (stop) / `XZ` (hinge pivot & bay) | **Coaxial bottom pivot pins (`Ø1.8 mm` in `Ø2.4 mm` sockets at `Z = 6.09 mm`, `2.5 mm` below the port-centred bay so the glued port bezels swing out past the case front: `0.55 mm` clear when open flat)**, **keeper bridges (`Y = -44.12 mm`, `4x Ø3.0 x 1.0 mm` N52 magnets on covers + `4x` in shell)**, and **stepped `Z = 10.80 / 9.55 mm` floor + `Z = 16.85 mm` glued top retainer bridge** locking all 4 `TE Connectivity 292303-7` `USB-A` receptacles in 6-DOF | Top fingernail slits (`6.4 x 0.85 mm`); 4x `TE Connectivity 292303-7` horizontal `USB-A` receptacles recessed `2.62 mm` behind closed covers | `0.30 mm/side` radial at pivot; `0.20 mm/side` in `XZ` bay; `0.15 mm` USB-A top bridge clearance |
| **J-06** | `front_bezel` (`Clear Cast Acrylic` curved-top N64 shield emblem + rear Cricut decal) to `upper_shell` front nose pocket | `Y` (depth) / `XZ` (pocket) | **Pocket back floor** in `Y`; **shield pocket side/bottom/arch walls** in `XZ` | `0.15 mm/side` perimeter locating clearance (`24.44 x 15.80 mm` shield pocket around `24.14 x 15.50 x 2.00 mm` shield bezel) | `0.00 mm` butt on floor; `0.15 mm/side` perimeter clearance |
| **J-07** | `led_light_pipe` (`Clear PETG` `6.36 x 1.76 mm` N64 lenticular front lens) & `Kingbright L-819EGW` (`3-lead Red/Green bi-colour LED`) to `lower_tub` front apron & cradle | `XZ` (bore) / `Y` (depth) | **Lenticular front apron aperture (`6.56 x 1.96 mm`)** in `XZ`; **internal collar step (`Y = -44.26 mm`) & `Ø3.40 mm` coaxial LED collimator cradle** in `Y` | `0.10 mm/side` perimeter clearance around lenticular lens; `0.26 mm` axial optical gap to `Kingbright L-819EGW` (`Red = Power/Standby`, `Green = ON`) | `0.10 mm/side` radial in lens bore; `0.26 mm` optical gap to bi-colour LED |
| **J-08** | `n64_port_insert` (`4x` separately-printed shallow `Ø10.88 mm` N64 controller port replicas, `1.92 mm` deep) to `front_port_cover` locating pockets | `Y` (glue seat) / `XZ` (circular boss) | **`Ø8.2 x 0.45 mm` circular front pocket** receiving **`Ø7.8 x 0.40 mm` rear locating boss** in `XZ`; **flange back face** in `Y` | `0.20 mm/side` radial locating clearance; `0.05 mm` adhesive film gap | `0.05 mm` glue film in `Y`; `0.20 mm/side` radial in pocket |
| **J-09** | `cartridge_flaps` (separately-printed `Light Cool Grey` `57.50 x 10.00 x 1.35 mm` dual cartridge dust-flap insert) to `upper_shell` cartridge throat pocket | `Z` (glue seat) / `XY` (filleted pocket) | **`Z = 25.35 mm` pocket floor** in `Z`; **`57.80 x 10.30 mm` filleted throat pocket walls** (`R = 4.40 mm` front, `R = 0.65 mm` rear) in `XY` | `0.15 mm/side` perimeter locating clearance; `0.05 mm` bottom adhesive film gap (`Z = 25.35 .. 25.40 mm`) | `0.05 mm` glue film in `Z`; `0.15 mm/side` perimeter in `XY` |

---

## 4. Momentary `POWER` (`J-03`) & `RESET` (`J-04`) Activation Tolerance Budget (`Omron SS-5GL`)

Adapted from `GBA/CAD/notes/TOLERANCES.md` §5 and `BOM_button.md`, verified mechanically by `OMRON_ACT` in `lib/subassembly/top_controls_check.py`:

### 4.1 `Omron SS-5GL` Datasheet Figures (from mounting-hole centreline `z = 0`)
- **Mounting holes:** `2x Ø2.35 mm` at `9.50 mm` pitch (`2.90 mm` above switch body bottom; body top is at `+7.30 mm`, pin plunger top is at `+8.50 mm`).
- **Free Position (`FP_max`):** `+13.60 mm` at lever tip (`X_local = +7.50 mm`, hinge pivot at `X_local = -7.00 mm`, total lever length `L = 14.50 mm`).
- **Operating Position (`OP`):** `+8.80 +/- 0.80 mm` (`+8.00 .. +9.60 mm` at lever tip; `1.60 mm` total factory tolerance band).
- **Overtravel (`OVERTRAVEL_MIN`):** `1.20 mm` minimum safe travel past `OP` (`h_min_safe = OP_min - OVERTRAVEL_MIN = 8.00 - 1.20 = +6.80 mm` at lever tip).
- **Movement Differential (`MD_max`):** `0.80 mm` maximum release travel hysteresis.
- **Operating / Release Force:** `OF_max = 0.49 N` (`50 gf`), `RF_min = 0.06 N` (`6 gf`).

### 4.2 Switch actuation: what presses the lever, and how far (C3)

Omron SS-5GL (hinge lever), from Omron's SS-series datasheet, all measured at the lever tip above
the mounting holes: operating position (click) `OP = 8.8 ± 0.8 mm`, free position `FP ≤ 13.6 mm`,
release hysteresis `MD ≤ 0.8 mm`, overtravel `OT ≥ 1.2 mm`.

1. **What presses the lever.** A flat button underside meets the lever's raised tip (a 1:1 press,
   4 mm off the button's centre), and with the old 1.9 mm travel a nominal switch never clicked.
   Each button's underside is now `0.33 mm` lower, with pockets over the lever either side of a
   `1.2 mm` ridge under the button centre, `72 %` of the way from the hinge (`lever_pockets()` in
   `component/omron_ss5gl.py`). Only the ridge touches the lever, so the button moves `0.72 mm`
   per `1 mm` at the tip, and pushes on its centre.
2. **Travel.** `RESET_STROKE_Z = 2.10 mm` to the bracket shelf and tub post stops
   (`BUTTON_STOP_Z`); POWER shares it.
3. **Measured, not computed (`OMRON_ACT`).** The check moves each real button down the real lever
   and finds where the tip sits: `10.66 mm` at rest (released for every switch: `≥ 9.6 + 0.8`,
   margin `0.26`) and `7.82 mm` at the stop (clicks every switch: `≤ 8.0`, margin `0.18`).
4. **Known limit.** The `1.6 mm` spread of `OP` is wider than the `1.2 mm` guaranteed overtravel,
   so no fixed stop clicks every switch *and* keeps every switch within its guaranteed overtravel:
   an earliest-clicking switch (`OP 9.6`) is pressed `1.78 mm` past its click point, `0.58 mm`
   beyond the guarantee, taken by the steel lever flexing. Test with real switches.
