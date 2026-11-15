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

**Every printed part is PETG Basic** (owner, 2026-11-13: no PETG-CF, no ASA, no resin). Clear PETG
for the light pipe. PLA only as the support interface (below).

| Considered | Why not |
|---|---|
| PLA in the console | softens at about 55 °C, below the heat sink's 60–70 °C (GBA rejected it too) |
| ASA for the duct and hood | ~95 °C would give heat margin, but the owner keeps one material. PETG's ~70 °C is close to the heat sink, so the on-console thermal test (`n64mini.console.thermal_test`) should also check the duct holds its clamp |
| PETG-CF | stiffer and flatter, but brittle at thin pins and hinges, a fibrous finish, a hardened nozzle |
| Resin (PCBWay) plus paint | was for less sanding before paint; PETG printed for paint (below) instead |

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
| `lower_tub` | 48 (44) | rear port-opening tops, LED hole top | inside openings (the switch V-pins went on 2026-11-15: two screws per switch instead) |
| `usb_retainer_bracket` | 4 (3.5) | the sideways guide pole | clears the button by 0.57 mm a side, so 0.10 mm proud doesn't matter |
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
- **Never let support fill a bore that something slides in** (G12): here, the button pole holes
  and the door hinge sockets.
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
| M3 inserts, corner bosses | Ø4.0 | same as GBA |
| M2.5 inserts, standoffs | Ø3.2 | **untested** anywhere: coupon 4 |
| M2.5 switch screws in the tower | Ø3.0 drawn | coupon plate 3 (2026-11-15): screws into the switch well; a little play in the tower hole (minor, owner). Ø2.8 drawn would tighten it. (The Ø2.2 V-pin fitted the switch hole well, slight resistance, but left the switch no way in: removed 2026-11-15) |
| Door hinge pins in their sockets | Ø1.8 in Ø2.4 (0.30 mm/side) | **at risk**: a small hole; at −0.4 mm it leaves ~0.1 mm/side and may bind. Coupon 3 |
| Magnets in their pockets | Ø3.0 in Ø3.2 (0.10 mm/side) | **at risk**: at −0.3 mm the pocket is ~Ø2.9 and the magnet won't go in. Not yet measured on GBA either. Coupon 3 |

## Prove it small first

GBA's whole first black-PETG run went straight to full size and had to be reprinted (G8, "prove it
small before printing it big"). Here, `./run coupons` cuts print-test coupons from the real parts
into `export/coupons/`; print them before any full part. A stepped gauge (three sizes of one hole)
settles a size in one print. Record what each coupon showed in this file.
