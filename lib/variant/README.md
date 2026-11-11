# `lib/variant/` — deliberate deviations from a reference-matched part

Every module in `lib/variant/<name>.py`:
1. Imports its faithful counterpart from `lib/part/<name>.py` (`from part import <name> as FAITHFUL`).
2. Applies only the deliberate modifications needed for the N64 Classic Mini build (e.g., Radxa X4 M2.5 standoffs, rear USB-C / Micro-HDMI / 3.5mm Audio / RJ45 apertures, front LED bore).
3. Declares **every added or removed chunk of geometry** in a `DEVIATIONS` dict with `kind` (`"added"` or `"removed"`), `why`, `bbox`, `volume_mm3`, and `tolerance_mm3`.

Verified by `lib/testing/variant_manifest.py`: any undeclared chunk or size mismatch fails the gate.
