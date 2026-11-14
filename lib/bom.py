"""Bill of Materials (BOM) generator for the N64 Classic Mini (`./run bom`).

Writes `notes/BOM_COMPLETE.md` with per-subassembly tables, master bought-hardware rollup,
and detailed buyer's guide for the Radxa X4 SBC, M.2 2230 NVMe storage sizing, shared GBA
components (`Omron SS-5GL` microswitches, `Kingbright L-93WEGW` Red/Green bi-colour LED,
`Ruthex` inserts, `DIN 912` / `ISO 4026` fasteners), and Clear Acrylic + Cricut front jewel.
"""

from __future__ import annotations

import os
import sys
from collections import defaultdict
from typing import Any

_LIB_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _LIB_DIR)

from assembly import datum as D  # noqa: E402

_REPO_DIR = os.path.dirname(_LIB_DIR)
BOM_MD_PATH = os.path.join(_REPO_DIR, "notes", "BOM_COMPLETE.md")

SUBASSEMBLIES: list[dict[str, Any]] = [
    {
        "id": "lower_tub_and_radxa",
        "title": (
            "1. Lower Tub, Inverted Radxa X4 & Front Panel Subassembly "
            "(`lib/subassembly/radxa_mount_mech.py`, `front_panel_mech.py`)"
        ),
        "printed": [
            {
                "part": (
                    "Lower Tub (`lib/variant/lower_tub.py`, `130.00 x 99.88 x 14.74 mm` with "
                    "integrated bi-colour LED & Clear PETG Light-Pipe Holder Cradle)"
                ),
                "material": "Charcoal Grey PETG Basic",
                "qty": 1,
            },
            {
                "part": (
                    "Twin-Port Hinged Front Controller Covers (`lib/part/front_port_cover.py`, "
                    "`28.0 x 11.0 x 1.8 mm`: Left `P1+P2` at `X=-25.0`, Right `P3+P4` at `X=+25.0`)"
                ),
                "material": "Charcoal Grey PETG Basic",
                "qty": 2,
            },
            {
                "part": (
                    "USB-A Top Retainer & Button Travel-Stop Brackets "
                    "(`lib/part/usb_retainer_bracket.py`, `31.6 x 8.8 x 11.85 mm`, glued onto "
                    "`lower_tub` USB-A cradle walls after seating the 4 USB-A receptacles)"
                ),
                "material": "Charcoal Grey PETG Basic",
                "qty": 2,
            },
            {
                "part": (
                    "Shallow N64 Controller Port Inserts (`lib/part/n64_port_insert.py`, "
                    "`Ø10.88 x 1.92 mm` with `R=0.50mm` front rim fillet & `P1..P4` tactile pips)"
                ),
                "material": "Light Cool Grey PETG Basic",
                "qty": 4,
            },
            {
                "part": (
                    "Lenticular N64 Power LED Light Pipe (`lib/part/led_light_pipe.py`, "
                    "`6.36 x 1.76 mm` authentic N64 almond front lens + rear optical barrel)"
                ),
                "material": "Clear / Transparent PETG (100% infill)",
                "qty": 1,
            },
            {
                "part": (
                    "Cooling duct (`lib/part/cooling_duct.py`): fan seat, plenum, chamber and the "
                    "cover that clamps the heat sink; printed cover-side down"
                ),
                "material": (
                    "PETG Basic (the heat sink runs ~60-70 C, near its limit: check it in the "
                    "on-console thermal test)"
                ),
                "qty": 1,
            },
            {
                "part": (
                    "Duct floor plate (`lib/part/duct_floor.py`): the plenum floor, printed flat "
                    "and glued into the duct's frame with 2-part epoxy (the bead seals the plenum)"
                ),
                "material": "PETG Basic (same as the duct)",
                "qty": 1,
            },
            {
                "part": (
                    "Intake hood (`lib/part/cooling_hood.py`): seals the 25 top louvers to the "
                    "fan; printed floor-side down"
                ),
                "material": "PETG Basic",
                "qty": 1,
            },
        ],
        "bought": [
            {
                "item": (
                    "Radxa X4 SBC — **4GB or 8GB LPDDR5, NO eMMC, NO 40-pin GPIO header** "
                    "(SKU `RS119-D4E0` 4GB or `RS119-D8E0` 8GB; Intel Processor N100, mounted "
                    "upside-down so SoC & heatsink face `+Z` up into the dome)"
                ),
                "spec": "Radxa X4 4GB/8GB (RS119-D4E0 / RS119-D8E0, no GPIO header)",
                "qty": 1,
            },
            {
                "item": (
                    "M.2 **2230** NVMe PCIe Gen3 x4 SSD — **64GB or 128GB** (M-key, `22 x 30 mm`; "
                    "e.g. Kioxia BG4/BG5 128GB or WD SN530/SN740 128GB; full N64 library + "
                    "Batocera OS + 1080p artwork uses only ~12–15 GB)"
                ),
                "spec": "M.2 2230 NVMe SSD (64GB / 128GB)",
                "qty": 1,
            },
            {
                "item": (
                    "Same Sky HSB26-343408 BGA pin-fin heat sink (`33.5 x 33.5 x 10 mm`, 14 x 14 "
                    "pins, black anodised AL6063; on the N100 with paste, clamped by the printed "
                    "duct; replaces the stock silicone pad, which limits the stock cooler)"
                ),
                "spec": "Same Sky HSB26-343408",
                "qty": 1,
            },
            {
                "item": (
                    "Sunon MF30060V2-1000U-A99 fan (`30 x 30 x 6 mm`, 5 V, 3.7 CFM, 0.11 inH2O, "
                    "15.7 dB(A); 2 wires to the Radxa X4 2-pin 1.25 mm fan header, which sets its "
                    "speed). Louder, more margin: Same Sky CFM-3007CF-0110-320 (7 mm, 32 dB(A))"
                ),
                "spec": "Sunon MF30060V2-1000U-A99",
                "qty": 1,
            },
            {
                "item": (
                    "Thermal paste, non-conductive (e.g. Arctic MX-4 or Noctua NT-H1): thin layer "
                    "between the N100 die and the heat sink. No thermal pad."
                ),
                "spec": "Non-conductive thermal paste",
                "qty": 1,
            },
            {
                "item": (
                    "3M Bumpon SJ5012 rubber foot (`12.7 mm` cylindrical, flat top, `3.5 mm` "
                    "tall): one over each corner screw counterbore; the gap feeds the floor vents"
                ),
                "spec": "3M Bumpon SJ5012",
                "qty": 4,
            },
            {
                "item": (
                    "Self-adhesive silicone rubber pad, `0.5 mm`, ~`30 x 12 mm`: on the duct "
                    "cover under the cartridge cradle; closing the shell presses the heat sink "
                    "onto the die"
                ),
                "spec": "Silicone pad 0.5 mm",
                "qty": 1,
            },
            {
                "item": (
                    "Closed-cell foam tape, `1 mm` thick, `3 mm` wide: seals the intake hood's "
                    "wall tops to the roof underside (~200 mm)"
                ),
                "spec": "Foam tape 1 x 3 mm",
                "qty": 1,
            },
            {
                "item": (
                    "Ruthex RX-M2.5x4.0 brass heat-set insert (`M2.5 x 4.0 mm`, `OD 3.2 mm`: "
                    "4 for Radxa X4 standoffs + 2 for 2.5GbE RJ45 Ethernet carrier standoffs)"
                ),
                "spec": "Ruthex RX-M2.5x4.0",
                "qty": 6,
            },
            {
                "item": (
                    "M2.5 x 6 ISO 7380 button-head socket screw (A2 stainless: "
                    "4 for Radxa X4 + 2 for 2.5GbE RJ45 Ethernet carrier)"
                ),
                "spec": "M2.5 x 6 ISO 7380 BHCS",
                "qty": 6,
            },
            {
                "item": (
                    "TE Connectivity 292303-7 right-angle USB 2.0 Type-A female receptacle "
                    "(Farnell `1240559` / Mouser `571-292303-7`, wired to Radxa X4 USB pads)"
                ),
                "spec": "TE 292303-7 USB-A receptacle",
                "qty": 4,
            },
            {
                "item": (
                    "Kingbright L-93WEGW (`Rapid 55-0155`) 3 mm Red/Green bi-colour 3-lead "
                    "common-cathode through-hole LED (Pin 1 Red `625 nm` = in the menu, "
                    "Pin 2 Common Cathode = `GND`, Pin 3 Green `565 nm` = in a game)"
                ),
                "spec": "Kingbright L-93WEGW (Rapid 55-0155) 3 mm bi-colour LED",
                "qty": 1,
            },
            {
                "item": (
                    "330 Ohm 0.25 W metal-film axial resistor (`1%`, current-limiting on "
                    "Pin 1 Red anode & Pin 3 Green anode — shared GBA BOM part)"
                ),
                "spec": "330R 0.25W 1% axial resistor",
                "qty": 2,
            },
            {
                "item": (
                    "2.5GbE 8P8C shielded RJ45 Ethernet receptacle on M2.5 breakout carrier "
                    "(`2x Ø2.70 mm` mounting ears at `(43.00, 23.00)` & `(51.50, 28.50)`)"
                ),
                "spec": "Panel-mount RJ45 jack",
                "qty": 1,
            },
            {
                "item": "Neodymium disc magnet (`Ø3.0 x 1.0 mm`, N52 — 2 per cover + 2 per bay)",
                "spec": "3.0 x 1.0 mm N52 magnet",
                "qty": 8,
            },
        ],
    },
    {
        "id": "upper_shell_and_controls",
        "title": "2. Upper Shell, Clear Acrylic Front Jewel & Top Deck Controls (`AC-T18`)",
        "printed": [
            {
                "part": (
                    "Upper Shell (`lib/variant/upper_shell.py`, `130.00 x 99.88 x 20.56 mm` "
                    "sculpted N64 top deck with 25 parabolic louvers & engraved lettering)"
                ),
                "material": "Charcoal Grey PETG Basic",
                "qty": 1,
            },
            {
                "part": (
                    "Front N64 Emblem Jewel (`lib/part/front_bezel.py`, `24.14 x 15.50 x 2.00 mm` "
                    "shaped from Clear Acrylic with Cricut vinyl N64 decal on flat `+Y` back)"
                ),
                "material": "2.0mm Clear Cast Acrylic + Rear Cricut Vinyl Sticker",
                "qty": 1,
            },
            {
                "part": (
                    "Diode-Laser Birch Plywood Cutting & Cricut Alignment Jig "
                    "(`lib/part/bezel_laser_jig.py` -> "
                    "`export/bezel_laser_jig/bezel_laser_jig_0.svg`)"
                ),
                "material": "3.0mm Laser-Grade Birch Plywood (cut on diode laser)",
                "qty": 1,
            },
            {
                "part": (
                    "Cartridge Slot Dust-Flap Insert (`lib/part/cartridge_flaps.py`, "
                    "`57.50 x 10.00 x 1.35 mm` with central parting seam & semicircular end tabs)"
                ),
                "material": "Light Cool Grey PETG Basic",
                "qty": 1,
            },
            {
                "part": (
                    "Momentary Power Button Plunger (`lib/part/power_slider.py`, smooth "
                    "cylindrical-crowned stadium cap matching Reset, 3D-engraved `POWER`)"
                ),
                "material": "Light Cool Grey PETG Basic",
                "qty": 1,
            },
            {
                "part": (
                    "Momentary Reset Button Plunger (`lib/part/reset_button.py`, smooth "
                    "cylindrical-crowned stadium cap, 3D-engraved `RESET`)"
                ),
                "material": "Light Cool Grey PETG Basic",
                "qty": 1,
            },
        ],
        "bought": [
            {
                "item": (
                    "Omron SS-5GL subminiature hinge-lever SPDT microswitch (`19.8 x 6.4 x "
                    "10.2 mm`, `0.49 N` max operating force, `OP = 8.8 +/- 0.8 mm` — shared GBA "
                    "BOM part; 1 under `POWER`, 1 under `RESET`)"
                ),
                "spec": "Omron SS-5GL microswitch",
                "qty": 2,
            },
            {
                "item": (
                    "3 x 10 mm pan-head thread-forming screw for plastics (PT type, e.g. EJOT "
                    "DELTA PT 30 x 10 or equivalent; 1 per `Omron SS-5GL`, driven from behind the "
                    "switch tower into the switch's `Ø2.35 mm` Hole 2, before the Radxa board; "
                    "bench-test on a spare switch first)"
                ),
                "spec": "3 x 10 thread-forming screw for plastics, pan head",
                "qty": 2,
            },
            {
                "item": (
                    "Ruthex RX-M3x5.7 brass heat-set insert (`M3 x 5.7 mm`, `OD 4.0 mm`, 4 in "
                    "`upper_shell` corner bosses — shared GBA BOM part)"
                ),
                "spec": "Ruthex RX-M3x5.7",
                "qty": 4,
            },
            {
                "item": (
                    f"M3 x {D.CORNER_SCREW_L:.0f} DIN 912 socket-head cap screw (A2-70, 4 corner "
                    "enclosure bolts; length checked by J01_SCREW)"
                ),
                "spec": f"M3 x {D.CORNER_SCREW_L:.0f} DIN 912 SHCS",
                "qty": 4,
            },
            {
                "item": (
                    "2.0 mm Clear Cast Acrylic sheet blank (`>= 35 x 25 mm`) + Cricut adhesive "
                    "vinyl (Matte Black background + Red/Blue/Green/Yellow/White N64 logo)"
                ),
                "spec": "2.0mm Clear Cast Acrylic + Cricut vinyl",
                "qty": 1,
            },
        ],
    },
]


