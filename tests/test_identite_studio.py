"""Contrôle de la nouvelle identité de marque sans migration technique DEEG."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
NAME = "Studio Vocal Éboulé"
PRESENTATION = [
    "README.md",
    "scripts/interface_studio.py",
    ".github/workflows/generer-voix.yml",
    ".github/workflows/comparatif-voix.yml",
    ".github/workflows/audit-catalogue.yml",
    "outils/ouvrir_studio_mac.command",
    ".github/workflows/clonage-voix.yml",
    ".github/workflows/profil-voix-video.yml",
    "scripts/generer_dictee_cm2_exemple.py",
    "scripts/exp_prepa_reprise_89_studio_edge.py",
]


def test_identite_de_marque():
    for fichier in PRESENTATION:
        source = (ROOT / fichier).read_text(encoding="utf-8")
        assert NAME in source, f"Marque manquante dans {fichier}"
        assert re.search(r"(studio\\s+vocal\\s+deeg|deeg\\s+studio\\s+vocal|studio\\s+deeg)", source, re.I) is None, fichier


def test_identifiants_deeg_preserves():
    generateur = (ROOT / "scripts/generer.py").read_text(encoding="utf-8")
    workflow = (ROOT / ".github/workflows/generer-voix.yml").read_text(encoding="utf-8")
    assert "DEEG_ENGINE" in generateur
    assert "DEEG_VIDEO_VOICE_REFERENCE_URL" in workflow
    assert "DEEG_VOICE_CATALOGUE" in workflow
