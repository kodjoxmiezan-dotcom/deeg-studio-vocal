"""Contrôles de l'interface sans charger Gradio ni le modèle Chatterbox."""
from pathlib import Path
import importlib.util
import sys

SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "interface_studio.py"
spec = importlib.util.spec_from_file_location("interface_studio", SOURCE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_diagnostic_sans_source():
    res = mod.diagnostiquer(None, "Bonjour.", 0, 85)
    assert res["etat"] == "Échec du diagnostic"
    assert "Sélectionnez" in res["erreur"]


def test_genere_refus_sans_droits():
    resultat, audio, fichiers, infos = mod.generer(None, "Bonjour.", 0, 85, False)
    assert "droits" in resultat
    assert audio is None
    assert fichiers == []
    assert infos == {}


def test_generer_simulation(tmp_path, monkeypatch):
    source = tmp_path / "voix_20s.wav"
    source.write_bytes(b"source privée")
    dossier = tmp_path / "sorties"
    dossier.mkdir()
    monkeypatch.setattr(mod, "OUTPUT", dossier)
    details = {}

    def faux_produire(**kwargs):
        details.update(kwargs)
        for fichier in (
            "DEEG_voix_video.wav", "DEEG_voix_video.mp3",
            "DEEG_voix_video.srt", "rapport.json", "texte_narre.txt"
        ):
            (dossier / fichier).write_text("essai")
        return {"mode": "synthese_reference", "vitesse_pct": 85}

    monkeypatch.setattr(mod, "produire", faux_produire)
    message, wav, fichiers, rapport = mod.generer(
        str(source), "Bonjour DEEG", 0, 85, True
    )
    assert message.startswith("✅")
    assert wav == str(dossier / "DEEG_voix_video.wav")
    assert len(fichiers) == 5
    assert details["source"] == source
    assert details["autorisation"] is True
    assert rapport["mode"] == "synthese_reference"
    assert "source" not in " ".join(fichiers)


def test_diagnostic_simule(tmp_path, monkeypatch):
    source = tmp_path / "voix.mp3"
    source.write_bytes(b"audio")
    monkeypatch.setattr(mod, "produire", lambda **kwargs: {
        "mode": "diagnostic", "duree_reference_secondes": 10.0,
        "diagnostic": kwargs["diagnostic"],
    })
    rep = mod.diagnostiquer(str(source), "Phrase.", 0, 85)
    assert rep["etat"] == "Référence validée techniquement"
    assert rep["diagnostic"] is True


def test_application_ecoute_locale_uniquement():
    texte = SOURCE.read_text(encoding="utf-8")
    assert 'server_name="127.0.0.1"' in texte
    assert "share=False" in texte
    assert "allowed_paths=[str(OUTPUT.resolve())]" in texte
