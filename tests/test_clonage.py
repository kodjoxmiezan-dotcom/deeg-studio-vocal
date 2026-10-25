from pathlib import Path
import importlib.util

source = Path(__file__).resolve().parents[1] / "scripts" / "cloner_voix.py"
spec = importlib.util.spec_from_file_location("cloner_voix", source)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_passages_courts():
    texte = "Première phrase. Deuxième phrase importante. Et une troisième."
    parts = mod.passages(texte, max_chars=32)
    assert len(parts) > 1
    assert " ".join(parts) == texte


def test_passages_long():
    sentence = "Bonjour " * 25
    parts = mod.passages(sentence, max_chars=40)
    assert all(len(x) <= 40 for x in parts)
    assert " ".join(parts) == sentence.strip()


def test_vitesse():
    assert mod.vitesse("85") == 85
    for v in ["0", "140"]:
        try:
            mod.vitesse(v)
            assert False, "Valeur invalide acceptée"
        except ValueError:
            pass
