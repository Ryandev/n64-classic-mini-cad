"""Dependency recorder for the gate's result cache. Inert unless N64_GATE_DEPLOG is set."""

import os
import sys

_LOG = os.environ.get("N64_GATE_DEPLOG")

if _LOG:
    import atexit
    import resource

    _fd = os.open(_LOG, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    _seen = set()
    _skip = tuple(
        p.rstrip("/") + "/"
        for p in {sys.prefix, sys.base_prefix, sys.exec_prefix}
        | {"/usr", "/lib", "/lib64", "/bin", "/proc", "/sys", "/dev", "/etc", "/run"}
        | {os.path.expanduser("~/.cache"), os.path.dirname(os.path.abspath(__file__))}
    )

    def _emit(kind, path):
        if isinstance(path, int):
            return
        try:
            path = os.fsdecode(path)
            path = os.path.abspath(path)
        except Exception:
            return
        if path == _LOG or path.startswith(_skip):
            return
        if "/__pycache__" in path or path.endswith(".pyc"):
            if kind == "R" and path.endswith(".pyc") and "/__pycache__/" in path:
                d, f = os.path.split(path)
                path = os.path.join(os.path.dirname(d), f.split(".", 1)[0] + ".py")
            else:
                return
        key = (kind, path)
        if key in _seen:
            return
        _seen.add(key)
        os.write(_fd, f"{kind}\t{path}\n".encode("utf-8", "surrogateescape"))

    def _hook(event, args):
        try:
            if event == "open":
                path, mode = args[0], args[1]
                if isinstance(mode, str) and ("r" not in mode and "+" not in mode):
                    _emit("W", path)
                    return
                flags = args[2] if len(args) > 2 and isinstance(args[2], int) else 0
                if flags & os.O_WRONLY:
                    _emit("W", path)
                    return
                if flags & os.O_RDWR:
                    _emit("W", path)
                _emit("R", path)
            elif event in ("os.listdir", "os.scandir"):
                _emit("D", args[0] if args and args[0] is not None else ".")
        except Exception:
            pass

    sys.addaudithook(_hook)

    _real_stat = os.stat

    def _stat(path, *a, **k):
        if not k.get("dir_fd"):
            try:
                _emit("S", path)
            except Exception:
                pass
        return _real_stat(path, *a, **k)

    os.stat = _stat

    _READERS = {
        "OCP.STEPControl": [
            ("STEPControl_Reader", "ReadFile", 1, "R"),
            ("STEPControl_Writer", "Write", 1, "W"),
        ],
        "OCP.STEPCAFControl": [
            ("STEPCAFControl_Reader", "ReadFile", 1, "R"),
            ("STEPCAFControl_Writer", "Write", 1, "W"),
        ],
        "OCP.IGESControl": [("IGESControl_Reader", "ReadFile", 1, "R")],
        "OCP.BRepTools": [("BRepTools", "Read_s", 1, "R"), ("BRepTools", "Write_s", 1, "W")],
        "OCP.StlAPI": [("StlAPI_Reader", "Read", 2, "R"), ("StlAPI_Writer", "Write", 2, "W")],
    }

    def _wrap(mod):
        for cls_name, meth, argi, kind in _READERS.get(mod.__name__, ()):
            cls = getattr(mod, cls_name, None)
            orig = getattr(cls, meth, None) if cls is not None else None
            if orig is None or getattr(orig, "_gate_wrapped", False):
                continue
            static = meth.endswith("_s")

            def make(orig, argi, kind, static):
                def w(*a, **k):
                    if len(a) > argi and isinstance(a[argi], (str, bytes, os.PathLike)):
                        _emit(kind, a[argi])
                    return orig(*a, **k)

                w._gate_wrapped = True
                return staticmethod(w) if static else w

            try:
                setattr(cls, meth, make(orig, argi, kind, static))
            except Exception:
                pass

    class _Finder:
        def find_spec(self, name, path=None, target=None):
            if name != "OCP" and name not in _READERS:
                return None
            for f in sys.meta_path:
                if f is self:
                    continue
                spec = getattr(f, "find_spec", lambda *a: None)(name, path, target)
                if spec is not None and spec.loader is not None:
                    real = spec.loader.exec_module

                    def exec_module(module, real=real):
                        real(module)
                        for m in _READERS:
                            if m in sys.modules:
                                _wrap(sys.modules[m])

                    spec.loader.exec_module = exec_module
                    return spec
            return None

    sys.meta_path.insert(0, _Finder())
    for _m in list(_READERS):
        if _m in sys.modules:
            _wrap(sys.modules[_m])

    def _at_exit():
        for m in list(sys.modules.values()):
            f = getattr(m, "__file__", None)
            if f:
                _emit("R", f)
        kb = max(
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
        )
        os.write(_fd, f"M\t{kb}\n".encode())

    atexit.register(_at_exit)
