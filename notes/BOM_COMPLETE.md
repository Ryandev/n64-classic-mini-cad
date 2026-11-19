# N64 Classic Mini — Complete Bill of Materials (BOM) & Buyer's Guide

Generated programmatically by `./run bom` (`lib/bom.py`).

## Buyer's Guide: Radxa X4 SBC, M.2 2230 Storage, Shared GBA Hardware & Workshop Notes

### 1. Which Radxa X4 Board to Buy
- **Recommended Model:** **Radxa X4 4GB (`RS119-D4E0`) or 8GB (`RS119-D8E0`), WITHOUT eMMC, WITHOUT pre-soldered 40-pin GPIO header**.
- **Why 4GB / 8GB RAM:** Batocera Linux + Mupen64Plus-Next (`GLideN64` / `ParaLLEl-RDP` at 1080p60) uses `< 1.5 GB` RAM total. The **4GB LPDDR5** model (`~$50–$58`) has over `2.5 GB` of free headroom; choose **8GB** (`~$65`) only if you also plan to run heavier emulators or texture packs.
- **Why NO pre-soldered 40-pin GPIO header:** Ordering the bare-pad (`H0`) version saves desoldering the 40-pin header and leaves clean through-hole pads for soldering the `Omron SS-5GL` `POWER`/`RESET` switches and the 3-lead bi-colour Red/Green LED.
- **Why Upside-Down Mounting (Heat Sink Facing UP `+Z`):** On the Radxa X4, the Intel Processor N100 lives on the underside of the PCB. Mounted inverted (`180 deg` roll about `+X` at `Z = 8.20 mm`), the N100 and its pin-fin heat sink face up into the dome. A 30 mm fan under the 25 top louvers blows room air down through the pins; it leaves through the floor vents, waist slots and rear slits (`subassembly/cooling_check.py` computes the junction temperature from the measured openings).

### 2. Which M.2 SSD to Buy & Two-Number Storage Estimator (`./run bom --estimate <N_ROMS> <N_PORTS>`)
- **Required Form Factor:** **M.2 2230 NVMe PCIe Gen3 x4 SSD** (`22 mm wide x 30 mm long`, M-key — same compact size used in Steam Deck / ROG Ally; **do not** buy 2242 or 2280).
- **Two-Number `/userdata` Usage Formula (in binary `GiB`, after 8.0 GiB `/boot`):**
  Plug in **`N_roms`** (emulated N64 games) and **`N_ports`** (native PC ports with HD packs):
  ```text
  /userdata Used (GiB) = 20.0 GiB (fixed) + (0.25 GiB x N_roms) + (2.50 GiB x N_ports)
                         (or 0.03 GiB x N_roms if no GLideN64 .hts packs are used)
  ```
  - **Fixed `/userdata` Cache & Scratch Overhead (`20.0 GiB`, plus `8.0 GiB` `/boot`):**
    - `6.0 GiB` — `/userdata/system/swap` file (for Torch `.o2r` extraction & 4K packs)
    - `6.0 GiB` — Mesa Vulkan shader cache + `GLideN64` uncompressed `.htc` mipmap cache
    - `8.0 GiB` — Temporary archive unpack scratch buffer (`2x` largest texture pack zip)
  - **Per Emulated ROM (`0.03 GiB` bare / `0.25 GiB` with `.hts` HD packs):**
    - `0.03 GiB` (`30 MiB`): `16.5 MiB` `.z64` ROM + `13.5 MiB` 1080p box art, `.mp4` snap & 4 save states
    - `0.25 GiB` (`250 MiB`): blended average when ~15% of emulated ROMs have a `1.5 GiB` `GLideN64` `.hts` pack
  - **Per Native PC Port (`2.50 GiB` average):**
    - `0.12 GiB` (`120 MiB`): AppImage / `N64Recomp` binary + extracted `.o2r` or stored `.z64`
    - `2.38 GiB`: `.o2r` / `.rtz` HD texture, 3D model & remastered audio packs (`1.5–6.0 GiB` each)

