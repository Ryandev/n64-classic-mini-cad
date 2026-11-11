# N64 Classic Mini — Enclosure & Mechanical CAD (`cad/`)

Parametric CadQuery enclosure and internal mechanisms for the **N64 Classic Mini** (50% scale Nintendo 64 console built around the **Radxa X4** Intel N100 SBC).

Architecture, fitment trade-offs, and mechanical split are specified in the owner's research notes (local only, `docs/references/research/03-compute-module-and-case-design.md`). Workflow, gate runner, design rules, and tolerance register are adapted from the sibling GBA CAD project.

---

## Coordinate Frame

Every part, subassembly, and assembly check uses one right-handed tabletop frame (`det == +1`):

| Axis | Direction | Origin (`0, 0, 0`) |
|---|---|---|
| **`+X`** | **Right** across the front of the console (`-65.00 .. +65.00 mm` at 50% scale; P1/P2 left, P3/P4 right) | Left-right centreline |
| **`+Y`** | **Rear** into the console (`-49.94 mm` front pod tangent to `+49.94 mm` rear bowed wall) | Front-to-rear centreline |
| **`+Z`** | **Up** from the desk/foot reference plane (`0.00 mm` bottom plane to `+33.50 mm` top of centre dome) | Bottom of lower tub |

All linear dimensions in code are **millimetres (`mm`)**. Angular constants carry a `_DEG` suffix.

---

## Requirements

Each requirement is enforced by a mechanical check row in `lib/gate.py` (`./run gate`) and mutation-tested by `lib/gate_selftest.py` (`./run selftest`).

