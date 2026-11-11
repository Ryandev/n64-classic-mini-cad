"""The gate's result cache: a check is re-run only when something it read has changed."""

import fcntl
import hashlib
import json
import os
import sys
import time

TESTING = os.path.dirname(os.path.abspath(__file__))
SITE_DIR = os.path.join(TESTING, "_gate_site")
REPO = os.path.dirname(os.path.dirname(TESTING))
CACHE_DIR = os.path.join(REPO, "scratch", "cache")
CACHE_FILE = os.path.join(CACHE_DIR, "gate_cache.json")
LOCK_FILE = os.path.join(CACHE_DIR, "gate_cache.lock")
VERSION = 1


def _sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _listing(path):
    names = sorted(
        n
        for n in os.listdir(path)
        if not n.startswith(".") and n != "__pycache__" and not n.endswith(".pyc")
    )
    return hashlib.sha256("\n".join(names).encode("utf-8", "surrogateescape")).hexdigest()


def env_key():
    """Everything outside the recorded files that can change a result."""
    h = hashlib.sha256()
    h.update(f"v{VERSION}\n{sys.version}\n{os.path.realpath(sys.executable)}\n".encode())
    meta = os.path.join(sys.prefix, "conda-meta")
    if os.path.isdir(meta):
        h.update("\n".join(sorted(os.listdir(meta))).encode())
    h.update(_sha_file(os.path.join(SITE_DIR, "sitecustomize.py")).encode())
    h.update(_sha_file(os.path.abspath(__file__)).encode())
    for k in sorted(os.environ):
        if k.startswith("N64_") and not k.startswith("N64_GATE_"):
            h.update(f"{k}={os.environ[k]}\n".encode())
    return h.hexdigest()


def enabled():
    return "N64_CAD_LIB_DIR" not in os.environ


def _load():
    try:
        with open(CACHE_FILE) as f:
            data = json.load(f)
        if data.get("version") == VERSION:
            return data
    except (OSError, ValueError):
        pass
    return {"version": VERSION, "entries": {}, "stats": {}}


def load():
    return _load()


def _sig(kind, path):
    try:
        if kind == "D":
            return (_listing(path), None) if os.path.isdir(path) else ("missing", None)
        st = os.stat(path)
    except FileNotFoundError:
        return "missing", None
    except OSError as e:
        return f"error:{e.errno}", None
    if os.path.isdir(path):
        return "dir", None
    return None, (st.st_size, st.st_mtime_ns)


def lookup(data, check, key):
    entry = data["entries"].get(check)
    if entry is None:
        return None, "no cached result"
    if entry.get("env") != key:
        return None, "interpreter, environment or N64_* variables changed"
    for dep in entry["deps"]:
        kind, path, size, mtime, sig = dep
        cur, stat = _sig(kind, path)
        if cur is None:
            if stat == (size, mtime):
                continue
            try:
                cur = _sha_file(path)
            except OSError as e:
                cur = f"error:{e.errno}"
        if cur != sig:
            return None, f"{_rel(path)} changed"
    return entry, None


def _rel(path):
    try:
        r = os.path.relpath(path, REPO)
        return path if r.startswith("..") else r
    except ValueError:
        return path


def parse_log(log_path):
    order, first, written, rss = [], {}, set(), 0
    try:
        with open(log_path, encoding="utf-8", errors="surrogateescape") as f:
            lines = f.read().splitlines()
    except OSError:
        return [], set(), 0
    for line in lines:
        kind, _, val = line.partition("\t")
        if kind == "M":
            rss = max(rss, int(val or 0))
            continue
        if kind == "W":
            written.add(val)
            first.setdefault(val, "W")
            continue
        if kind == "D":
            key = ("D", val)
        else:
            first.setdefault(val, kind)
            key = ("F", val)
        if key not in order:
            order.append(key)
    deps = [(k, p) for k, p in order if k == "D" or first.get(p) != "W"]
    return deps, written, rss


def make_entry(check, key, deps, written, t0, stdout, stderr, returncode, elapsed, rss):
    out = []
    for kind, path in deps:
        sig, stat = _sig(kind, path)
        size = mtime = None
        if sig is None:
            size, mtime = stat
            if mtime >= t0 and path not in written:
                return None, f"{_rel(path)} changed during the run"
            try:
                sig = _sha_file(path)
            except OSError as e:
                return None, f"{_rel(path)} unreadable ({e.errno})"
        out.append([kind, path, size, mtime, sig])
    return {
        "env": key,
        "deps": out,
        "stdout": stdout,
        "stderr_tail": "\n".join((stderr or "").strip().splitlines()[-5:]),
        "returncode": returncode,
        "elapsed": round(elapsed, 1),
        "rss_kb": rss,
        "when": time.strftime("%Y-%m-%d %H:%M:%S"),
    }, None


def save(updates, stats):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(LOCK_FILE, "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        data = _load()
        data["entries"].update(updates)
        for check, s in stats.items():
            data["stats"].setdefault(check, {}).update(s)
        for d in (data["entries"], data["stats"]):
            for check in [c for c in d if not os.path.exists(os.path.join(REPO, "lib", c))]:
                del d[check]
        tmp = f"{CACHE_FILE}.{os.getpid()}.tmp"
        with open(tmp, "w") as f:
            json.dump(data, f)
        os.replace(tmp, CACHE_FILE)