- **Usable Drive Capacity After Formatting & 20% SSD Wear-Leveling Reserve:**

  | Sticker Size | Raw Binary (`GiB`) | Usable `ext4` (`/userdata`) | Safe 80% Ceiling (Keep 20% Free) |
  |---:|---:|---:|---:|
  | **128 GB** | 119.2 GiB | 105.6 GiB | **84.5 GiB** |
  | **256 GB** | 238.4 GiB | 218.9 GiB | **175.1 GiB** |
  | **512 GB** | 476.8 GiB | 445.4 GiB | **356.3 GiB** |

- **Quick Lookup Table (`Total GiB` vs Safe 80% Drive Ceiling):**

  | Build Scenario | `N_roms` | `N_ports` | Fixed | ROMs + `.hts` | Ports + HD | **Total Used** | Recommended SSD |
  |---|---:|---:|---:|---:|---:|---:|---|
  | Bare ROMs + Current Ports (no `.hts`) | 300 | 28 | 20.0 GiB | 9.0 GiB | 70.0 GiB | **99.0 GiB** | **256 GB** (`175 GiB` safe) |
  | Loaded Current Build (with `.hts`) | 300 | 28 | 20.0 GiB | 75.0 GiB | 70.0 GiB | **165.0 GiB** | **256 GB** (`175 GiB` safe) / **512 GB** |
  | Future-Proof (`+22` new Recomp ports) | 300 | 50 | 20.0 GiB | 75.0 GiB | 125.0 GiB | **220.0 GiB** | **512 GB** (`356 GiB` safe) |
  | Heavy Future (`+42` new Recomp ports) | 300 | 70 | 20.0 GiB | 75.0 GiB | 175.0 GiB | **270.0 GiB** | **512 GB** (`356 GiB` safe) |

- **Recommended Capacity:** **256 GB or 512 GB M.2 2230 NVMe** (e.g. *Kioxia BG4 / BG5 / BG6* or *WD PC SN530 / SN740* OEM Steam Deck / ROG Ally pulls). Run `./run bom --estimate <N_ROMS> <N_PORTS>` to compute any custom combination.

### 3. Shared GBA BOM Parts: `Omron SS-5GL` Buttons & `Kingbright L-93WEGW` LED
- **Momentary `POWER` (`J-03`) & `RESET` (`J-04`) Buttons with `Omron SS-5GL`:** Both top-deck buttons use the exact same smooth cylindrical-crowned stadium profile (transverse slider nub removed from `POWER`) and actuate `2x Omron SS-5GL` microswitches (`0.49 N` operating force, `OP = 8.8 +/- 0.8 mm`). Each switch is dropped into its tower from above and held by two `M2.5 x 10` screws driven from behind through close-fit tower holes into both of its holes (C2, coupon plate 2). Each button presses its switch lever through a ridge under its centre, 72% along the lever (C3), with `2.10 mm` of travel to front-and-rear stops and `2.80 x 4.20 mm` anti-rotation oblong guide poles on `usb_retainer_bracket.py`: every switch across the full `OP = 8.0..9.6 mm` band releases at rest and clicks before the stop (`OMRON_ACT`).
- **Dual-Colour Front LED (`Kingbright L-93WEGW`, 3 mm, `Green = ON`):** Wire **Pin 2 (Common Cathode)** to `GND` (header pin 9), **Pin 1 (Red Anode)** via `330 Ω` to `GP4` (pin 7), and **Pin 3 (Green Anode)** via `330 Ω` to `GP7` (pin 29) on the Radxa X4's RP2040 (`firmware/rp2040_reset/code.py`). The RP2040 only runs while the PC is on: red in Batocera's menu, green while a game runs, dark in standby (C7; the launch wrapper tells it which over USB serial).
- **Hard Power-Off Resilience (Pulling the Plug Without Safe Shutdown):** Batocera's root OS (`/boot/batocera`) is a read-only SquashFS image in RAM that cannot be corrupted by a sudden power cut; `n64mini.console.suspend` flushes save states with `os.fsync()` before atomic `replace()`, ignores `0`-byte interrupted files, and `n64mini-service.sh` cleans up any orphaned `.tmp`/`.pending` files on boot. Set BIOS `Chipset -> PCH-IO Configuration -> State After G3 -> S0` (or `Last State`) if switching power at the wall socket.

