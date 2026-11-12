# Manufacturing & Assembly Guide

## 1. FDM printing (Bambu Lab X2D / P1S)

All 15 printed parts are pre-oriented and packed onto a single `240.6 x 229.0 x 23.5 mm` build plate in `export/plate/print_plate.step` (or exported individually in `export/<part>/<part>.step`).

| Parameter | Structural enclosure (`lower_tub`, `upper_shell`, `usb_retainer_bracket`, `front_port_cover`) | Cosmetic caps & inserts (`power_slider`, `reset_button`, `cartridge_flaps`, `n64_port_insert`) | Optical lens (`led_light_pipe`) |
|---|---|---|---|
| **Material** | Charcoal Grey PETG or Matte Charcoal PLA | Light Cool Grey PLA or PETG | Clear / Transparent PETG |
| **Nozzle** | `0.4 mm` | `0.4 mm` (or `0.2 mm` for crisp button text) | `0.4 mm` |
| **Layer height** | `0.16 mm` (adaptive `0.08 mm` on `upper_shell` domes) | `0.12 mm` | `0.12 mm` |
| **Wall loops** | `4` (`1.6 mm`) | `3` (`1.2 mm`) | `100%` aligned rectilinear infill |
| **Infill** | `20%` gyroid | `25%` gyroid | `100%` |
| **Print orientation** | `lower_tub`, `upper_shell`: `PRINT_NORMAL = (0, 0, 1)`; `usb_retainer_bracket`, `front_port_cover`: `PRINT_NORMAL = (0, 1, 0)` (support-free) | `PRINT_NORMAL = (0, 0, 1)` (support-free) | `PRINT_NORMAL = (0, -1, 0)` (support-free) |

---

## 2. Heat-set insert installation (`12x` Ruthex brass inserts total)

Set at `205–215 °C` (PLA) or `235–245 °C` (PETG) using a vertical soldering-iron press with conical heat-set tips:

