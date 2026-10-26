from pathlib import Path
import importlib.util

module_path = Path(__file__).resolve().parents[1] / "scripts" / "optimiser_tanguy.py"
spec = importlib.util.spec_from_file_location("optimiser_tanguy", module_path)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


def test_two_distinct_profiles():
    assert len(app.PROFILES) == 2
    assert len({p["id"] for p in app.PROFILES}) == 2
    assert all(0.0 < p["cfg_weight"] < 1 for p in app.PROFILES)


def test_reference_files_private():
    assert all(not p["ref"].startswith("/") for p in app.PROFILES)
    assert all(p["ref"].endswith(".wav") for p in app.PROFILES)


def test_speed_validation():
    assert app.valid_speed("85") == 85
    for bad in ["150", "x"]:
        try:
            app.valid_speed(bad)
            assert False
        except ValueError:
            pass
