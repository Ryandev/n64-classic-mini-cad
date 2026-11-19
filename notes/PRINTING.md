# Printing: the printer, PETG, supports and measured fits

Read this before slicing anything. Most of it was learned the hard way on the owner's GBA project
(`C:\Users\ryan\Documents\GBA\CAD`), which uses the same printer and the same PETG. Its sources
are named in brackets: `PRINTING.md` is `GBA/CAD/lib/slicing/PRINTING.md`, `TOLERANCES.md` is
`GBA/CAD/notes/TOLERANCES.md`, G1–G13 are in `GBA/CAD/notes/TODO.md`, and dated entries are in
`GBA/CAD/history/DECISIONS.md`. Process details (layer heights, walls, inserts, assembly) are in
[`MANUFACTURING.md`](MANUFACTURING.md); design fit classes are in [`TOLERANCES.md`](TOLERANCES.md).

## The printer

**Bambu X2D**, two nozzles.

| | |
|---|---|
| Left nozzle | the AMS (PETG) |
| Right nozzle | the external spool (PLA, AMS id 255); it can't reach x < 20.5 |
| Bed, one nozzle | 256 x 256 mm |
| Bed, both nozzles | **235.5 x 256 mm** (G9) |
| Chamber | 65 °C active. **Run it cool for PETG**: 65 °C is for ASA/ABS, and PETG goes soft there |

## Materials

**SLA Tough Resin for all visible, carrier, button and shell parts; PETG Basic only for the 3 internal cooling parts** (`cooling_duct`, `duct_floor`, `cooling_hood`, which clamp directly onto the `60–70 °C` heat sink; owner decision 2026-11-18). Clear SLA Resin (`JLC3DP 8001`) for the light pipe. FDM fit coupons (`./run coupons`) use PETG Basic with a PLA support interface (below).

| Considered | Why / Where used |
|---|---|
| **SLA Tough Resin** (`JLC3DP Imagine Black / 9600` or `PCBWay`) | **Used for all 11 visible, carrier, button and shell parts** (`upper_shell`, `lower_tub`, `front_io_carrier_l`/`_r`, `usb_retainer_bracket`, `front_port_cover`, `n64_port_insert`, `power_slider`, `reset_button`, `cartridge_flaps`, plus `8001 Clear Resin` for `led_light_pipe`). Gives crisp `0.08 mm/side` oblong button guide fit (`SLEEVE_CLEAR`) and smooth outer surfaces with no FDM layer lines |
| **PETG Basic** (`Bambu Lab X2D`) | **Used for the 3 hidden cooling parts** (`cooling_duct`, `duct_floor`, `cooling_hood`) that sit on the `60–70 °C` heat sink, plus rapid fit-test coupons |
| PLA in the console | softens at about 55 °C, below the heat sink's 60–70 °C (GBA rejected it too) |
| PETG-CF | stiffer and flatter, but brittle at thin pins and hinges, a fibrous finish, a hardened nozzle |

**Dry the PETG and the PLA interface spool** before use (G10).

## Printing for paint (fewer layer lines to sand)

- **Orientation does most of it.** A shallow slope printed face-up terraces in rings (about
  0.2 mm / tan(slope) wide per layer); the same surface printed as a wall comes out smooth (GBA's
  d-pad cross, DECISIONS 10-30). Check how each visible face prints before a full part.
- **Variable layer height** in Bambu Studio: 0.08 mm on the shell's sloped deck and domes,
  0.2 mm elsewhere.
- **Ironing** on flat top faces; **seam** at a rear corner, away from the faces that show.
- **2K high-build filler primer**, 3–5 coats sanded back. 1K primer shrinks back and the layer
  lines reappear weeks later (GBA `MANUFACTURING.md`).
- **Paint closes gaps, so painted fits are drawn open** (owner, 2026-11-13: everything visible
  painted, no masking). One datum, `PAINT_T` = 0.15 mm per face (basecoat + clear on unsanded gap
  edges, from GBA's film figures; **provisional until a painted coupon is measured**). Each
  painted fit is drawn at its working clearance plus the paint it gains, and the gate's
  `PAINT_FIT` row measures every one on the solids:

  | Fit | Faces painted | Drawn | After paint |
  |---|---|---|---|
  | port door in its bay | both | 0.50 | 0.20 |
  | cartridge flaps in their pocket | both | 0.45 | 0.15 |
  | clear jewel in its pocket | pocket only | 0.30 | 0.15 |
  | clear LED lens in its window | window only | 0.25 | 0.10 |

  The **buttons are not opened**: their sliding faces are hidden inside the chimneys, so spray the
  shell with the buttons out and each button's top held by its stem. If they bind after paint,
  raise `RESET_CLEAR`/`SLIDER_CLEAR` by `PAINT_T`. **Coupons are cut from the painted design**:
  paint coupon 3 before judging the door fit (unpainted it is 0.3 mm looser on purpose).

## Manufacturing profiles: design nominal, allowances at print time

The CAD is the design at true size, with every fit drawn as the finished gap (owner, 2026-11-15).
What a process does to sizes lives in `lib/process/profiles.py`, one profile per material on a
machine, and is added at print time, so a part changes process by changing its `PROFILE`, never
its geometry. A profile's allowances come only from measured prints; `process/profile_check.py`
fails any made part with no profile, or whose profile has no measurement behind it.

| Profile | Holes (per side) | Outside faces (per side) | Measured from |
|---|---|---|---|
| `fdm_petg_x2d` | print 0.22 mm small | up to 0.05 mm big (one face came out 0.15 small) | coupon plate 1 button and shell chimney, owner 2026-11-15 |
| `resin_mars` | not yet measured | not yet measured | print one resin button first |

**Slice with `./run slice NAME PROFILE [--support hidden|visible] STL...`** (`lib/slicing/bambu.py`).
It puts the profile's allowances into Bambu's `xy_hole_compensation` / `xy_contour_compensation`
(+0.22 / −0.05 for `fdm_petg_x2d`), uses the X2D settings proven on the owner's prints, tree
supports for hidden faces and normal supports under a continuous PLA interface for visible ones,
and refuses its own output unless the file's settings say all of that (`slicing/slice_check.py`
holds the refusal to coupon plate 3, sliced before any of this with both compensations at 0).

