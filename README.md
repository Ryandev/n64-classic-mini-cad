# `n64-classic-mini-cad` — 50%-Scale Parametric CadQuery Enclosure for the Radxa X4

[![CAD CI & STEP Export](https://github.com/Ryandev/n64-classic-mini-cad/actions/workflows/ci.yml/badge.svg)](https://github.com/Ryandev/n64-classic-mini-cad/actions/workflows/ci.yml)

A 100% parametric **CadQuery (OpenCASCADE B-Rep)** enclosure reproducing the classic 64-bit console silhouette at **exact 50% linear scale (`130.0 x 99.9 x 33.5 mm`)**, engineered around an inverted **Radxa X4 (`Intel Processor N100`)** single-board computer, 4 front USB-A controller ports hidden behind magnetic hinged doors, tactile **`Omron SS-5GL`** microswitches under both **`POWER`** and **`RESET`** with coaxial anti-tilt guide poles, and a `Kingbright L-93WEGW` dual-colour front status LED.

The case is checked by **155 geometry, interference and printability gate rows** (`./run gate`, which needs the reference models listed under [External sources](#external-sources)) and a first-pass FEM run (`./run fem`, see the caveat below).

---

## Downloads

Every push to `main` lints the code, builds every printed part and the print plate
([`.github/workflows/ci.yml`](.github/workflows/ci.yml)), and publishes them to the
**[latest release](https://github.com/Ryandev/n64-classic-mini-cad/releases/latest)**:

| File | Download | Contents |
|---|---|---|
| `print_plate.step` | [print_plate.step](https://github.com/Ryandev/n64-classic-mini-cad/releases/latest/download/print_plate.step) | All 15 printed bodies on one plate (`240.6 x 229.0 x 23.5 mm`), laid flat on `Z = 0` for a `256 x 256 mm` bed |
| `n64-classic-mini-cad-exports.zip` | [n64-classic-mini-cad-exports.zip](https://github.com/Ryandev/n64-classic-mini-cad/releases/latest/download/n64-classic-mini-cad-exports.zip) | Each printed part as its own STEP, the laser jig SVG, the print plate, the BOM, manufacturing and tolerance notes, `LICENSE` and `CREDITS.md` |

The geometry gate (`./run gate`) and the full console assembly check the case against
third-party models that are not in this repository (see [External sources](#external-sources)),
so they run on the maintainer's machine, not in CI.

---

## 🔗 N64 Classic Mini — Sister Repositories

| Repository | Role | Latest Build Download |
|---|---|---|
| **[`Ryandev/n64-classic-mini-cad`](https://github.com/Ryandev/n64-classic-mini-cad)** *(this repo)* | 50%-scale (`130 x 99.9 x 33.5 mm`) parametric CadQuery enclosure, Gmsh + CalculiX 3D FEM structural verification, single-plate STEP export & BOM | [`n64-classic-mini-cad-exports.zip`](https://github.com/Ryandev/n64-classic-mini-cad/releases/latest/download/n64-classic-mini-cad-exports.zip) / [`print_plate.step`](https://github.com/Ryandev/n64-classic-mini-cad/releases/latest/download/print_plate.step) |
| **[`Ryandev/es-theme-n64-classic-mini`](https://github.com/Ryandev/es-theme-n64-classic-mini)** | Batocera EmulationStation theme, 4-slot `Suspend Point List` cartridge drawer, native PC port installer, RP2040 Reset/LED firmware & theme validator | [`n64-classic-mini-theme.zip`](https://github.com/Ryandev/es-theme-n64-classic-mini/releases/latest/download/n64-classic-mini-theme.zip) |
| **[`Ryandev/n64-classic-mini-music`](https://github.com/Ryandev/n64-classic-mini-music)** | The theme's original menu music: an upbeat 32-bar loop synthesised in Python with N64-style voices | [`theme.wav`](https://github.com/Ryandev/n64-classic-mini-music/releases/latest/download/theme.wav) |

---

## Pictures

| Front | Rear: vents and I/O |
|---|---|
| ![Front isometric](notes/screenshots/cad_front_iso.png) | ![Rear isometric](notes/screenshots/cad_rear_iso.png) |

| Inside: the inverted Radxa X4, USB-A retainers and button guides | First-pass FEM (von Mises stress) on the USB retainer |
|---|---|
| ![Internal cutaway](notes/screenshots/cad_internal_cutaway.png) | ![FEM von Mises stress](notes/screenshots/cad_fem_stress.png) |

The print plate: all 15 printed bodies (`240.6 x 229.0 x 23.5 mm`).

![Print plate](notes/screenshots/cad_print_plate.png)

---

## Rear plaque lettering

The rear oval plaque on `upper_shell.py` is engraved with the generic word **`CLASSIC`**
(`PLAQUE_TEXT` in [`lib/part/shared/n64_text.py`](lib/part/shared/n64_text.py), set in the
bundled DejaVu Sans Bold). To engrave your own lettering in a local build, change `PLAQUE_TEXT`,
or put traced glyph outlines in a git-ignored `local/nintendo_glyphs.py` (a `NINTENDO_GLYPHS`
tuple of `(outer, inner_loops)` polylines); the build uses that file whenever it exists.

For the front nose jewel (`front_bezel.py`), cut `bezel_laser_jig/bezel_laser_jig_0.svg` (in the release's `n64-classic-mini-cad-exports.zip`, or from `./run export`) from `3.0 mm` birch plywood on a diode laser to flush-trim `2.0 mm` clear cast acrylic and register your own Cricut-cut vinyl decal on the flat `+Y` back face.

---

## 🔬 3D Tetrahedral FEM Structural Verification (`./run fem`)

[`lib/testing/fem_check.py`](lib/testing/fem_check.py) meshes the actual B-Rep solids with
**Gmsh** (10-node `C3D10` tetrahedra) and solves 4 linear-elastic load cases in **CalculiX**
(PETG, $E = 2200\,\text{MPa}$, $\nu = 0.36$). Each case is solved on two meshes (the second
`0.7x` finer) and must agree within 15 %. Stress is judged at the 99th percentile of the points
clear of loads and supports, since point loads, clamps and the model's sharp inside corners are
true stress singularities whose maximum never converges. Supports follow the real console: the
tub rests on its floor, held sideways only under the rubber feet; the shell rests on the tub's
rim and is screwed at its 4 corners.

> **Status (2026-11-13 night, C4): not yet in the gate.** Each flex limit is now set by what the
> part has to do (owner: don't reinforce): the guide pole must not reach the button (0.57 mm), the
> button stop may give no more than the switch's guaranteed over-travel margin (0.158 mm), the
> chimneys must keep the button's sliding clearance (0.22 mm), and the standoffs must keep the rear
> jack's 0.5 mm from the wall. The dome sag is reported, not limited: the hood and fan under it
> aren't modelled. With the flat tub bottom the floor sits on the bed or desk, and the stop and
> standoff flex dropped from ~0.3 mm to 0.05 and 0.01 mm. Since the 2026-11-14 review, LC1 also
> grades the bracket's stop shelf on its own: it gives 0.18 mm under the 50 N mash, past the
> switch's 0.158 mm margin (an open decision, RELEASE_TODO E). LC1's stress sits in a sharp inside
> corner (the middle leg's root under the bridge), which is why it never converges; LC4's is
> 0.06 MPa. The FEM stays out of the gate until those are settled.

| Load Case | Component | Loads | von Mises (p99) | Deflection | Mesh change (stress / defl.) |
|---|---|---|---|---|---|
| **`FEM_LC1`** | `usb_retainer_bracket.py` | `50 N` button-stop mash, `15 N` sideways on the guide pole, `15 N` USB-A pry | `11.2 MPa` (limit 25), at the middle leg's root under the bridge | `0.30 mm` at the guide pole tip (limit 0.57); **stop shelf gives `0.18 mm` (limit 0.158, the switch's over-travel margin)** | **31 %** / 2 % |
| **`FEM_LC2`** | `lower_tub.py` front USB & Omron bay | `40 N` USB-A insertion, `30 N` cable yank, `50 N` button-stop mash | `3.0 MPa` (limit 20) | `0.05 mm` max (limit 0.158, the switch's over-travel margin) | 11 % / 11 % |
| **`FEM_LC3`** | `upper_shell.py` | `100 N` (~10 kg) on the dome | `5.2 MPa` (limit 25) | `0.78 mm` dome sag (reported only); chimneys `0.14 mm` (limit 0.22, the button clearance) | 6 % / 6 % |
| **`FEM_LC4`** | `lower_tub.py` Radxa & RJ45 standoffs | `30 N` rear plug push, `60 N` screw preload, on the 6 standoff tops | `0.06 MPa` (limit 15) | `0.01 mm` (limit 0.50, the jack's gap to the wall) | **23 %** / 2 % |

---

## 🛠️ Building, Testing & Documentation

```bash
./run all        # ruff lint + 155 B-Rep/printability gate rows + STEP/SVG/plate export + round-trip validation
./run fem        # 4 Gmsh + CalculiX C3D10 load cases, each on two meshes (~4 min)
./run selftest   # run 40 planted geometry mutations to prove every gate row can fail
./run bom        # regenerate notes/BOM_COMPLETE.md from parametric subassemblies
```

- **[Complete Bill of Materials & Buyer's Guide (`notes/BOM_COMPLETE.md`)](notes/BOM_COMPLETE.md)** — Exact SKUs for the Radxa X4 (`RS119-D4E0` / `RS119-D8E0`), M.2 2230 NVMe SSD, `Omron SS-5GL` switches, `Kingbright L-93WEGW` bi-colour LED, `TE 292303-7` USB-A jacks, and `Ruthex` heat-set inserts.
- **[Manufacturing, Heat-Set Inserts, GPIO Wiring & Assembly Guide (`notes/MANUFACTURING.md`)](notes/MANUFACTURING.md)** — Print settings, 40-pin GPIO solder-pad wiring table, and 8-step top-down assembly sequence.
- **[Joint Clearances & Tolerance Ledger (`notes/TOLERANCES.md`)](notes/TOLERANCES.md)** — Per-joint (`J-01`..`J-09`) clearance table and rationale.

## External sources

The case is modelled against third-party CAD files that are **not** included here. Download them
yourself if you want to run the reference checks:

- *Nintendo 64 console* by Bruno Amaral: <https://grabcad.com/library/nintendo-64-console-1>
- *Radxa X4 V1.11 3D model* by Radxa: <https://dl.radxa.com/x/x4/radxa_x4_3d_pcba.zip>
  (mirror: <https://grabcad.com/library/radxa-x4-1>)
- *Radxa X4 heatsink 3D model* by Radxa:
  <https://dl.radxa.com/accessories/heatsink-for-x4/radxa_heatsink_for_x4_3d.zip>
- *TE Connectivity 292303-7 USB-A* from KiCad's 3D library:
  <https://gitlab.com/kicad/libraries/kicad-packages3D>

Details are in [CREDITS.md](CREDITS.md).

## Licence

[CERN-OHL-P-2.0](LICENSE), © 2026 Ryan Powell. The bundled DejaVu font keeps its own licence
(`lib/part/shared/fonts/LICENSE-DejaVu.txt`).
