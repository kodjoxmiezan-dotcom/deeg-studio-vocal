"""Tests sans installation des poids Kokoro ni dépendances volumineuses."""
import importlib.util
from pathlib import Path
import pytest

CHEMIN = Path(__file__).resolve().parents[1] / "scripts" / "essai_kokoro_fr.py"
spec = importlib.util.spec_from_file_location("essai_kokoro_fr", CHEMIN)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


def test_texte_autorise():
    assert app.verifier_texte("  Bonjour.  ") == "Bonjour."
    with pytest.raises(ValueError):
        app.verifier_texte("")
    with pytest.raises(ValueError):
        app.verifier_texte("A" * 801)


def test_vitesse_autorisee():
    assert app.verifier_vitesse("85") == 85
    for invalide in ["0", "150", "abc"]:
        with pytest.raises(ValueError):
            app.verifier_vitesse(invalide)


def test_pipeline_reste_isole():
    script = CHEMIN.read_text(encoding="utf-8")
    assert 'voice="ff_siwis"' in script
    assert 'KPipeline(lang_code="f")' in script
    assert "DEEG_TANGUY_REFERENCE_URL" not in script
    assert "DEEG_VIDEO_VOICE_REFERENCE_URL" not in script
