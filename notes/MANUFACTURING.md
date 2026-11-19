# Manufacturing & Assembly Guide

## 1. SLA Resin (JLC3DP / PCBWay / Elegoo Mars) & FDM Cooling (Bambu Lab X2D)

Every visible, structural, or tactile part is printed in **SLA Tough Resin** (`JLC3DP Imagine Black / 9600` or `PCBWay UTR-8100 / Somos Ledo`, plus `JLC3DP 8001 Clear Resin` for `led_light_pipe`); only the 3 internal thermal parts (`cooling_duct`, `duct_floor`, `cooling_hood`, which sit directly on the `60–70 °C` N100 heat sink) are printed in **PETG Basic** on the Bambu Lab X2D (owner decision 2026-11-18). Because `upper_shell` and `lower_tub` (`130.00 x 99.88 mm`) exceed the Elegoo Mars build width, order the SLA resin parts from **JLC3DP** or **PCBWay** using the production `.step` / `.stl` files in `export/<part>/`.

| Parameter | SLA Tough Resin enclosure & mechanisms (`lower_tub`, `upper_shell`, `front_io_carrier_l`/`_r`, `usb_retainer_bracket`, `front_port_cover`, `power_slider`, `reset_button`, `cartridge_flaps`, `n64_port_insert`) | SLA Clear Resin optical lens (`led_light_pipe`) | FDM internal cooling (`cooling_duct`, `duct_floor`, `cooling_hood`) |
|---|---|---|---|
| **Material** | SLA Tough Resin (`JLC3DP Imagine Black / 9600`) | SLA Clear Resin (`JLC3DP 8001` with gloss clear coat) | PETG Basic on Bambu Lab X2D (`PRINTING.md`) |
| **Layer / resolution** | `0.05 mm` (`50 µm`) SLA | `0.05 mm` (`50 µm`) SLA | `0.16 mm` (`0.4 mm` nozzle, `4` wall loops) |
| **Button guide fit** | `2.80 x 4.20 mm` oblong pole in `2.96 x 4.36 mm` sleeve (`SLEEVE_CLEAR = 0.08 mm/side`) | — | — |

**Before printing the PETG cooling parts or test coupons, read [`PRINTING.md`](PRINTING.md).**

---

## 2. Cold Glue-In Brass Insert Installation (`14x` Ruthex brass inserts total: 4 + 6 + 4)

Because thermoset SLA resin cannot be heat-set with a soldering iron, the insert bores are drawn at `+0.10 mm` slip-fit over the Ruthex knurl OD (`INSERT_M25_BORE_D = 3.60 mm` over the `3.50 mm` RX-M2.5x4.0 knurl, and `INSERT_M3_BORE_D = 4.30 mm` over the `4.20 mm` RX-M3x5.7 knurl). Apply a small drop of **medium CA glue or 2-part epoxy** to the bore wall (keeping adhesive out of the M2.5/M3 threads) and push each insert flush by hand:

