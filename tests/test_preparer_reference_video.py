"""Tests du préparateur audio : aucun moteur IA ni réseau requis."""
import importlib.util
from pathlib import Path
import shutil
import subprocess

import pytest

FICHIER = Path(__file__).resolve().parents[1] / "scripts" / "preparer_reference_video.py"
spec = importlib.util.spec_from_file_location("preparer_reference_video", FICHIER)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_validation_debut_longueur():
    module.valider_parametres(0, 10, 20.01)
    module.valider_parametres(10, 10, 20.01)
    for debut, longueur, duree in [(-1, 10, 20), (0, 4, 20), (0, 21, 22), (15, 10, 20)]:
        with pytest.raises(ValueError):
            module.valider_parametres(debut, longueur, duree)


@pytest.mark.skipif(shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
                    reason="FFmpeg non installé")
def test_preparation_depuis_audio(tmp_path):
    entree = tmp_path / "entree.wav"
    sortie = tmp_path / "prive" / "extrait.wav"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", "sine=frequency=220:duration=10.5",
                    str(entree)], check=True)
    result = module.preparer(entree, sortie, 0, 10)
    assert 9.95 <= result["duree_secondes"] <= 10.05
    assert result["rms_normalise"] > 0.002
    assert sortie.is_file()


@pytest.mark.skipif(shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
                    reason="FFmpeg non installé")
def test_fichier_sans_audio(tmp_path):
    video = tmp_path / "sans_audio.mp4"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", "color=c=black:s=64x64:d=6",
                    "-an", "-c:v", "mpeg4", str(video)], check=True)
    with pytest.raises(ValueError, match="Aucune piste audio"):
        module.inspecter(video)
