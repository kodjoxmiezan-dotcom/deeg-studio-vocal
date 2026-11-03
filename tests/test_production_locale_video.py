"""Tests du lancement vocal local sans téléverser de référence ni charger le modèle."""
import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location(
    "produire_voix_video_locale", SCRIPTS / "produire_voix_video_locale.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_textes_valides():
    assert mod.verifier_texte(" Bonjour ") == "Bonjour"
    for invalide in ("", " " * 3, "a" * 501):
        with pytest.raises(ValueError):
            mod.verifier_texte(invalide)


def test_autorisation_requise(tmp_path):
    with pytest.raises(PermissionError, match="autorisation"):
        mod.produire(tmp_path / "video.mp4", tmp_path / "sortie",
                     "Bonjour.", autorisation=False)


def test_generation_simulee_protege_la_reference(tmp_path, monkeypatch):
    video = tmp_path / "source.mp4"
    video.write_bytes(b"fichier de test")
    dossier_sortie = tmp_path / "sortie"
    profil_temp = {}

    def fausse_preparation(source, reference, debut, duree):
        assert source == video
        assert duree == 10.0
        reference.write_bytes(b"PRIVATE-REFERENCE")
        profil_temp["reference"] = reference
        return {"duree_secondes": 10.0, "rms_normalise": 0.1,
                "part_ecretee": 0.0}

    def faux_processus(args, **kw):
        assert "cloner_voix.py" in args[1]
        ref = Path(kw["env"]["DEEG_REFERENCE_PATH"])
        assert ref.read_bytes() == b"PRIVATE-REFERENCE"
        assert kw["env"]["DEEG_TEXT"] == "Bonjour."
        assert kw["env"]["DEEG_SPEED"] == "85"
        dossier = mod.ROOT / "sorties-clonage"
        dossier.mkdir(exist_ok=True)
        (dossier / "narrateur_deeg.wav").write_bytes(b"sortie-wav")
        (dossier / "narrateur_deeg.mp3").write_bytes(b"sortie-mp3")
        (dossier / "texte_narre.txt").write_text("Bonjour.", encoding="utf-8")

    monkeypatch.setattr(mod, "preparer", fausse_preparation)
    monkeypatch.setattr(mod, "duration_seconds", lambda *_: 2.5)
    monkeypatch.setattr(mod, "estimate_srt", lambda text, duration, path:
                        path.write_text("essai SRT", encoding="utf-8"))
    monkeypatch.setattr(mod.subprocess, "run", faux_processus)
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    resultat = mod.produire(video, dossier_sortie, "Bonjour.", autorisation=True)
    assert resultat["mode"] == "synthese_reference"
    assert (dossier_sortie / "DEEG_voix_video.wav").read_bytes() == b"sortie-wav"
    assert (dossier_sortie / "DEEG_voix_video.mp3").read_bytes() == b"sortie-mp3"
    assert (dossier_sortie / "DEEG_voix_video.srt").read_text() == "essai SRT"
    assert (dossier_sortie / "rapport.json").exists()
    assert not profil_temp["reference"].exists()
    assert not (dossier_sortie / "reference.wav").exists()
