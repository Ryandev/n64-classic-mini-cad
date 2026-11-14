# Manufacturing & Assembly Guide

## 1. FDM printing (Bambu Lab X2D)

All 15 printed parts are pre-oriented and packed onto a single `240.6 x 229.0 x 23.5 mm` build plate in `export/plate/print_plate.step` (or exported individually in `export/<part>/<part>.step`).

| Parameter | Structural enclosure (`lower_tub`, `upper_shell`, `usb_retainer_bracket`, `front_port_cover`) | Cosmetic caps & inserts (`power_slider`, `reset_button`, `cartridge_flaps`, `n64_port_insert`) | Optical lens (`led_light_pipe`) |
|---|---|---|---|
| **Material** | Charcoal Grey PETG Basic (`PRINTING.md`) | Light Cool Grey PETG Basic | Clear / Transparent PETG |
| **Nozzle** | `0.4 mm` | `0.4 mm` (or `0.2 mm` for crisp button text) | `0.4 mm` |
| **Layer height** | `0.16 mm` (adaptive `0.08 mm` on `upper_shell` domes) | `0.12 mm` | `0.12 mm` |
| **Wall loops** | `4` (`1.6 mm`) | `3` (`1.2 mm`) | `100%` aligned rectilinear infill |
| **Infill** | `20%` gyroid | `25%` gyroid | `100%` |
| **Print orientation** | `lower_tub`, `upper_shell`: `PRINT_NORMAL = (0, 0, 1)`; `usb_retainer_bracket`, `front_port_cover`: `PRINT_NORMAL = (0, 1, 0)` (support-free) | `PRINT_NORMAL = (0, 0, 1)` (support-free) | `PRINT_NORMAL = (0, -1, 0)` (support-free) |

**Before printing, read [`PRINTING.md`](PRINTING.md):** the printer, materials (PETG Basic for every
printed part), printing for paint, supports (PETG body, PLA interface), the fits
measured on the owner's GBA prints, and the print-test coupons (`./run coupons`).

---

## 2. Heat-set insert installation (`10x` Ruthex brass inserts total: 4 + 2 + 4)

Set at `205–215 °C` (PLA) or `235–245 °C` (PETG) using a vertical soldering-iron press with conical heat-set tips:

1. **Radxa X4 standoffs in `lower_tub` (`4x Ruthex RX-M2.5x4.0`):**
   - Printed bore: `Ø3.20 mm`, depth `4.5 mm` inside `Ø7.0 mm` standoff post (`wall = 1.90 mm`; `1.60 mm` in the top `1.0 mm`, stepped to `Ø6.4 mm` to clear Radxa's parts).
   - Set flush with the `Z = 8.20 mm` standoff top datum.
2. **2.5GbE RJ45 carrier standoffs in `lower_tub` (`2x Ruthex RX-M2.5x4.0`):**
   - Printed bore: `Ø3.20 mm` at `(43.00, 23.00)` and `(51.50, 28.50)`.
   - Set flush with the `Z = 5.60 mm` standoff top datum.
3. **Omron SS-5GL switch mounts in `lower_tub`: no inserts (C2).** Hole 2 is a `Ø3.4 mm`
   clearance hole through each tower (`X = ±33.73 mm`, `Z = 14.60 mm`); the switch screw threads
   into the switch itself (see the assembly step).
4. **Enclosure corner bosses in `upper_shell` (`4x Ruthex RX-M3x5.7`):**
   - Printed bore: `Ø4.00 mm`, depth `7.0 mm` inside `Ø8.5 mm` corner boss (`wall = 2.25 mm`).
   - Set flush with the `Z = 12.94 mm` (`SPLIT_Z`) upper-shell parting face.

---

## 3. GPIO, Power Button & Dual-Colour LED Wiring (`firmware/rp2040_reset/code.py`)

When the Radxa X4 (`RS119-D4E0` / `RS119-D8E0`, ordered **without** the pre-soldered 40-pin header) is mounted upside-down in `lower_tub`, the 40-pin GPIO through-hole pads sit along the **front (`-Y`) edge of the PCB (`Y ≈ -22 mm`)**, immediately behind the `POWER`/`RESET` microswitches and LED cradle. **Pin 1 (`3V3`)** is marked by the **square solder pad** (Pins 2–40 are round pads).

The wiring below matches the firmware's own table, `firmware/rp2040_reset/README.md` in the theme
repo, which is the source of truth: `frontend/tests/test_firmware_pins.py` holds it and `code.py` to
Radxa's X4 GPIO table. (An older version of this section had RESET on GP3, POWER on GP2 and green
on GP5; none of those reach the header. Fixed 2026-11-14 after the Gemini review.)

| Component | Terminal / Lead | Series Resistor | Radxa X4 | Signal & Function |
|---|---|---|---|---|
| **`RESET` switch** (`Omron SS-5GL`, `X = +32.32 mm`) | `NO` | — | **Header pin 5** | **`GP29`** (input, pull-up; a press sends USB HID `KEY_F13` -> `n64mini-reset`) |
| **`RESET` switch** | `COM` | — | **Header pin 6** | `GND` (leave `NC` unconnected) |
| **`POWER` switch** (`Omron SS-5GL`, `X = -32.32 mm`) | `NO` and `COM` | — | **Across the X4's own power button `K1`** | `PMC_PWRBTN_N`: wakes the N100 or asks Batocera to shut down (not a header pin: the RP2040 is off in standby) |
| **Front LED** (`Kingbright L-93WEGW`) | Pin 1, red anode | `330 Ω` | **Header pin 7** | **`GP4`**: **red in Batocera's menu** (and while USB comes up) |
| **Front LED** | Pin 2, common cathode | — | **Header pin 9** | `GND` |
| **Front LED** | Pin 3, green anode | `330 Ω` | **Header pin 29** | **`GP7`**: **green while a game runs** (the launch wrapper tells the RP2040 over USB serial) |

