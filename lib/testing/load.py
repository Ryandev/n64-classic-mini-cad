"""Load a module by its exact path, bypassing Python's module-name cache."""

import importlib.util


def load_by_path(path, unique_name):
    spec = importlib.util.spec_from_file_location(unique_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