def generate_markdown() -> str:
    lines = [
        "# N64 Classic Mini — Complete Bill of Materials (BOM) & Buyer's Guide",
        "",
        "Generated programmatically by `./run bom` (`lib/bom.py`).",
        "",
        "## Buyer's Guide: Radxa X4 SBC, M.2 2230 Storage, Shared GBA Hardware & Workshop Notes",
        "",
        "### 1. Which Radxa X4 Board to Buy",
        (
            "- **Recommended Model:** **Radxa X4 4GB (`RS119-D4E0`) or 8GB (`RS119-D8E0`), "
            "WITHOUT eMMC, WITHOUT pre-soldered 40-pin GPIO header**."
        ),
        (
            "- **Why 4GB / 8GB RAM:** Batocera Linux + Mupen64Plus-Next (`GLideN64` / "
            "`ParaLLEl-RDP` at 1080p60) uses `< 1.5 GB` RAM total. The **4GB LPDDR5** model "
            "(`~$50–$58`) has over `2.5 GB` of free headroom; choose **8GB** (`~$65`) only if you "
            "also plan to run heavier emulators or texture packs."
        ),
        (
            "- **Why NO pre-soldered 40-pin GPIO header:** Ordering the bare-pad (`H0`) version "
            "saves desoldering the 40-pin header and leaves clean through-hole pads for soldering "
            "the `Omron SS-5GL` `POWER`/`RESET` switches and the 3-lead bi-colour Red/Green LED."
        ),
        (
            "- **Why Upside-Down Mounting (Heat Sink Facing UP `+Z`):** On the Radxa X4, the Intel "
            "Processor N100 lives on the underside of the PCB. Mounted inverted (`180 deg` roll "
            "about `+X` at `Z = 8.20 mm`), the N100 and its pin-fin heat sink face up into the "
            "dome. A 30 mm fan under the 25 top louvers blows room air down through the pins; it "
            "leaves through the floor vents, waist slots and rear slits (`subassembly/"
            "cooling_check.py` computes the junction temperature from the measured openings)."
        ),
        "",
        "### 2. Which M.2 SSD to Buy & Storage Space Needed",
        (
            "- **Required Form Factor:** **M.2 2230 NVMe PCIe Gen3 x4 SSD** (`22 mm wide x "
            "30 mm long`, M-key — same compact size used in Steam Deck / ROG Ally; **do not** "
            "buy 2280)."
        ),
        "- **Storage Math for N64 Classic Mini:**",
        "  - Each Nintendo 64 ROM (`.z64`) is **8 MB to 64 MB** (average `~24 MB`).",
        (
            "  - The **entire official North American / PAL N64 library (296–388 games)** is only "
            "**~6.5 GB**."
        ),
        (
            "  - Adding Batocera Linux OS (`~4 GB`) + 1080p box art, cartridge textures, and "
            "preview videos (`~2.5 GB`) brings a **complete every-N64-game build to ~13 GB total**."
        ),
        (
            "- **Recommended Capacity:** **64 GB or 128 GB M.2 2230 NVMe** (e.g. *Kioxia BG4 / "
            "BG5 128GB M.2 2230*, *WD PC SN530 / SN740 128GB M.2 2230*, or *Sabrent Rocket 2230*, "
            "`~$15–$22`)."
        ),
        "",
        "### 3. Shared GBA BOM Parts: `Omron SS-5GL` Buttons & `Kingbright L-93WEGW` LED",
        (
            "- **Momentary `POWER` (`J-03`) & `RESET` (`J-04`) Buttons with `Omron SS-5GL`:** "
            "Both top-deck buttons use the exact same smooth cylindrical-crowned stadium profile "
            "(transverse slider nub removed from `POWER`) and actuate `2x Omron SS-5GL` "
            "microswitches (`0.49 N` operating force, `OP = 8.8 +/- 0.8 mm`). Each switch is "
            "located on a `Ø2.20 mm` pin (Hole 1, `0.075 mm/side` fit) and clamped to its tower "
            "by a `3 x 10` thread-forming screw driven from behind into Hole 2 (C2). "
            "Each button presses its switch lever through a ridge under its centre, 72% along "
            "the lever (C3), with `2.10 mm` of travel to front-and-rear stops and `Ø2.80 mm` "
            "anti-tilt guide poles on `usb_retainer_bracket.py`: every switch across the full "
            "`OP = 8.0..9.6 mm` band releases at rest and clicks before the stop (`OMRON_ACT`)."
        ),
        (
            "- **Dual-Colour Front LED (`Kingbright L-93WEGW`, 3 mm, `Green = ON`):** "
            "Wire **Pin 2 (Common Cathode)** to `GND` (header pin 9), **Pin 1 (Red Anode)** via "
            "`330 Ω` to `GP4` (pin 7), and **Pin 3 (Green Anode)** via `330 Ω` to `GP7` (pin 29) "
            "on the Radxa X4's RP2040 (`firmware/rp2040_reset/code.py`). The RP2040 only runs "
            "while the PC is on: red in Batocera's menu, green while a game runs, dark in standby "
            "(C7; the launch wrapper tells it which over USB serial)."
        ),
        (
            "- **Hard Power-Off Resilience (Pulling the Plug Without Safe Shutdown):** Batocera's "
            "root OS (`/boot/batocera`) is a read-only SquashFS image in RAM that cannot be "
            "corrupted by a sudden power cut; `n64mini.console.suspend` flushes save states with "
            "`os.fsync()` before atomic `replace()`, ignores `0`-byte interrupted files, and "
            "`n64mini-service.sh` cleans up any orphaned `.tmp`/`.pending` files on boot. Set BIOS "
            "`Chipset -> PCH-IO Configuration -> State After G3 -> S0` (or `Last State`) "
            "if switching power at the wall socket."
        ),
        "",
        "### 4. Clear Acrylic Front Jewel (`front_bezel.py`) with Diode Laser + Cricut",
        (
            "- Cut `export/bezel_laser_jig/bezel_laser_jig_0.svg` out of `3.0 mm` birch plywood on "
            "your diode laser. Clamp a rough piece of `2.0 mm` clear cast acrylic under the "
            "`24.14 x 15.50 mm` plywood window to score/flush-trim the acrylic to exact size, "
            "then drop the clear acrylic face-down into the same plywood window to align and stick "
            "the Cricut-cut N64 vinyl decal onto the flat `+Y` back face before gluing into "
            "`upper_shell`."
        ),
        "",
    ]
    rollup: dict[str, dict[str, Any]] = defaultdict(lambda: {"item": "", "qty": 0})
    for sub in SUBASSEMBLIES:
        lines.append(f"## {sub['title']}")
        lines.append("")
        lines.append("### Fabricated Parts (FDM 3D Print / Diode Laser / Clear Acrylic)")
        lines.append("")
        lines.append("| Part | Material | Qty |")
        lines.append("|---|---|---:|")
        for p in sub["printed"]:
            lines.append(f"| {p['part']} | {p['material']} | {p['qty']} |")
        lines.append("")
        lines.append("### Bought Hardware & Electronics")
        lines.append("")
        lines.append("| Item | Specification | Qty |")
        lines.append("|---|---|---:|")
        for b in sub["bought"]:
            lines.append(f"| {b['item']} | `{b['spec']}` | {b['qty']} |")
            entry = rollup[b["spec"]]
            entry["item"] = b["item"]
            entry["qty"] += b["qty"]
        lines.append("")

    lines.append("## Master Bought-Hardware Rollup")
    lines.append("")
    lines.append("| Specification | Description | Total Qty |")
    lines.append("|---|---|---:|")
    for spec in sorted(rollup):
        lines.append(f"| `{spec}` | {rollup[spec]['item']} | {rollup[spec]['qty']} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    md = generate_markdown()
    with open(BOM_MD_PATH, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Wrote {BOM_MD_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