1. **Radxa X4 standoffs in `lower_tub` (`4x Ruthex RX-M2.5x4.0`):**
   - Slip-fit bore: `Ø3.60 mm`, depth `4.5 mm` inside `Ø7.0 mm` standoff post (`wall = 1.70 mm`; `1.40 mm` in the top `1.0 mm`, stepped to `Ø6.4 mm` to clear Radxa's parts).
   - Press flush with the `Z = 8.20 mm` standoff top datum.
2. **Left & Right Front Control/I/O Subassembly bosses in `lower_tub` (`6x Ruthex RX-M2.5x4.0`):**
   - Bore: `Ø3.20 mm` heat-set (Stage-2 FDM fit mule) or `Ø3.60 mm` slip-fit (Stage-5 SLA resin), `4.15 mm` deep (`Z = 0.85 .. 5.00 mm`) in the `6x` flat-top floor bosses (`(±43.80, -32.20)`, `(±6.40, -30.20)`, `(±25.00, -15.50)`).
   - Press flush with the `Z = 5.00 mm` boss top datum.
3. **Omron SS-5GL switch mounts in `front_io_carrier_l`/`_r`: no inserts (C2).** The `2x` holes
   through each tower (`Ø2.60 mm` close-fit clearance) let two `M2.5 x 10` screws thread from
   behind directly into the switch's own `Ø2.35 mm` holes (see the assembly step).
4. **Enclosure corner bosses in `upper_shell` (`4x Ruthex RX-M3x5.7`):**
   - Slip-fit bore: `Ø4.30 mm`, depth `5.8 mm` inside `Ø8.4 mm` corner boss (`wall = 2.05 mm`).
   - Press flush with the `Z = 12.94 mm` (`SPLIT_Z`) upper-shell parting face.

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

## 4. Top-Down Assembly Sequence (`front_io_carrier_l`/`_r` -> `lower_tub` -> `upper_shell`)

1. **Bench-Assemble Left (`P1+P2 / Power`) & Right (`P3+P4 / Reset`) Front Subassemblies (`front_io_carrier_l.py`, `front_io_carrier_r.py`):**
   - Glue `4x` `n64_port_insert` rings (`P1..P4`) onto the `2x` `front_port_cover` doors and press-fit `8x` `Ø3.0 x 1.0 mm` N52 magnets into the doors (`4x`), carrier central keeper pillars (`2x`), and `upper_shell` keeper pillars (`2x`).
   - Seat each door's `22.20 mm` centre knuckle between the carrier's two `2.10 mm` `360°` hinge barrels and push the single `Ø1.5 x 27.4 mm` steel hinge pin through the inner barrel (`Ø1.60 mm` close fit), door knuckle (`Ø1.80 mm` turning bore), and outer barrel (`Ø1.50 mm` press fit) (`HINGE_PINS`).
   - Drop `2x TE Connectivity 292303-7` right-angle USB-A receptacles per carrier straight down (`-Z`) onto the stepped `Z = 10.80 / 9.55 mm` floor so their kink legs engage the `Y = -32.35 .. -30.00 mm` retention slots, and solder their 4 downward tails per port to the `6-pin Micro-JST 1.25 mm` pigtail harness exiting straight back (`+Y`).
   - Drop each `Omron SS-5GL` straight down against the carrier's integrated rear switch tower (`OMRON_INSTALL`), drive two `M2.5 x 10` pan-head screws from behind the tower into both of the switch's `Ø2.35 mm` holes (`OMRON_SCREW`), and solder `COM` and `NO` to the `2-pin Micro-JST 1.25 mm` pigtail harness.
2. **Bolt Both Front Subassemblies & `2x usb_retainer_bracket` into `lower_tub`:**
   - Lower the bench-assembled Left and Right `front_io_carrier` modules straight down (`-Z`) onto `lower_tub`'s `6x` flat-top `Z = 5.00 mm` `RX-M2.5x4.0` floor bosses and fasten the 4 Inner-Rear (`(±6.40, -30.20)`) and Rear-Tower (`(±25.00, -15.50)`) ears with `4x M2.5 x 6 ISO 7380` button-head screws.
   - Place the Left and Right `usb_retainer_bracket` bridges over the `4x` USB-A metal shells (`Z = 16.85 mm`) so their `2.80 x 4.20 mm` oblong guide poles stand at `(±32.32, -32.20)` and clamp each bracket's outer foot (`(±43.80, -32.20)`) through the carrier into `lower_tub`'s Outer-Front `RX-M2.5x4.0` boss with `2x M2.5 x 16 ISO 7380` button-head screws (zero glue required).
3. **Front Power LED & Light Pipe:**
   - Slide `led_light_pipe` (SLA Clear Resin `8001` or Clear PETG) into the `X = 0` front aperture and seat the `Kingbright L-93WEGW` 3-lead bi-colour LED (`330 Ω` resistors on Red & Green anodes) into the rear cradle.
4. **Inverted Radxa X4 + M.2 2230 SSD + Micro-JST Harnesses:**
   - Install the M.2 2230 NVMe SSD on the Radxa X4, solder the board-side `2x 6-pin` (USB) and `2x 2-pin` (`POWER`/`RESET`) Micro-JST 1.25 mm mating leads plus the LED leads, fasten the inverted Radxa X4 onto the 4 standoffs (`4x M2.5 x 6 BHCS` at `Z = 8.20 mm`), and mate the 4 inline Micro-JST connectors in the open `+X` right-hand bay (`X = +45..47 mm`).
5. **Cooling (REQ-04):**
   - Clean the N100 die, spread a thin layer of non-conductive paste (no thermal pad), and set the `Same Sky HSB26-343408` on it, centred on the package.
   - **Before this, glue the `duct_floor` plate into `cooling_duct`** (any time after printing): scuff
     both faces, run 2-part epoxy round the duct's ledge, press the plate onto the ledge and let it
     cure. The bead all round seals the plenum, so the fan's air goes through the heat sink.
   - Lower the printed `cooling_duct` over it (cover onto the pin tips, skirts either side) and stick the `0.5 mm` silicone pad on the cover above the die.
   - Seat the `Sunon MF30060V2` on the duct (label down, blowing into the plenum) and plug it into the X4's 2-pin fan header.
   - Set `cooling_hood` on the fan rim and the duct, and run `1 mm` foam tape along the hood's wall tops.
   - Stick a `3M Bumpon SJ5012` over each corner screw counterbore on the underside.
6. **Seat `POWER` & `RESET` Buttons on Oblong Guide Poles:**
   - Place `power_slider` (`X = -32.32 mm`) and `reset_button` (`X = +32.32 mm`) straight down onto the `2.80 x 4.20 mm` oblong anti-rotation guide poles on `usb_retainer_bracket`. Each button's oblong sleeve slides on its pole and holds the button upright and rotationally aligned in `Z` before the top shell is installed; with the shell on, chimney and sleeve together guide it (rows `BTN_TILT`, `BTN_STACK`).
7. **Upper Shell Trim (`cartridge_flaps` & `front_bezel`):**
   - Glue `cartridge_flaps` into the top slot pocket and `front_bezel` (2.0 mm clear acrylic + rear Cricut N64 decal aligned with `bezel_laser_jig_0.svg`) into the front nose pocket of `upper_shell`.
8. **Close Enclosure:**
   - Lower `upper_shell` straight down (`-Z`) onto `lower_tub` so the `360°` guide chimneys telescope over `power_slider` and `reset_button`, and fasten from underneath with `4x M3 x 14 DIN 912` SHCS.