1. **Radxa X4 standoffs in `lower_tub` (`4x Ruthex RX-M2.5x4.0`):**
   - Printed bore: `Ø3.20 mm`, depth `4.5 mm` inside `Ø7.0 mm` standoff post (`wall = 1.90 mm`; `1.60 mm` in the top `1.0 mm`, stepped to `Ø6.4 mm` to clear Radxa's parts).
   - Set flush with the `Z = 8.20 mm` standoff top datum.
2. **2.5GbE RJ45 carrier standoffs in `lower_tub` (`2x Ruthex RX-M2.5x4.0`):**
   - Printed bore: `Ø3.20 mm` at `(43.00, 23.00)` and `(51.50, 28.50)`.
   - Set flush with the `Z = 5.60 mm` standoff top datum.
3. **Omron SS-5GL switch mounts in `lower_tub` (`2x Ruthex RX-M2x4.0`):**
   - Printed bore: `Ø3.20 mm`, depth `4.8 mm` in rear Hole 2 (`Y = -16.95 mm`, `X = ±32.32 mm`).
   - Set flush with the vertical switch-mounting cheek face.
4. **Enclosure corner bosses in `upper_shell` (`4x Ruthex RX-M3x5.7`):**
   - Printed bore: `Ø4.00 mm`, depth `7.0 mm` inside `Ø8.5 mm` corner boss (`wall = 2.25 mm`).
   - Set flush with the `Z = 16.00 mm` upper-shell parting face.

---

## 3. GPIO, Power Button & Dual-Colour LED Wiring (`firmware/rp2040_reset/code.py`)

When the Radxa X4 (`RS119-D4E0` / `RS119-D8E0`, ordered **without** the pre-soldered 40-pin header) is mounted upside-down in `lower_tub`, the 40-pin GPIO through-hole pads sit along the **front (`-Y`) edge of the PCB (`Y ≈ -22 mm`)**, immediately behind the `POWER`/`RESET` microswitches and LED cradle. **Pin 1 (`3V3`)** is marked by the **square solder pad** (Pins 2–40 are round pads).

| Component | Terminal / Lead | Series Resistor | Radxa X4 Solder Pad | Signal & Function (`firmware/rp2040_reset/code.py`) |
|---|---|---|---|---|
| **`RESET` Switch** (`Omron SS-5GL`, right `X = +32.32 mm`) | **`NO`** (Middle terminal) | — | **40-pin Header Pin 5** | **`GP3`** (`INPUT` + internal `Pull.UP`; active-LOW press sends USB HID `KEY_F13` -> `n64mini-reset`) |
| **`RESET` Switch** (`Omron SS-5GL`, right `X = +32.32 mm`) | **`COM`** (Bottom hinge terminal) | — | **40-pin Header Pin 6** | **`GND`** *(leave top `NC` terminal unconnected)* |
| **`POWER` Switch** (`Omron SS-5GL`, left `X = -32.32 mm`) | **`NO`** (Middle terminal) | — | **Onboard `PWR` button signal pad** *(or + Header Pin 3 `GP2`)* | **`PWR_BTN_N`** (wakes Intel N100 from `S5` standby or triggers clean ACPI shutdown) |
| **`POWER` Switch** (`Omron SS-5GL`, left `X = -32.32 mm`) | **`COM`** (Bottom hinge terminal) | — | **40-pin Header Pin 14** *(or `PWR` button `GND` pad)* | **`GND`** *(leave top `NC` terminal unconnected)* |
| **Front Status LED** (`Kingbright L-93WEGW`, `X = 0`) | **Pin 1 — Red Anode** (`625 nm`, flat side) | **`330 Ω` 0.25W** | **40-pin Header Pin 7** | **`GP4`** (`HIGH` in `S5` standby when USB-C power is connected -> **Red**) |
| **Front Status LED** (`Kingbright L-93WEGW`, `X = 0`) | **Pin 2 — Common Cathode** (centre longest lead) | — | **40-pin Header Pin 9** | **`GND`** |
| **Front Status LED** (`Kingbright L-93WEGW`, `X = 0`) | **Pin 3 — Green Anode** (`565 nm`) | **`330 Ω` 0.25W** | **40-pin Header Pin 29** | **`GP5`** (`HIGH` when Intel N100 USB host is active in `S0` -> **Green**) |

---

## 4. Top-Down Assembly Sequence (`lower_tub` -> `upper_shell`)

1. **Front Controller Ports (`lower_tub`):**
   - Press-fit `4x` `n64_port_insert` rings (`P1..P4`) and `8x` `Ø3.0 x 1.0 mm` N52 magnets into the front apron and `2x` `front_port_cover` doors; snap the cover hinge trunnions into the side walls.
   - Drop `4x TE Connectivity 292303-7` right-angle USB-A receptacles straight down (`-Z`) onto the stepped `Z = 10.80 / 9.55 mm` cradle floors so their PCB kink legs engage the `Y = -32.35 .. -30.00 mm` retention slots.
2. **Glue `2x usb_retainer_bracket` Bridges:**
   - Apply a drop of CA / epoxy to the outer, centre (`X = ±25.00 mm`), and inner USB divider walls of `lower_tub` and press the Left and Right `usb_retainer_bracket` pieces down until their `Z = 16.85 mm` bridges seat over the `4x` USB-A metal shells (`0.15 mm` top clearance) and their `Z = 23.45 mm` stop blocks (`Face854` extended to `Y = -27.80 mm`) and `Ø2.80 mm` guide poles stand vertical at `(±32.32, -32.20)`.
3. **Omron SS-5GL Microswitches (`POWER` & `RESET`):**
   - Slide each `Omron SS-5GL` onto its integral `Ø2.20 mm` front locating pin (`Y = -26.45 mm`) with the hinge lever extending forward (`-Y`) over the `usb_retainer_bracket` stop block, and clamp Hole 2 (`Y = -16.95 mm`) with an `M2 x 10 DIN 912` SHCS + `M2 DIN 125` washer.
4. **Front Power LED & Light Pipe:**
   - Slide `led_light_pipe` (Clear PETG) into the `X = 0` front aperture and seat the `Kingbright L-93WEGW` 3-lead bi-colour LED (`330 Ω` resistors on Red & Green anodes) into the rear cradle.
5. **Inverted Radxa X4 + M.2 2230 SSD + RJ45 Breakout:**
   - Install the M.2 2230 NVMe SSD on the Radxa X4, solder the USB-A, RJ45, Omron (`POWER`/`RESET`), and LED leads, and fasten the inverted Radxa X4 (`4x M2.5 x 6 BHCS` at `Z = 8.20 mm`) and rear-right RJ45 breakout (`2x M2.5 x 6 BHCS` at `Z = 5.60 mm`).
5b. **Cooling (REQ-04):**
   - Clean the N100 die, spread a thin layer of non-conductive paste (no thermal pad), and set the `Same Sky HSB26-343408` on it, centred on the package.
   - Lower the printed `cooling_duct` over it (cover onto the pin tips, skirts either side) and stick the `0.5 mm` silicone pad on the cover above the die.
   - Seat the `Sunon MF30060V2` on the duct (label down, blowing into the plenum) and plug it into the X4's 2-pin fan header.
   - Set `cooling_hood` on the fan rim and the duct, and run `1 mm` foam tape along the hood's wall tops.
   - Stick a `3M Bumpon SJ5012` over each corner screw counterbore on the underside.
6. **Seat `POWER` & `RESET` Buttons on Guide Poles:**
   - Place `power_slider` (`X = -32.32 mm`) and `reset_button` (`X = +32.32 mm`) straight down onto the `Ø2.80 mm` vertical guide poles on `usb_retainer_bracket`. The `Ø3.20 mm` blind underside holes (`1.70 mm` engaged at rest) hold both buttons upright and oriented before the top shell is installed.
7. **Upper Shell Trim (`cartridge_flaps` & `front_bezel`):**
   - Glue `cartridge_flaps` into the top slot pocket and `front_bezel` (2.0 mm clear acrylic + rear Cricut N64 decal aligned with `bezel_laser_jig_0.svg`) into the front nose pocket of `upper_shell`.
8. **Close Enclosure:**
   - Lower `upper_shell` straight down (`-Z`) onto `lower_tub` so the `360°` guide chimneys telescope over `power_slider` and `reset_button`, and fasten from underneath with `4x M3 x 12 DIN 912` SHCS.
