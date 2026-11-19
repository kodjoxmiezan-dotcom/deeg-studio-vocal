"""Tests du module Podcastfy sans Internet, ni dépendances IA."""
import importlib.util
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "podcastfy_studio.py"
spec = importlib.util.spec_from_file_location("podcastfy_studio", SOURCE)
studio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(studio)


def test_exemple_dialogue_integral():
    texte = (SOURCE.parents[1] / "podcasts" / "exemple_dialogue.txt").read_text(encoding="utf-8")
    tours = studio.lignes_dialogue(texte)
    assert len(tours) == 6
    assert tours[0][0] == "Person1"
    assert tours[1][0] == "Person2"
    markup = studio.baliser(tours)
    assert markup.count("<Person1>") == 3
    assert markup.count("<Person2>") == 3
    assert studio.extraire_dialogue_balise(markup) == tours


def test_dialogue_pour_actions_sur_une_ligne():
    t = studio.lignes_dialogue("ANIMATRICE: Bonjour. | EXPERT: Bienvenue.")
    assert t == [("Person1", "Bonjour."), ("Person2", "Bienvenue.")]


def test_refus_repliques_malordonnees():
    for texte in ["ANIMATRICE: A", "EXPERT: A | ANIMATRICE: B",
                  "ANIMATRICE: A | ANIMATRICE: B",
                  "ANIMATRICE: A | EXPERT: "]:
        with pytest.raises(ValueError):
            studio.lignes_dialogue(texte)


def test_echappement_balises():
    texte = studio.baliser([("Person1", "Le nombre 3 < 5 & c'est vrai."),
                          ("Person2", "Tout à fait.")])
    assert "&lt;" in texte
    assert "&amp;" in texte


def test_validation_des_voix_et_contenus():
    assert studio.verifier_voix("fr-FR-DeniseNeural", "fr-FR-HenriNeural")
    with pytest.raises(ValueError):
        studio.verifier_voix("fr-FR-DeniseNeural", "fr-FR-DeniseNeural")
    with pytest.raises(ValueError):
        studio.verifier_voix("fr-FR-FausseNeural", "fr-FR-HenriNeural")
    with pytest.raises(ValueError):
        studio.source_validee("x" * 8001)


def test_mode_sans_cle_et_mode_ia_explicitement_autorise():
    studio.verifier_mode("dialogue", "", "false")
    with pytest.raises(ValueError):
        studio.verifier_mode("ia_gemini", "", "true")
    with pytest.raises(ValueError):
        studio.verifier_mode("ia_gemini", "exemple", "false")
    studio.verifier_mode("ia_gemini", "exemple", "true")
    with pytest.raises(ValueError):
        studio.verifier_mode("openai", "", "false")


def test_configuration_edge_uniquement():
    cfg = studio.configuration("fr-FR-DeniseNeural", "fr-FR-HenriNeural")
    tts = cfg["text_to_speech"]
    assert tts["default_tts_model"] == "edge"
    assert tts["edge"]["default_voices"]["question"] == "fr-FR-DeniseNeural"
    assert tts["edge"]["default_voices"]["answer"] == "fr-FR-HenriNeural"


def test_sous_titres_mentions_estimes(tmp_path):
    cible = tmp_path / "essai.srt"
    studio.sous_titres([("Person1", "Bonjour."), ("Person2", "Merci.")], 8.0, cible)
    texte = cible.read_text(encoding="utf-8")
    assert "00:00:08,000" in texte
    assert "Animatrice" in texte
    assert "Expert" in texte