### 4. Clear Acrylic Front Jewel (`front_bezel.py`) with Diode Laser + Cricut
- Cut `export/bezel_laser_jig/bezel_laser_jig_0.svg` out of `3.0 mm` birch plywood on your diode laser. Clamp a rough piece of `2.0 mm` clear cast acrylic under the `24.14 x 15.50 mm` plywood window to score/flush-trim the acrylic to exact size, then drop the clear acrylic face-down into the same plywood window to align and stick the Cricut-cut N64 vinyl decal onto the flat `+Y` back face before gluing into `upper_shell`.

## 1. Lower Tub, Inverted Radxa X4 & Front Panel Subassembly (`lib/subassembly/radxa_mount_mech.py`, `front_panel_mech.py`)

### Fabricated Parts (SLA Resin / PETG Cooling / Diode Laser / Clear Acrylic)

| Part | Material | Qty |
|---|---|---:|
| Lower Tub (`lib/variant/lower_tub.py`, `130.00 x 99.88 x 14.74 mm` with integrated bi-colour LED & Clear Resin Light-Pipe Holder Cradle) | SLA Tough Resin (JLC3DP Imagine Black / 9600) | 1 |
| Twin-Port Hinged Front Controller Covers (`lib/part/front_port_cover.py`, `28.0 x 11.0 x 1.8 mm`: Left `P1+P2` at `X=-25.0`, Right `P3+P4` at `X=+25.0`) | SLA Tough Resin (JLC3DP Imagine Black / 9600 or Elegoo Mars) | 2 |
| Left & Right Removable Front Control & I/O Subassembly Carriers (`lib/part/front_io_carrier_l.py`, `front_io_carrier_r.py`, `46.0 x 32.7 x 20.2 mm`, bench-assembled with door, hinge pin, 2x USB-A & Omron SS-5GL) | SLA Tough Resin (JLC3DP Imagine Black / 9600 or Elegoo Mars) | 2 |
| USB-A Top Retainer & Button Travel-Stop Brackets (`lib/part/usb_retainer_bracket.py`, `37.3 x 8.8 x 18.7 mm`, clamped onto `front_io_carrier` over the 4 USB-A receptacles via the outer M2.5 screw) | SLA Tough Resin (JLC3DP Imagine Black / 9600 or Elegoo Mars) | 2 |
| Shallow N64 Controller Port Inserts (`lib/part/n64_port_insert.py`, `Ø10.88 x 1.92 mm` with `R=0.50mm` front rim fillet & `P1..P4` tactile pips) | SLA Tough Resin (JLC3DP 9600 / Elegoo Mars, Light Cool Grey) | 4 |
| Lenticular N64 Power LED Light Pipe (`lib/part/led_light_pipe.py`, `6.36 x 1.76 mm` authentic N64 almond front lens + rear optical barrel) | SLA Clear Resin (JLC3DP 8001 Transparent) | 1 |
| Cooling duct (`lib/part/cooling_duct.py`): fan seat, plenum, chamber and the cover that clamps the heat sink; printed cover-side down | PETG Basic (the heat sink runs ~60-70 C, near its limit: check it in the on-console thermal test) | 1 |
| Duct floor plate (`lib/part/duct_floor.py`): the plenum floor, printed flat and glued into the duct's frame with 2-part epoxy (the bead seals the plenum) | PETG Basic (same as the duct) | 1 |
| Intake hood (`lib/part/cooling_hood.py`): seals the 25 top louvers to the fan; printed floor-side down | PETG Basic | 1 |

### Bought Hardware & Electronics

