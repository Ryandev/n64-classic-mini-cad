"""Build `lib/step/radxa_x4.step` from Radxa's own download, unedited (C10).

    ./run radxa-ref [ZIP] [--out PATH]   # downloads Radxa's zip when no ZIP is given

The reference was once assembled by hand (connectors picked by index, an HDMI shield copied in,
a USB-C socket drawn with a corner cut away "to clear the standoff"), so the clearance rows
graded the case against a board edited to pass them. This builds it the only allowed way:

1. the zip from `URL`, checked against `SHA256` (a changed file fails loud, not silently);
2. its one STEP, imported whole: every solid Radxa modelled, nothing added or removed;
3. moved (translation only) so the board's four Ø2.7 mounting holes, found in the PCB solid,
   sit on this project's local PCB frame: the `58 x 49 mm` pattern centred where
   `assembly/datum.py` puts it (holes at x -39/+19, y ±24.5).

Anything the console needs changed (the desoldered headers) is a declared deviation in
`variant/radxa_x4.py`, never an edit here. The model's licence isn't stated, so the output stays
in the git-ignored `private/cad/step/` (the `radxa_x4.step` symlink).
"""

import argparse
import hashlib
import itertools
import os
import sys
import tempfile
import urllib.request
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq  # noqa: E402
from assembly import datum as D  # noqa: E402

URL = "https://dl.radxa.com/x/x4/radxa_x4_3d_pcba.zip"
SHA256 = "5daee0a08da5a40efbd9427c562147f17240f55638f30151862f5ea19ed3ebec"  # 2024-11-20 build
STEP_NAME = "radxa_x4_v1.11_3d_20241120.stp"
SOLIDS = 363  # what Radxa's STEP holds; the check rows hold the built reference to it
HOLE_R = D.RADXA_HOLE_D / 2.0
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "radxa_x4.step")


def local_hole_centre() -> tuple[float, float]:
    """The mounting-hole pattern's centre in the local PCB frame (from the datum)."""
    x_left = -D.RADXA_W / 2.0 + D.RADXA_HOLE_LEFT_MARGIN
    return (x_left + D.RADXA_HOLE_DX / 2.0, 0.0)


def mounting_holes(board: cq.Solid) -> list[tuple[float, float]]:
    """Axis XY of every Ø2.7 mm through-hole in the PCB solid (deduplicated)."""
    found: set[tuple[float, float]] = set()
    for face in board.Faces():
        if face.geomType() != "CYLINDER":
            continue
        cyl = face._geomAdaptor().Cylinder()
        if abs(cyl.Radius() - HOLE_R) > 0.01:
            continue
        loc = cyl.Location()
        found.add((round(loc.X(), 3), round(loc.Y(), 3)))
    return sorted(found)


def mounting_pattern(holes: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """The four holes on the datum's 58 x 49 mm rectangle (the board has other Ø2.7 holes)."""
    found = []
    for quad in itertools.combinations(holes, 4):
        xs = sorted({x for x, _ in quad})
        ys = sorted({y for _, y in quad})
        if (
            len(xs) == 2
            and len(ys) == 2
            and abs(xs[1] - xs[0] - D.RADXA_HOLE_DX) <= 0.05
            and abs(ys[1] - ys[0] - D.RADXA_HOLE_DY) <= 0.05
        ):
            found.append(list(quad))
    if len(found) != 1:
        raise SystemExit(f"expected one 58 x 49 mm mounting pattern among {holes}, found {found}")
    return found[0]


def pattern_centre(raw: cq.Shape) -> tuple[float, float]:
    """Centre of the mounting-hole pattern in the PCB (the board's biggest solid)."""
    board = sorted(raw.Solids(), key=lambda s: -s.Volume())[0]
    quad = mounting_pattern(mounting_holes(board))
    return (sum(x for x, _ in quad) / 4.0, sum(y for _, y in quad) / 4.0)


def placement(raw: cq.Shape) -> tuple[float, float]:
    """The XY shift that puts the mounting-hole pattern on the local PCB frame."""
    (cx, cy), (px, py) = local_hole_centre(), pattern_centre(raw)
    return (cx - px, cy - py)


def fetch(dest: str) -> str:
    """Download Radxa's zip to `dest`."""
    with urllib.request.urlopen(URL, timeout=120) as response, open(dest, "wb") as out:  # noqa: S310 - fixed https URL
        out.write(response.read())
    return dest


def build(zip_path: str, out: str = OUT) -> tuple[int, tuple[float, float]]:
    """Check, import, place and write the reference; returns (solids, shift)."""
    digest = hashlib.sha256(open(zip_path, "rb").read()).hexdigest()
    if digest != SHA256:
        raise SystemExit(f"{zip_path}: SHA-256 {digest}, expected {SHA256} (Radxa changed it?)")
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(zip_path) as z:
            z.extract(STEP_NAME, tmp)
        raw = cq.importers.importStep(os.path.join(tmp, STEP_NAME)).val()
    count = len(raw.Solids())
    if count != SOLIDS:
        raise SystemExit(f"{STEP_NAME}: {count} solids, expected {SOLIDS}")
    shift = placement(raw)
    placed = raw.translate(cq.Vector(shift[0], shift[1], 0.0))
    target = os.path.realpath(out)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    cq.exporters.export(placed, target)
    return count, shift


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("zip", nargs="?", help="Radxa's zip (downloaded when left out)")
    parser.add_argument("--out", default=OUT, help="where to write the STEP (CI: a temp file)")
    args = parser.parse_args(argv)
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = args.zip or fetch(os.path.join(tmp, "radxa_x4_3d_pcba.zip"))
        count, shift = build(zip_path, args.out)
    dx, dy = shift
    print(f"{args.out}: {count} solids from {STEP_NAME}, moved by ({dx:+.3f}, {dy:+.3f}, 0)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