The RP2040 runs only while the PC is on (its power and `RUN` pin follow the N100), so there is no
standby light.

---

## 4. Top-Down Assembly Sequence (`lower_tub` -> `upper_shell`)

1. **Front Controller Ports (`lower_tub`):**
   - Press-fit `4x` `n64_port_insert` rings (`P1..P4`) and `8x` `Ø3.0 x 1.0 mm` N52 magnets into the front apron and `2x` `front_port_cover` doors; snap the cover hinge trunnions into the side walls.
   - Drop `4x TE Connectivity 292303-7` right-angle USB-A receptacles straight down (`-Z`) onto the stepped `Z = 10.80 / 9.55 mm` cradle floors so their PCB kink legs engage the `Y = -32.35 .. -30.00 mm` retention slots.
2. **Glue `2x usb_retainer_bracket` Bridges:**
   - Apply a drop of CA / epoxy to the outer, centre (`X = ±25.00 mm`), and inner USB divider walls of `lower_tub` and press the Left and Right `usb_retainer_bracket` pieces down until their `Z = 16.85 mm` bridges seat over the `4x` USB-A metal shells (`0.15 mm` top clearance) and their `Z = BUTTON_STOP_Z` stop blocks (`22.97 mm`) (`Face854` extended to `Y = -27.80 mm`) and `Ø2.80 mm` guide poles stand vertical at `(±32.32, -32.20)`.
3. **Omron SS-5GL Microswitches (`POWER` & `RESET`):**
   - Slide each `Omron SS-5GL` onto its integral `Ø2.20 mm` locating pin (Hole 1) with the hinge lever extending forward (`-Y`) over the `usb_retainer_bracket` stop block.
   - **Before the Radxa X4 goes in**, drive a `3 x 10` pan-head thread-forming screw for plastics from behind each tower, through its `Ø3.4 mm` clearance hole, into the switch's `Ø2.35 mm` Hole 2 until the switch is snug against the tower. Don't over-tighten: the screw rolls its own thread in the switch case. The USB-A socket in front of the switch leaves no room for a screw from the front (C2).
   - **Bench-test first:** drive one screw into a spare `SS-5GL`, snug it, and check the case doesn't crack and the switch still clicks cleanly. If it fails, see C2 in the release todo for the screw-as-pin fallback.
4. **Front Power LED & Light Pipe:**
   - Slide `led_light_pipe` (Clear PETG) into the `X = 0` front aperture and seat the `Kingbright L-93WEGW` 3-lead bi-colour LED (`330 Ω` resistors on Red & Green anodes) into the rear cradle.
5. **Inverted Radxa X4 + M.2 2230 SSD + RJ45 Breakout:**
   - Install the M.2 2230 NVMe SSD on the Radxa X4, solder the USB-A, RJ45, Omron (`POWER`/`RESET`), and LED leads, and fasten the inverted Radxa X4 (`4x M2.5 x 6 BHCS` at `Z = 8.20 mm`) and rear-right RJ45 breakout (`2x M2.5 x 6 BHCS` at `Z = 5.60 mm`).
5b. **Cooling (REQ-04):**
   - Clean the N100 die, spread a thin layer of non-conductive paste (no thermal pad), and set the `Same Sky HSB26-343408` on it, centred on the package.
   - **Before this, glue the `duct_floor` plate into `cooling_duct`** (any time after printing): scuff
     both faces, run 2-part epoxy round the duct's ledge, press the plate onto the ledge and let it
     cure. The bead all round seals the plenum, so the fan's air goes through the heat sink.
   - Lower the printed `cooling_duct` over it (cover onto the pin tips, skirts either side) and stick the `0.5 mm` silicone pad on the cover above the die.
   - Seat the `Sunon MF30060V2` on the duct (label down, blowing into the plenum) and plug it into the X4's 2-pin fan header.
   - Set `cooling_hood` on the fan rim and the duct, and run `1 mm` foam tape along the hood's wall tops.
   - Stick a `3M Bumpon SJ5012` over each corner screw counterbore on the underside.
6. **Seat `POWER` & `RESET` Buttons on Guide Poles:**
   - Place `power_slider` (`X = -32.32 mm`) and `reset_button` (`X = +32.32 mm`) straight down onto the `Ø2.80 mm` vertical guide poles on `usb_retainer_bracket`. The `Ø4.0 mm` blind underside holes (`BUTTON_POLE_HOLE_D`; the chimney locates the button, the pole only backstops, row `BTN_DATUM`) hold both buttons upright and oriented before the top shell is installed.
7. **Upper Shell Trim (`cartridge_flaps` & `front_bezel`):**
   - Glue `cartridge_flaps` into the top slot pocket and `front_bezel` (2.0 mm clear acrylic + rear Cricut N64 decal aligned with `bezel_laser_jig_0.svg`) into the front nose pocket of `upper_shell`.
8. **Close Enclosure:**
   - Lower `upper_shell` straight down (`-Z`) onto `lower_tub` so the `360°` guide chimneys telescope over `power_slider` and `reset_button`, and fasten from underneath with `4x M3 x 14 DIN 912` SHCS.