| Item | Specification | Qty |
|---|---|---:|
| Radxa X4 SBC — **4GB or 8GB LPDDR5, NO eMMC, NO 40-pin GPIO header** (SKU `RS119-D4E0` 4GB or `RS119-D8E0` 8GB; Intel Processor N100, mounted upside-down so SoC & heatsink face `+Z` up into the dome) | `Radxa X4 4GB/8GB (RS119-D4E0 / RS119-D8E0, no GPIO header)` | 1 |
| M.2 **2230** NVMe PCIe Gen3 x4 SSD — **256GB or 512GB** (M-key, `22 x 30 mm`; e.g. Kioxia BG4/BG5/BG6 or WD SN530/SN740 Steam Deck pull; sized for ROMs + native PC ports + HD `.o2r`/`.rtz`/`.hts` texture packs + swap/shader caches) | `M.2 2230 NVMe SSD (256GB / 512GB)` | 1 |
| Same Sky HSB26-343408 BGA pin-fin heat sink (`33.5 x 33.5 x 10 mm`, 14 x 14 pins, black anodised AL6063; on the N100 with paste, clamped by the printed duct; replaces the stock silicone pad, which limits the stock cooler) | `Same Sky HSB26-343408` | 1 |
| Sunon MF30060V2-1000U-A99 fan (`30 x 30 x 6 mm`, 5 V, 3.7 CFM, 0.11 inH2O, 15.7 dB(A); 2 wires to the Radxa X4 2-pin 1.25 mm fan header, which sets its speed). Louder, more margin: Same Sky CFM-3007CF-0110-320 (7 mm, 32 dB(A)) | `Sunon MF30060V2-1000U-A99` | 1 |
| Thermal paste, non-conductive (e.g. Arctic MX-4 or Noctua NT-H1): thin layer between the N100 die and the heat sink. No thermal pad. | `Non-conductive thermal paste` | 1 |
| 3M Bumpon SJ5012 rubber foot (`12.7 mm` cylindrical, flat top, `3.5 mm` tall): one over each corner screw counterbore; the gap feeds the floor vents | `3M Bumpon SJ5012` | 4 |
| Self-adhesive silicone rubber pad, `0.5 mm`, ~`30 x 12 mm`: on the duct cover under the cartridge cradle; closing the shell presses the heat sink onto the die | `Silicone pad 0.5 mm` | 1 |
| Closed-cell foam tape, `1 mm` thick, `3 mm` wide: seals the intake hood's wall tops to the roof underside (~200 mm) | `Foam tape 1 x 3 mm` | 1 |
| Ruthex RX-M2.5x4.0 brass threaded insert (`M2.5 x 4.0 mm`, knurl `OD 3.5 mm`, heat-set into `Ø3.20 mm` bores on the Stage-2 FDM fit mule or cold-glued with medium CA / 2-part epoxy into `Ø3.60 mm` slip-fit bores on the Stage-5 SLA resin shell: 4 for Radxa X4 standoffs + 6 for Front Subassembly floor bosses) | `Ruthex RX-M2.5x4.0` | 10 |
| M2.5 x 6 ISO 7380 button-head socket screw (A2 stainless: 4 for Radxa X4 + 4 for Inner/Rear Front Subassembly ears) | `M2.5 x 6 ISO 7380 BHCS` | 8 |
| M2.5 x 16 ISO 7380 button-head socket screw (A2 stainless: 2x outer Front Subassembly screws clamping `usb_retainer_bracket` + `front_io_carrier` into `lower_tub`) | `M2.5 x 16 ISO 7380 BHCS` | 2 |
| 6-pin Micro-JST 1.25 mm (Molex PicoBlade / JST GH) pre-crimped Male + Female wire-to-wire inline connector pair (`9.5 x 8.0 x 3.4 mm` mated, 1 per front subassembly: `+5V, D1-, D1+, D2-, D2+, GND`) | `6-pin Micro-JST 1.25mm wire-to-wire pair` | 2 |
| 2-pin Micro-JST 1.25 mm (Molex PicoBlade / JST GH) pre-crimped Male + Female wire-to-wire inline connector pair (`4.5 x 8.0 x 3.4 mm` mated, 1 per front subassembly for the `POWER` and `RESET` `Omron SS-5GL` `COM` + `NO` leads) | `2-pin Micro-JST 1.25mm wire-to-wire pair` | 2 |
| TE Connectivity 292303-7 right-angle USB 2.0 Type-A female receptacle (Farnell `1240559` / Mouser `571-292303-7`, wired to Radxa X4 USB pads) | `TE 292303-7 USB-A receptacle` | 4 |
| Kingbright L-93WEGW (`Rapid 55-0155`) 3 mm Red/Green bi-colour 3-lead common-cathode through-hole LED (Pin 1 Red `625 nm` = in the menu, Pin 2 Common Cathode = `GND`, Pin 3 Green `565 nm` = in a game) | `Kingbright L-93WEGW (Rapid 55-0155) 3 mm bi-colour LED` | 1 |
| 330 Ohm 0.25 W metal-film axial resistor (`1%`, current-limiting on Pin 1 Red anode & Pin 3 Green anode — shared GBA BOM part) | `330R 0.25W 1% axial resistor` | 2 |
| Neodymium disc magnet (`Ø3.0 x 1.0 mm`, N52 — 2 per cover + 2 per bay) | `3.0 x 1.0 mm N52 magnet` | 8 |
| Steel door hinge pin (`Ø1.5 x 27.4 mm`, 1 per door pushed end to end; cut from 1.5 mm rod) | `ISO 8734 1.5 x 27.4 dowel pin` | 2 |

