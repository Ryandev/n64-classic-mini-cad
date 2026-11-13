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

| Parts | Material | Why |
|---|---|---|
| Tub, shell, bracket, doors, buttons | PETG | tough, takes heat-set inserts; the GBA run's material |
| Cooling duct and intake hood | ASA, or PETG | the heat sink runs at 60–70 °C, close to PETG's ~70 °C limit, and the duct clamps it, so PETG may creep |
| Light pipe | clear PETG | |
| Supports' interface only | PLA | see below |

**No PLA in the console itself.** It softens at about 55 °C (GBA rejected it: HDT ~55 °C, creeps).
**Dry the PETG and the PLA interface spool** before use (G10).

## Supports

**The design aims to need none.** The gate's `overhang` row (`lib/printable.py`) fails any
downward face wider than a 10 mm bridge, unless the part declares `SUPPORT_MM2` with the reason.
The row fails if a part ever needs more than it declares. As of 2026-11-13:

| Part | Declared | Where | Why it's acceptable |
|---|---|---|---|
| `upper_shell` | 9,010 mm² | inside of the top deck | printed split-face down, the deck is a roof over the hollow shell; that face is hidden |
| `cooling_duct` | 510 mm² | a 34 x 16 mm ceiling at z 11.2 | **open**: it must be confirmed that support there can be reached and removed, or the face reshaped to bridge |
| everything else | 0 | | prints support-free |

When a part does need support, use the GBA set-up (`PRINTING.md`, DECISIONS 10-18 and 10-30):

- **PETG support body, PLA interface.** PLA barely bonds to PETG, so the support lifts off
  clean. PETG-on-PETG supports weld on: the face comes out rough and stringy, and mating parts
  don't fit (G5; dovetail coupon 11-10).
- **Tree supports, build plate only**, so the PLA stands on the bed. PLA laid *onto* a PETG face
  keys into it for good; PETG laid onto PLA lets go (06b, 10-29).
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
| Switch V-pin in the switch's moulded Ø2.35 hole | Ø2.2 | only the printed pin varies: coupon 2 |
| Door hinge pins in their sockets | Ø1.8 in Ø2.4 (0.30 mm/side) | **at risk**: a small hole; at −0.4 mm it leaves ~0.1 mm/side and may bind. Coupon 3 |
| Magnets in their pockets | Ø3.0 in Ø3.2 (0.10 mm/side) | **at risk**: at −0.3 mm the pocket is ~Ø2.9 and the magnet won't go in. Not yet measured on GBA either. Coupon 3 |

## Prove it small first

GBA's whole first black-PETG run went straight to full size and had to be reprinted (G8, "prove it
small before printing it big"). Here, `./run coupons` cuts print-test coupons from the real parts
into `export/coupons/`; print them before any full part. A stepped gauge (three sizes of one hole)
settles a size in one print. Record what each coupon showed in this file.