Don't bake these into the CAD (a hole drawn big "so it prints right"): it ties the part to one
process. Audit 2026-11-15: the switch-tower screw holes (drawn Ø3.0 to print ~Ø2.67) went back
to nominal Ø2.6. The one FDM-specific feature left in the CAD is the two-layer bridge over the
tub's corner counterbores (`part/lower_tub.py`, steps of `LAYER_MM`): it sets no size or fit,
and a resin print just reproduces the steps.

## Supports

**The design aims to need none, and nothing is sliced with supports off unless the overhang row
passes it.** The row (`lib/process/printable.py`) slices the part in 0.2 mm layers and finds what each layer
prints past the layer below (beyond the 50° step). That still prints if it is within half a line
(0.21 mm) of a hold, or bridges (one direction in which every line across it is held at both ends,
no longer than 10 mm: windows, pocket ceilings, holes closed over, the two-layer counterbore
bridge), or lies in the first 1.0 mm and is no wider than a bridge, where it can only sag onto the bed. Anything else (a peg, a
pin, a skin stepping out layer after layer, a ring round a hole, a start in mid-air) needs support.
A part may declare `SUPPORT_MM2` (projected area) with the reason; the row fails if it needs more.

`print_outcome_check.py` holds the row to a real print, coupon plate 1 (2026-11-14, no supports):
the bracket peg, the switch V-pin, the button printed on its side and the cut-out shell skin
failed, and the row says so for exactly those four. The 1.0 mm bed limit sits between the
upright button's lever pocket (0.8 mm up, clean) and the side-printed button's cap (1.3 mm, failed).

Declared as of 2026-11-14, all measured by layers and all inside the console or inside an opening:

| Part | Declared (measured) | Where | Why it's acceptable |
|---|---|---|---|
| `upper_shell` | 9,010 mm² (8,490) | inside of the top deck | printed split-face down, the deck is a roof over the hollow shell; that face is hidden |
| `cooling_hood` | 900 (853) | stepped wall tops, closed top | inside the console |
| `cooling_duct` | 480 (456) | fan seat ring round the bore, plate-frame ledge | inside; reached through the fan bore and the floor opening. The floor itself is the separate `duct_floor` (owner, 2026-11-13) |
| `lower_tub` | 40 | rear port-opening tops, LED hole top | inside openings (the switch V-pins went on 2026-11-15: two screws per switch instead) |
| `usb_retainer_bracket` | 10 (10.0) | the sideways `2.8 x 4.2 mm` oblong guide pole | hidden, and the button's oblong sleeve (`3.1 x 4.5 mm`) slides on it with 0.15 mm a side (checked on coupon plate 7, 2026-11-18) |
| `power_slider`, `reset_button` | 125 (116) each | the flange's underside round the guide sleeve | printed crown up, standing on the sleeve; the underside is hidden and only the switch lever touches it (~0.10 mm proud costs 0.10 of the 0.26 mm release margin) |
| everything else | 0 | | prints support-free by the row |