## 2. Upper Shell, Clear Acrylic Front Jewel & Top Deck Controls (`AC-T18`)

### Fabricated Parts (SLA Resin / PETG Cooling / Diode Laser / Clear Acrylic)

| Part | Material | Qty |
|---|---|---:|
| Upper Shell (`lib/variant/upper_shell.py`, `130.00 x 99.88 x 20.56 mm` sculpted N64 top deck with 25 parabolic louvers & engraved lettering) | SLA Tough Resin (JLC3DP Imagine Black / 9600) | 1 |
| Front N64 Emblem Jewel (`lib/part/front_bezel.py`, `24.14 x 15.50 x 2.00 mm` shaped from Clear Acrylic with Cricut vinyl N64 decal on flat `+Y` back) | 2.0mm Clear Cast Acrylic + Rear Cricut Vinyl Sticker | 1 |
| Diode-Laser Birch Plywood Cutting & Cricut Alignment Jig (`lib/part/bezel_laser_jig.py` -> `export/bezel_laser_jig/bezel_laser_jig_0.svg`) | 3.0mm Laser-Grade Birch Plywood (cut on diode laser) | 1 |
| Cartridge Slot Dust-Flap Insert (`lib/part/cartridge_flaps.py`, `57.50 x 10.00 x 1.35 mm` with central parting seam & semicircular end tabs) | SLA Tough Resin (JLC3DP 9600 / Elegoo Mars, Light Cool Grey) | 1 |
| Momentary Power Button Plunger (`lib/part/power_slider.py`, smooth cylindrical-crowned stadium cap matching Reset, 3D-engraved `POWER`) | SLA Tough Resin (JLC3DP 9600 / Elegoo Mars, Light Cool Grey) | 1 |
| Momentary Reset Button Plunger (`lib/part/reset_button.py`, smooth cylindrical-crowned stadium cap, 3D-engraved `RESET`) | SLA Tough Resin (JLC3DP 9600 / Elegoo Mars, Light Cool Grey) | 1 |

### Bought Hardware & Electronics

