"""Tests de l'intégration de la voix privée dans le Studio vocal DEEG.

Aucun accès au modèle Chatterbox n'est nécessaire pour ces tests.
"""
import importlib.util
from pathlib import Path

import pytest

source = Path(__file__).resolve().parents[1] / "scripts" / "generer.py"
spec = importlib.util.spec_from_file_location("deeg_generer", source)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_voix_video_reference_absente(tmp_path, monkeypatch):
    monkeypatch.setenv("DEEG_REFERENCE_PATH", str(tmp_path / "absente.wav"))
    with pytest.raises(FileNotFoundError, match="Référence privée absente"):
        mod.voix_video("Bonjour.", 85, tmp_path / "a.mp3",
                       tmp_path / "a.wav", tmp_path / "a.srt")


def test_voix_video_limite_texte(tmp_path):
    with pytest.raises(ValueError, match="500 caractères"):
        mod.voix_video("a" * 501, 85, tmp_path / "a.mp3",
                       tmp_path / "a.wav", tmp_path / "a.srt")


def test_voix_video_sorties_et_env(tmp_path, monkeypatch):
    reference = tmp_path / "voix-privee.wav"
    reference.write_bytes(b"reference simulee")
    monkeypatch.setenv("DEEG_REFERENCE_PATH", str(reference))
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    dossier = tmp_path / "sorties-clonage"
    dossier.mkdir()
    (dossier / "narrateur_deeg.wav").write_bytes(b"wav-de-test")
    (dossier / "narrateur_deeg.mp3").write_bytes(b"mp3-de-test")
    monkeypatch.setattr(mod, "duration_seconds", lambda _: 2.5)
    envs = []
    def fake_run(args, **kwargs):
        envs.append(kwargs.get("env", {}))
    monkeypatch.setattr(mod.subprocess, "run", fake_run)

    wav, mp3, srt = (tmp_path / f"resultat.{ext}"
                     for ext in ("wav", "mp3", "srt"))
    voix = mod.voix_video("Bonjour, bienvenue dans le studio.", 85, mp3, wav, srt)
    assert voix == "deeg_voix_video_2026_11"
    assert wav.read_bytes() == b"wav-de-test"
    assert mp3.read_bytes() == b"mp3-de-test"
    assert "00:00:02,500" in srt.read_text(encoding="utf-8")
    assert envs[0]["DEEG_SPEED"] == "85"
    assert envs[0]["DEEG_REFERENCE_PATH"] == str(reference)