| ID | Requirement | Enforced by |
|---|---|---|
| **REQ-01** | **50% Scale Proportions & Authentic Silhouette:** Outer shell envelope matches 50% scale of `Console_N64.step` (`260.00 x 199.76 x 67.00 mm` -> `130.00 x 99.88 x 33.50 mm`, `SPLIT_Z = 12.94 mm`), with twin protruding `R = 12.50 mm` front corner pods, `120.00 mm` recessed waist, `R = 5.00 mm` convex front-pod domes, `10.275 deg` sloped wing decks, `33.50 mm` convex front barrel dome, 25 parabolic saddle louvers, and concave rear cartridge cradle verified by ray-casting against `lib/step/n64_shell.py`. | `lib/assembly/datum_check.py` (`SCALE`, `SCAN_50`), `lib/assembly/console_check.py` (`SH_OUTSIDE`) |
| **REQ-02** | **Right-Handed Tabletop Frame:** Coordinate transforms and placement maps have determinant `+1` (no reflections that mirror port order or board connectors). | `lib/assembly/datum_check.py` (`HANDED`) |
| **REQ-03** | **Radxa X4 Fitment & Standoffs:** De-ported Radxa X4 (`lib/step/radxa_x4.py` -> `lib/variant/radxa_x4.py`, `85.0 x 56.0 mm`, `4x Ø2.7 mm` mounting holes on `58.0 x 49.0 mm` rectangle, 6 tall headers stripped) mounts inverted (`180 deg` roll about `+X`) on 4 standoffs (`6.6 mm` posts for `5.53 mm` M.2 2230 NVMe SSD, shifted `-5.5 mm` in `X` and flush against the `+Y` rear wall at `Y_centre = +18.80 mm`) inside the `120.0 mm` N64 waist. | `lib/assembly/datum_check.py` (`RADXA_FIT`), `lib/subassembly/radxa_mount_check.py` (`VARIANT`, `HEADERS`, `J02_SEAT`, `M2_CLEAR`) |
| **REQ-04** | **Vertical Thermal Stackup:** Inverted Radxa X4 + upward-facing milled finned aluminium SoC heatsink (`lib/step/radxa_heatsink.py` -> `lib/variant/radxa_heatsink.py`, `Z = 9.80 .. 20.20 mm`) clears the `33.50 mm` centre dome interior with `>= 8.0 mm` breathing plenum beneath the parabolic dome & rear exhaust vents. | `lib/assembly/datum_check.py` (`THERMAL`), `lib/subassembly/radxa_mount_check.py` |
| **REQ-05** | **Rear I/O Bay:** Rear panel (`+Y`) exposes the flush-rear Radxa X4 Micro-HDMI, USB-C PD power, and 3.5mm audio jacks plus a `>= 20.5 mm` wide bay on `+X` for the panel-mount RJ45 Ethernet jack. | `lib/assembly/datum_check.py` (`REAR_IO`) |
| **REQ-06** | **Twin-Port Front Controller Covers, Shallow N64 Port Inserts & Clear PETG LED Light Pipe:** Front face (`-Y`) accommodates `4x` `TE Connectivity 292303-7` horizontal USB-A controller ports concealed behind twin bottom-hinged covers (`Left P1+P2` at `X = -25.0 mm`, `Right P3+P4` at `X = +25.0 mm`, preserving the untouched `21.60 mm` central front apron), carrying `4x` separately-printed Light Cool Grey N64 controller port inserts (`n64_port_insert.py`, `Ø10.88 mm`, `J-08`) and flanking the central Clear PETG lenticular Power LED light pipe (`led_light_pipe.py`, `6.36 x 1.76 mm`, `J-07`) + 3-lead bi-colour Red/Green LED (`Kingbright L-819EGW`, `Red = Power`, `Green = ON`). | `lib/assembly/datum_check.py` (`FRONT_USB`), `lib/subassembly/front_panel_check.py` (`J05_COVER`, `J07_PIPE`, `J08_PORT`) |
| **REQ-07** | **Clear Acrylic Front Jewel & Diode-Laser Plywood Jig:** Central untouched front apron carries a flush curved pocket (`J-06`) for the `24.14 x 15.50 x 2.00 mm` Clear Cast Acrylic front jewel (`front_bezel.py`, backed by a Cricut vinyl N64 sticker), accompanied by a diode-laser birch plywood cutting & alignment jig (`bezel_laser_jig.py`). | `lib/assembly/datum_check.py` (`CONTROLS`), `lib/subassembly/top_controls_check.py` (`J06_BEZEL`) |
| **REQ-08** | **Momentary Power & Reset Buttons (`Omron SS-5GL`, `AC-T18`) & Cartridge Flap Insert:** Upper deck provides sculpted concave thumb wells and `0.22 mm/side` stadium bores for the momentary Light Cool Grey `POWER` (`J-03`) and `RESET` (`J-04`) buttons (sharing the exact same smooth `R = 19.391 mm` cylindrical-crowned stadium button profile with the slider nub removed from `POWER`) atop `2x Omron SS-5GL` subminiature hinge-lever microswitches (`OP = 8.8 +/- 0.8 mm`, `r = 0.72`, `M3 x 6 ISO 4026` bottom-stop set screws in `Ruthex RX-M3x5.7` inserts), plus a recessed cartridge throat pocket (`J-09`) for the separately-printed Light Cool Grey dual cartridge dust-flap insert (`cartridge_flaps.py`). | `lib/assembly/datum_check.py` (`CONTROLS`), `lib/subassembly/top_controls_check.py` (`J03_SLIDE`, `J04_RESET`, `OMRON_ACT`, `J09_FLAPS`) |
| **REQ-09** | **Multi-Piece Colour Split:** Parts separate cleanly by colour and print orientation without multi-material AMS requirement (`Charcoal Grey` upper shell, lower tub & twin port covers; `Light Cool Grey` cartridge flaps, Power/Reset caps & `4x` controller port inserts; `Clear PETG` LED light pipe; `Clear Cast Acrylic + Cricut decal` front jewel; `Birch Plywood` diode-laser jig). | `lib/testing/export_validate.py` (`DECLARED`) |
| **REQ-10** | **Joint Register & Single-Datum Rule:** Every mating pair names one datum feature per axis in [`notes/TOLERANCES.md`](notes/TOLERANCES.md); all other features on that axis carry explicit clearance beating the process stack. | `lib/assembly/datum_check.py` (`JOINT_REGISTER`) |
| **REQ-11** | **Process & Bed Limits:** Every FDM part fits the `256 x 256 x 256 mm` print volume, maintains `>= 0.8 mm` local wall (`>= 1.5 mm` structural shell wall), and passes `lib/printable.py` (`manifold`, `single_body`, `footprint`, `wall`). | `lib/subassembly/radxa_mount_check.py`, `lib/testing/export_validate.py` |
| **REQ-12** | **Checks Can Fail (MFIC):** Every check module in `lib/subassembly/` and `lib/assembly/` is paired with a mutation in `lib/gate_selftest.py` proving the gate turns red when a geometric defect is planted. | `lib/gate_selftest.py` |