| Item | Specification | Qty |
|---|---|---:|
| Omron SS-5GL subminiature hinge-lever SPDT microswitch (`19.8 x 6.4 x 10.2 mm`, `0.49 N` max operating force, `OP = 8.8 +/- 0.8 mm` — shared GBA BOM part; 1 under `POWER`, 1 under `RESET`) | `Omron SS-5GL microswitch` | 2 |
| M2.5 x 10 mm pan-head screw (2 per `Omron SS-5GL`, driven from behind the switch tower through its close-fit holes into both of the switch's `Ø2.35 mm` holes, where it bites; before the Radxa board. Owner bench test 2026-11-15) | `M2.5 x 10 pan-head screw` | 4 |
| Ruthex RX-M3x5.7 brass threaded insert (`M3 x 5.7 mm`, knurl `OD 4.2 mm`, heat-set into `Ø4.00 mm` bores on the Stage-2 FDM fit mule or cold-glued with medium CA / 2-part epoxy into `Ø4.30 mm` slip-fit bores on the Stage-5 SLA resin `upper_shell` corner bosses — shared GBA BOM part) | `Ruthex RX-M3x5.7` | 4 |
| M3 x 14 DIN 912 socket-head cap screw (A2-70, 4 corner enclosure bolts; length checked by J01_SCREW) | `M3 x 14 DIN 912 SHCS` | 4 |
| 2.0 mm Clear Cast Acrylic sheet blank (`>= 35 x 25 mm`) + Cricut adhesive vinyl (Matte Black background + Red/Blue/Green/Yellow/White N64 logo) | `2.0mm Clear Cast Acrylic + Cricut vinyl` | 1 |

## Master Bought-Hardware Rollup

| Specification | Description | Total Qty |
|---|---|---:|
| `2-pin Micro-JST 1.25mm wire-to-wire pair` | 2-pin Micro-JST 1.25 mm (Molex PicoBlade / JST GH) pre-crimped Male + Female wire-to-wire inline connector pair (`4.5 x 8.0 x 3.4 mm` mated, 1 per front subassembly for the `POWER` and `RESET` `Omron SS-5GL` `COM` + `NO` leads) | 2 |
| `2.0mm Clear Cast Acrylic + Cricut vinyl` | 2.0 mm Clear Cast Acrylic sheet blank (`>= 35 x 25 mm`) + Cricut adhesive vinyl (Matte Black background + Red/Blue/Green/Yellow/White N64 logo) | 1 |
| `3.0 x 1.0 mm N52 magnet` | Neodymium disc magnet (`Ø3.0 x 1.0 mm`, N52 — 2 per cover + 2 per bay) | 8 |
| `330R 0.25W 1% axial resistor` | 330 Ohm 0.25 W metal-film axial resistor (`1%`, current-limiting on Pin 1 Red anode & Pin 3 Green anode — shared GBA BOM part) | 2 |
| `3M Bumpon SJ5012` | 3M Bumpon SJ5012 rubber foot (`12.7 mm` cylindrical, flat top, `3.5 mm` tall): one over each corner screw counterbore; the gap feeds the floor vents | 4 |
| `6-pin Micro-JST 1.25mm wire-to-wire pair` | 6-pin Micro-JST 1.25 mm (Molex PicoBlade / JST GH) pre-crimped Male + Female wire-to-wire inline connector pair (`9.5 x 8.0 x 3.4 mm` mated, 1 per front subassembly: `+5V, D1-, D1+, D2-, D2+, GND`) | 2 |
| `Foam tape 1 x 3 mm` | Closed-cell foam tape, `1 mm` thick, `3 mm` wide: seals the intake hood's wall tops to the roof underside (~200 mm) | 1 |
| `ISO 8734 1.5 x 27.4 dowel pin` | Steel door hinge pin (`Ø1.5 x 27.4 mm`, 1 per door pushed end to end; cut from 1.5 mm rod) | 2 |
| `Kingbright L-93WEGW (Rapid 55-0155) 3 mm bi-colour LED` | Kingbright L-93WEGW (`Rapid 55-0155`) 3 mm Red/Green bi-colour 3-lead common-cathode through-hole LED (Pin 1 Red `625 nm` = in the menu, Pin 2 Common Cathode = `GND`, Pin 3 Green `565 nm` = in a game) | 1 |
| `M.2 2230 NVMe SSD (256GB / 512GB)` | M.2 **2230** NVMe PCIe Gen3 x4 SSD — **256GB or 512GB** (M-key, `22 x 30 mm`; e.g. Kioxia BG4/BG5/BG6 or WD SN530/SN740 Steam Deck pull; sized for ROMs + native PC ports + HD `.o2r`/`.rtz`/`.hts` texture packs + swap/shader caches) | 1 |
| `M2.5 x 10 pan-head screw` | M2.5 x 10 mm pan-head screw (2 per `Omron SS-5GL`, driven from behind the switch tower through its close-fit holes into both of the switch's `Ø2.35 mm` holes, where it bites; before the Radxa board. Owner bench test 2026-11-15) | 4 |
| `M2.5 x 16 ISO 7380 BHCS` | M2.5 x 16 ISO 7380 button-head socket screw (A2 stainless: 2x outer Front Subassembly screws clamping `usb_retainer_bracket` + `front_io_carrier` into `lower_tub`) | 2 |
| `M2.5 x 6 ISO 7380 BHCS` | M2.5 x 6 ISO 7380 button-head socket screw (A2 stainless: 4 for Radxa X4 + 4 for Inner/Rear Front Subassembly ears) | 8 |
| `M3 x 14 DIN 912 SHCS` | M3 x 14 DIN 912 socket-head cap screw (A2-70, 4 corner enclosure bolts; length checked by J01_SCREW) | 4 |
| `Non-conductive thermal paste` | Thermal paste, non-conductive (e.g. Arctic MX-4 or Noctua NT-H1): thin layer between the N100 die and the heat sink. No thermal pad. | 1 |
| `Omron SS-5GL microswitch` | Omron SS-5GL subminiature hinge-lever SPDT microswitch (`19.8 x 6.4 x 10.2 mm`, `0.49 N` max operating force, `OP = 8.8 +/- 0.8 mm` — shared GBA BOM part; 1 under `POWER`, 1 under `RESET`) | 2 |
| `Radxa X4 4GB/8GB (RS119-D4E0 / RS119-D8E0, no GPIO header)` | Radxa X4 SBC — **4GB or 8GB LPDDR5, NO eMMC, NO 40-pin GPIO header** (SKU `RS119-D4E0` 4GB or `RS119-D8E0` 8GB; Intel Processor N100, mounted upside-down so SoC & heatsink face `+Z` up into the dome) | 1 |
| `Ruthex RX-M2.5x4.0` | Ruthex RX-M2.5x4.0 brass threaded insert (`M2.5 x 4.0 mm`, knurl `OD 3.5 mm`, heat-set into `Ø3.20 mm` bores on the Stage-2 FDM fit mule or cold-glued with medium CA / 2-part epoxy into `Ø3.60 mm` slip-fit bores on the Stage-5 SLA resin shell: 4 for Radxa X4 standoffs + 6 for Front Subassembly floor bosses) | 10 |
| `Ruthex RX-M3x5.7` | Ruthex RX-M3x5.7 brass threaded insert (`M3 x 5.7 mm`, knurl `OD 4.2 mm`, heat-set into `Ø4.00 mm` bores on the Stage-2 FDM fit mule or cold-glued with medium CA / 2-part epoxy into `Ø4.30 mm` slip-fit bores on the Stage-5 SLA resin `upper_shell` corner bosses — shared GBA BOM part) | 4 |
| `Same Sky HSB26-343408` | Same Sky HSB26-343408 BGA pin-fin heat sink (`33.5 x 33.5 x 10 mm`, 14 x 14 pins, black anodised AL6063; on the N100 with paste, clamped by the printed duct; replaces the stock silicone pad, which limits the stock cooler) | 1 |
| `Silicone pad 0.5 mm` | Self-adhesive silicone rubber pad, `0.5 mm`, ~`30 x 12 mm`: on the duct cover under the cartridge cradle; closing the shell presses the heat sink onto the die | 1 |
| `Sunon MF30060V2-1000U-A99` | Sunon MF30060V2-1000U-A99 fan (`30 x 30 x 6 mm`, 5 V, 3.7 CFM, 0.11 inH2O, 15.7 dB(A); 2 wires to the Radxa X4 2-pin 1.25 mm fan header, which sets its speed). Louder, more margin: Same Sky CFM-3007CF-0110-320 (7 mm, 32 dB(A)) | 1 |
| `TE 292303-7 USB-A receptacle` | TE Connectivity 292303-7 right-angle USB 2.0 Type-A female receptacle (Farnell `1240559` / Mouser `571-292303-7`, wired to Radxa X4 USB pads) | 4 |
