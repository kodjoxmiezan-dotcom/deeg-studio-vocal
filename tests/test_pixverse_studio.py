"""Tests 100 % hors ligne, y compris la preuve que simulation ne facture rien."""
import importlib.util
from pathlib import Path
from unittest.mock import patch
import pytest

SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "pixverse_studio.py"
spec = importlib.util.spec_from_file_location("pixverse_studio", SOURCE)
pix = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pix)


def test_tarifs_v6_sans_audio():
    assert pix.credits_estimes(5, "360p") == 25
    assert pix.credits_estimes(5, "720p") == 45
    assert pix.credits_estimes(10, "1080p") == 180


def test_creation_texte_et_image():
    p = pix.preparer_demande("texte", "Une école au lever du soleil.", 5, "720p", "16:9")
    assert p["model"] == "v6" and p["aspect_ratio"] == "16:9"
    assert p["generate_audio_switch"] is False and "img_id" not in p
    q = pix.preparer_demande("image", "Animation douce dans une cour.", 5, "360p", "16:9", "4567")
    assert q["img_id"] == 4567 and "aspect_ratio" not in q


@pytest.mark.parametrize("args", [
    ("image", "Animation douce dans une cour.", 5, "360p", "16:9", ""),
    ("texte", "Court", 5, "360p", "16:9", ""),
    ("texte", "Animation douce dans une cour.", 5, "240p", "16:9", ""),
    ("texte", "Animation douce dans une cour.", 5, "360p", "0:0", ""),
    ("texte", "Animation douce dans une cour.", 5, "360p", "16:9", "12"),
])
def test_refus_entrees_invalides(args):
    with pytest.raises(ValueError):
        pix.preparer_demande(*args)


def test_autorisation_credits_obligatoire():
    with pytest.raises(ValueError, match="autorisation"):
        pix.autoriser_generation("false", "25", 25, "cle")
    with pytest.raises(ValueError, match="secret"):
        pix.autoriser_generation("true", "25", 25, "")
    with pytest.raises(ValueError, match="Plafond"):
        pix.autoriser_generation("true", "24", 25, "cle")
    assert pix.autoriser_generation("true", "25", 25, "cle") == 25


def test_simulation_ne_fait_aucun_appel(tmp_path, monkeypatch):
    monkeypatch.setattr(pix, "OUTPUT", tmp_path)
    with patch.object(pix, "appel_api", side_effect=AssertionError("Réseau interdit")):
        r = pix.executer({
            "PIXVERSE_OPERATION": "simulation",
            "PIXVERSE_MODE": "texte",
            "PIXVERSE_PROMPT": "Cour d'école paisible au soleil.",
            "PIXVERSE_DUREE": "5",
            "PIXVERSE_QUALITE": "360p",
            "PIXVERSE_RATIO": "16:9",
        })
    assert r["simulation"] is True and r["credits_estimes"] == 25
    assert "aucun crédit" in r["etat"]
    assert (tmp_path / "rapport_pixverse.json").exists()


def test_execution_reelle_protegee_avant_reseau(tmp_path, monkeypatch):
    monkeypatch.setattr(pix, "OUTPUT", tmp_path)
    with patch.object(pix, "appel_api", side_effect=AssertionError("Ne doit pas appeler l'API")):
        with pytest.raises(ValueError):
            pix.executer({
                "PIXVERSE_OPERATION": "generation",
                "PIXVERSE_MODE": "texte",
                "PIXVERSE_PROMPT": "Cour d'école paisible au soleil.",
                "PIXVERSE_DUREE": "5",
                "PIXVERSE_QUALITE": "360p",
                "PIXVERSE_RATIO": "16:9",
                "PIXVERSE_AUTORISATION": "false",
                "PIXVERSE_CREDITS_MAX": "25",
                "PIXVERSE_API_KEY": "factice",
            })


def test_status_n_envoie_pas_de_generation(tmp_path, monkeypatch):
    monkeypatch.setattr(pix, "OUTPUT", tmp_path)
    appels = []
    def faux_appel(methode, chemin, cle, donnees=None):
        appels.append((methode, chemin))
        return {"status": 1, "url": "https://cdn.pixverse.ai/test.mp4"}
    with patch.object(pix, "appel_api", side_effect=faux_appel):
        r = pix.executer({
            "PIXVERSE_OPERATION": "statut",
            "PIXVERSE_VIDEO_ID": "12345",
            "PIXVERSE_API_KEY": "cle-privee",
            "PIXVERSE_PUBLIER_URL": "false",
        })
    assert appels == [("GET", "/openapi/v2/video/result/12345")]
    assert "url" not in r
    assert "cle-privee" not in (tmp_path / "rapport_pixverse.json").read_text()


def test_generation_acceptee_simulee_sans_double_charge(tmp_path, monkeypatch):
    monkeypatch.setattr(pix, "OUTPUT", tmp_path)
    appels = []
    def faux_appel(methode, chemin, cle, donnees=None):
        appels.append(methode)
        if methode == "POST":
            return {"video_id": 9876, "credits": 25}
        return {"status": 1, "url": "https://media.example.com/test.mp4"}
    with patch.object(pix, "appel_api", side_effect=faux_appel):
        r = pix.executer({
            "PIXVERSE_OPERATION": "generation",
            "PIXVERSE_MODE": "texte",
            "PIXVERSE_PROMPT": "Cour d'école paisible au soleil.",
            "PIXVERSE_DUREE": "5",
            "PIXVERSE_QUALITE": "360p",
            "PIXVERSE_RATIO": "16:9",
            "PIXVERSE_AUTORISATION": "true",
            "PIXVERSE_CREDITS_MAX": "25",
            "PIXVERSE_API_KEY": "cle-privee",
            "PIXVERSE_PUBLIER_URL": "false",
        })
    assert appels == ["POST", "GET"]
    assert r["video_id"] == 9876 and r["statut"] == 1
    assert "url" not in r
    assert "cle-privee" not in (tmp_path / "rapport_pixverse.json").read_text()
