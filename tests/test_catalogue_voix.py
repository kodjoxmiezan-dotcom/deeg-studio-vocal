"""Tests hors réseau : présélections, rétrocompatibilité et garde-fous du catalogue."""
import importlib.util
import json
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("generer_catalogue", RACINE / "scripts" / "generer.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


def test_catalogue_structure_et_unicite():
    data = app.charger_catalogue()
    assert data["version"] == 1
    voix = data["voix"]
    ids = [v["identifiant"] for v in voix]
    assert len(ids) == len(set(ids)) == 10
    assert {v["moteur"] for v in voix} == {"edge", "piper", "voix_video"}
    assert sum(v["moteur"] == "edge" for v in voix) == 5
    assert sum(v["moteur"] == "piper" for v in voix) == 4
    assert sum(v["moteur"] == "voix_video" for v in voix) == 1


def test_voix_presetees():
    assert app.choisir_voix("edge", "fr-FR-DeniseNeural", "fr-FR-HenriNeural") == "fr-FR-DeniseNeural"
    assert app.choisir_voix("piper", "fr_FR-siwis-medium", "fr-FR-HenriNeural") == "fr_FR-siwis-medium"
    assert app.choisir_voix("voix_video", "automatique", "fr-FR-HenriNeural") == "deeg_voix_video_2026_11"


def test_retour_aux_options_historiques():
    assert app.choisir_voix("edge", "automatique", "fr-FR-HenriNeural") == "fr-FR-HenriNeural"
    assert app.choisir_voix("piper", "automatique", "fr-FR-HenriNeural") == "fr_FR-tom-medium"
    assert app.choisir_voix("edge", "", "fr-FR-DeniseNeural") == "fr-FR-DeniseNeural"
    assert app.choisir_voix("piper", "", "fr_FR-tom-medium") == "fr_FR-tom-medium"


def test_refus_melange_moteurs_et_voix_inconnues():
    with pytest.raises(ValueError, match="incompatible"):
        app.choisir_voix("piper", "fr-FR-DeniseNeural", "fr_FR-tom-medium")
    with pytest.raises(ValueError, match="inconnue"):
        app.choisir_voix("edge", "voix-inventee", "fr-FR-HenriNeural")
    with pytest.raises(ValueError, match="Moteur inconnu"):
        app.choisir_voix("moteur-inconnu", "automatique", "x")


def test_liste_actions_et_catalogue_synchronises():
    workflow = (RACINE / ".github" / "workflows" / "generer-voix.yml").read_text(encoding="utf-8")
    comparaison = (RACINE / ".github" / "workflows" / "comparatif-voix.yml").read_text(encoding="utf-8")
    assert "- automatique" in workflow
    for voix in app.charger_catalogue()["voix"]:
        if voix["moteur"] in {"edge", "piper"}:
            assert "          - " + voix["identifiant"] in workflow
        if voix["moteur"] == "edge":
            assert "          - " + voix["identifiant"] in comparaison
    assert "DEEG_VOICE_CATALOGUE: ${{ inputs.voix_catalogue || 'automatique' }}" in workflow


def test_catalogue_prive_sans_reference_audio():
    data = app.charger_catalogue()
    contenu = json.dumps(data, ensure_ascii=False)
    assert "DEEG_TANGUY_REFERENCE_URL" not in contenu
    assert "https://" not in contenu
    assert "reference_video.wav" not in contenu
