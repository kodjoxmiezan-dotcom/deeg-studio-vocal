import importlib.util
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "generer.py"
spec = importlib.util.spec_from_file_location("generer", SOURCE)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


def test_speed():
    assert app.check_speed("85") == 85
    assert app.check_speed("130") == 130
    for value in ["0", "200", "x"]:
        try:
            app.check_speed(value)
        except ValueError:
            continue
        raise AssertionError(f"Vitesse invalide acceptée : {value}")


def test_timestamp():
    assert app.stamp(61.234) == "00:01:01,234"


def test_srt(tmp_path):
    path = tmp_path / "demo.srt"
    app.estimate_srt("Bonjour. Au revoir.", 4.0, path)
    content = path.read_text(encoding="utf-8")
    assert "00:00:04,000" in content
    assert "Bonjour." in content
    assert "Au revoir." in content