The lower-tub corner counterbores open on the bed and close with the two-layer bridge (a slot
the hole's width, then a square), so they need none.

When a part does need support, use the GBA set-up (`PRINTING.md`, DECISIONS 10-18 and 10-30):

- **PETG support body, PLA interface.** PLA barely bonds to PETG, so the support lifts off
  clean. PETG-on-PETG supports weld on: the face comes out rough and stringy, and mating parts
  don't fit (G5; dovetail coupon 11-10).
- **Tree supports, build plate only**, so the PLA stands on the bed. PLA laid *onto* a PETG face
  keys into it for good; PETG laid onto PLA lets go (06b, 10-29).
- **Tree supports only suit hidden faces.** Each branch tip gets its own PLA interface patch, so a
  large supported face prints partly onto PLA and partly onto air between patches, and areas no
  branch can reach from the bed get nothing. Coupon plate 3 (2026-11-15): the inside of the shell
  corner (a ~57° face) came out rough. Fine where it is hidden. **For any supported face with a
  user-facing finish**, slice with normal (grid) supports and a solid, full-coverage PLA
  interface, so the PETG prints onto one continuous PLA surface (owner, 2026-11-15).
- **Always enable the prime tower** (`enable_prime_tower = 1`, at 200, 210). Only the left nozzle
  primes on layer 1. Without the tower, the right nozzle's first interface layer extrudes air and
  the overhang above it turns to spaghetti (11-10).
- Check `filament_map` is `1,2` (PETG left, PLA right). Run the nozzle-offset calibration before the
  first two-material print, and clean the calibration plate and both tips after purging.
- **Visible faces never sit on support.** Orient for the faces the user sees first.
- **Never let support fill a bore that something slides in** (G12): here, the button sleeves
  and the door hinge holes.
- **A face printed on support comes out about 0.10 mm proud.** Give each supported mating face an
  extra 0.10–0.12 mm of clearance (TOLERANCES.md §4, class 3).

## Bed adhesion and stringing

- **Brims:** 12 mm on any part over 150 mm, kept at least 10 mm from the bed edge. A big flat
  part lifted at its corner nearest the bed edge, even with a brim (G4). Ours are 130 mm or less,
  but keep the tub and shell away from the bed edges.
- **Look at how a part meets the bed.** A small pad under a big part lifts. The tub's underside
  is flat for this reason (C9, 2026-11-13).
- **Stringing** came from travel across holes and around supports, not from nozzle temperature:
  250/245/240/235 °C all printed clean (G6). Watch the louvres and the port openings.

## Fits measured on the GBA prints (PETG, 0.4 mm nozzle, 0.20 mm layers)

From GBA `TOLERANCES.md` §4 (measured 2026-11-08..10). These are real prints from this printer,
so they outrank the generic ±0.2 mm in our `TOLERANCES.md`.

| Measured | Lesson |
|---|---|
| A Ø10.03 vertical bore printed at **Ø9.70** (−0.33 mm) | holes print small: draw them oversize |
| Holes under Ø2 shrink about **0.4 mm** | small holes need much more clearance |
| A printed shaft in a printed bore at 0.10 mm/side dragged on the layer lines | sliding fits: **0.18–0.22 mm/side** |
| A support-free dovetail at 0.10–0.14 mm/side slid nicely | locating fits: 0.10–0.14 mm/side |
| The same dovetail printed on a PLA interface locked solid | +0.10–0.12 mm for each supported face |
| Printed nubs in printed holes: Ø1.08 in Ø1.70, Ø2.00 in Ø2.70 | small locators: 0.31–0.35 mm/side, glued |
| A Ø3.0 steel dowel: press fit at Ø3.01, slip fit at Ø3.05 | |
| M3 x 5.7 Ruthex inserts in Ø4.0 bores | fine |

### Our fits against those results

| Fit | Drawn | Verdict |
|---|---|---|
| Button in its chimney | 0.22 mm/side | matches the proven sliding fit |
| Shell lip over the tub | 0.15 mm/side | in the proven locating range |
| M3 inserts, corner bosses | Ø4.0 nominal (Ø4.3 slip-fit for cold-glued SLA resin) | same as GBA |
| M2.5 inserts, standoffs & front floor bosses | Ø3.2 nominal (Ø3.6 slip-fit for cold-glued SLA resin) | coupon 4 |
| M2.5 switch screws in the tower | Ø2.6 nominal, compensated at slicing | coupon plate 3 (2026-11-15): screws into the switch well; a little play in the tower hole (minor, owner) |
| Door hinge: `Ø1.5 x 27.4 mm` steel pin in the door centre knuckle and carrier hinge barrels | Ø1.5 pin: Ø1.8 where it turns in the door, Ø1.5 press in outer carrier barrel, Ø1.6 close fit in inner carrier barrel | 3-knuckle barrel hinge inside the 28.40 mm bay opening (through-bored for bench assembly/disassembly) |
| Magnets in their pockets | Ø3.0 in Ø3.2 nominal pocket (45-deg roofed on horizontal pockets) | coupon plate 6 (2026-11-18): vertical holes (`6_hole_gauge_plate_downward`) printed at **3.1 x 3.2** (Ø3.2 drawn), **3.4 x 3.4** (Ø3.4), **3.7 x 3.7** (Ø3.6); sideways holes (`6_hole_gauge_wall_sideways`) printed at **3.0 x 2.8** (Ø3.2), **3.2 x 2.7** (Ø3.4), **3.4 x 3.1** (Ø3.6) |

## Prove it small first

GBA's whole first black-PETG run went straight to full size and had to be reprinted (G8, "prove it
small before printing it big"). Here, `./run coupons` cuts print-test coupons from the real parts
into `export/coupons/`; print them before any full part. A stepped gauge (three sizes of one hole)
settles a size in one print. Record what each coupon showed in this file.
