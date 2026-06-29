"""Standalone test runner (no pytest needed). Imports every test_*.py and runs each test_*()."""
import importlib, pathlib, sys, traceback

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))


def main() -> int:
    modules = [p.stem for p in HERE.glob("test_*.py")]
    passed = failed = 0
    for mod_name in sorted(modules):
        mod = importlib.import_module(mod_name)
        for name in sorted(dir(mod)):
            if not name.startswith("test_"):
                continue
            fn = getattr(mod, name)
            if not callable(fn):
                continue
            try:
                fn()
                passed += 1
                print(f"  PASS {mod_name}.{name}")
            except Exception as e:
                failed += 1
                print(f"  FAIL {mod_name}.{name}: {e}")
                traceback.print_exc()
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
