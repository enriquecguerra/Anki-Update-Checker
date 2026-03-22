import importlib.util
import sys
from pathlib import Path


def ensure_package_loaded() -> str:
    package_name = "update_checker_pkg"
    if package_name in sys.modules:
        return package_name

    repo_root = Path(__file__).resolve().parents[1]
    init_file = repo_root / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        package_name,
        init_file,
        submodule_search_locations=[str(repo_root)],
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not create package spec for tests.")

    module = importlib.util.module_from_spec(spec)
    sys.modules[package_name] = module
    spec.loader.exec_module(module)
    return package_name
