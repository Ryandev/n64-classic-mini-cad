"""Single-command pass/fail gate for every check in `cad/lib/`.

    ./run gate

Exits 0 if and only if every row of every discovered `*_check.py` passes.

AUTO-DISCOVERED, not listed: every `<dir>/*_check.py` under `subassembly/`,
`assembly/`, `tiling/`, `slicing/` is found and run, plus `lint_subassembly.py`.

PARALLEL AND CACHED: checks run concurrently, and `lib/testing/gate_cache.py`
records every file each check opened so an unchanged check is answered from the
cache (`N64_GATE_NOCACHE=1` forces a full re-run).
"""

import concurrent.futures
import os
import re
import subprocess
import sys
import tempfile
import time

HERE = os.environ.get("N64_CAD_LIB_DIR") or os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from testing import gate_cache  # noqa: E402

SCAN_DIRS = ("subassembly", "assembly", "tiling", "slicing")
LINT = os.path.join("testing", "lint_subassembly.py")
ROW_RE = re.compile(r"^\s*(PASS|FAIL)\s+(\S.*?)\s*$")
CHECK_TIMEOUT_S = int(os.environ.get("N64_GATE_TIMEOUT", "420"))


def _default_jobs():
    try:
        with open("/proc/meminfo") as f:
            kb = next(int(x.split()[1]) for x in f if x.startswith("MemAvailable:"))
        by_ram = max(1, (kb // (1024 * 1024) - 2) // 2)
    except Exception:
        by_ram = 4
    return max(1, min(os.cpu_count() or 4, by_ram, 6))


JOBS = int(os.environ.get("N64_GATE_JOBS", _default_jobs()))
NOCACHE = os.environ.get("N64_GATE_NOCACHE", "") not in ("", "0")


def discover():
    found = []
    for d in SCAN_DIRS:
        full = os.path.join(HERE, d)
        if not os.path.isdir(full):
            continue
        for f in sorted(os.listdir(full)):
            if f.endswith("_check.py") and not f.startswith("_"):
                found.append(os.path.join(d, f))
    if os.path.isfile(os.path.join(HERE, LINT)):
        found.append(LINT)
    return found


def _parse_rows(stdout):
    return [
        (m.group(1) == "PASS", m.group(2))
        for line in stdout.splitlines()
        if (m := ROW_RE.match(line))
    ]


def _run_one(rel, key):
    path = os.path.join(HERE, rel)
    fd, log = tempfile.mkstemp(prefix="n64_deplog_", suffix=".txt")
    os.close(fd)
    env = os.environ.copy()
    env["N64_GATE_DEPLOG"] = log
    pypath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = gate_cache.SITE_DIR + (os.pathsep + pypath if pypath else "")
    t0 = time.time_ns()
    t_wall = time.monotonic()
    try:
        proc = subprocess.run(
            [sys.executable, path],
            cwd=HERE,
            env=env,
            capture_output=True,
            text=True,
            timeout=CHECK_TIMEOUT_S,
        )
        elapsed = time.monotonic() - t_wall
        deps, written, rss = gate_cache.parse_log(log)
        entry, why_not = gate_cache.make_entry(
            rel,
            key,
            deps,
            written,
            t0,
            proc.stdout,
            proc.stderr,
            proc.returncode,
            elapsed,
            rss,
        )
        return {
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "returncode": proc.returncode,
            "timed_out": False,
            "elapsed": elapsed,
            "rss_kb": rss,
            "entry": entry,
            "uncacheable": why_not,
        }
    except subprocess.TimeoutExpired as e:
        elapsed = time.monotonic() - t_wall
        _, _, rss = gate_cache.parse_log(log)
        out = e.stdout.decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        err = e.stderr.decode(errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        return {
            "stdout": out,
            "stderr": err,
            "returncode": -1,
            "timed_out": True,
            "elapsed": elapsed,
            "rss_kb": rss,
            "entry": None,
            "uncacheable": "timed out",
        }
    finally:
        try:
            os.unlink(log)
        except OSError:
            pass


def _grade(rel, res):
    rows = _parse_rows(res["stdout"])
    bad = [label for ok, label in rows if not ok]
    if res["timed_out"]:
        bad.append(f"<timed out after {CHECK_TIMEOUT_S}s ({len(rows)} row(s) printed before hang)>")
    elif not rows:
        bad.append("<produced no PASS/FAIL rows -- did the script crash or change format?>")
    elif res["returncode"] != 0 and not bad:
        bad.append(f"<exited {res['returncode']} with all rows PASS>")
    return rows, bad


def main():
    t_start = time.monotonic()
    checks = discover()
    only = [a for a in sys.argv[1:] if not a.startswith("-")]
    if only:
        checks = [c for c in checks if any(k in c for k in only)]
        if not checks:
            print(f"GATE: nothing matched {only}")
            return 2

    use_cache = gate_cache.enabled() and not NOCACHE
    cache = gate_cache.load() if gate_cache.enabled() else {"entries": {}, "stats": {}}
    key = gate_cache.env_key() if gate_cache.enabled() else ""

    results = {}
    to_run = []
    for rel in checks:
        if use_cache:
            entry, miss = gate_cache.lookup(cache, rel, key)
            if entry is not None:
                results[rel] = {
                    "stdout": entry["stdout"],
                    "stderr": entry.get("stderr_tail", ""),
                    "returncode": entry["returncode"],
                    "timed_out": False,
                    "elapsed": entry.get("elapsed", 0.0),
                    "rss_kb": entry.get("rss_kb", 0),
                    "cached": True,
                    "when": entry.get("when", "?"),
                }
                continue
        else:
            miss = "N64_GATE_NOCACHE=1" if NOCACHE else "N64_CAD_LIB_DIR set"
        to_run.append((rel, miss))

    n_hit = len(results)
    if to_run:
        workers = min(JOBS, len(to_run))
        order = sorted(
            to_run,
            key=lambda rm: -cache.get("stats", {}).get(rm[0], {}).get("elapsed", 999.0),
        )
        print(
            f"GATE: {len(checks)} check(s) -- {n_hit} cached, running {len(to_run)} "
            f"across {workers} worker(s)"
        )
        for rel, why in order:
            print(f"      miss {rel}: {why}")
        print(flush=True)

        updates, stats = {}, {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            futs = {pool.submit(_run_one, rel, key): rel for rel, _ in order}
            for fut in concurrent.futures.as_completed(futs):
                rel = futs[fut]
                res = fut.result()
                res["cached"] = False
                results[rel] = res
                rows, bad = _grade(rel, res)
                tag = "PASS" if not bad else "FAIL"
                mb = res["rss_kb"] // 1024
                print(
                    f"  done [{tag}] {rel:42s} {res['elapsed']:5.1f}s  "
                    f"{mb:4d}MB  ({len(rows)} rows)",
                    flush=True,
                )
                stats[rel] = {"elapsed": round(res["elapsed"], 1), "rss_kb": res["rss_kb"]}
                if res["entry"] is not None and rows and not res["timed_out"]:
                    updates[rel] = res["entry"]
        if gate_cache.enabled() and (updates or stats):
            gate_cache.save(updates, stats)
        print()

    total_rows = 0
    failed = []
    for rel in checks:
        res = results[rel]
        rows, bad = _grade(rel, res)
        total_rows += len(rows)
        status = "PASS" if not bad else "FAIL"
        origin = (
            f"cached ({res['elapsed']:.1f}s @ {res['when']})"
            if res["cached"]
            else f"ran in {res['elapsed']:.1f}s"
        )
        print(f"=== [{status}] {rel}  ({len(rows)} rows, {origin}) ===")
        print(res["stdout"].rstrip())
        if bad and res["stderr"]:
            print("  --- stderr (last 10 lines) ---")
            for ln in res["stderr"].strip().splitlines()[-10:]:
                print(f"  {ln}")
        print()
        if bad:
            failed.append((rel, bad))

    wall = time.monotonic() - t_start
    print("=" * 66)
    if not failed:
        print(
            f"GATE: PASS  ({len(checks)} check scripts, {total_rows} rows, "
            f"{n_hit} cached / {len(to_run)} ran, {wall:.1f}s)"
        )
        return 0
    print(f"GATE: FAIL  ({len(failed)}/{len(checks)} scripts failed, {wall:.1f}s)")
    for rel, bad in failed:
        for b in bad:
            print(f"  FAIL  {rel} :: {b}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
