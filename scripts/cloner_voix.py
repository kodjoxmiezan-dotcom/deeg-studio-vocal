"""Reproduction vocale DEEG via Chatterbox Multilingual V3 (expérimental).

La référence audio est fournie par l'utilisateur et n'est jamais publiée
dans le dépôt public ou les artefacts de sortie.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "sorties-clonage"
DEFAULT_TEXT = ROOT / "narrations" / "texte.txt"
REFERENCE = ROOT / ".modeles" / "reference_tanguy.wav"


def vitesse(valeur: str) -> int:
    v = int(valeur)
    if not 60 <= v <= 130:
        raise ValueError("Vitesse attendue entre 60 et 130 %.")
    return v


def passages(texte: str, max_chars: int = 180) -> list[str]:
    """Couper sans rompre les mots, en privilégiant la fin des phrases."""
    if not texte.strip():
        raise ValueError("Texte vide.")
    if max_chars < 30:
        raise ValueError("max_chars trop petit.")
    phrases = re.split(r"(?<=[.!?])\s+|\n+", texte.strip())
    resultat: list[str] = []
    courant = ""
    for phrase in phrases:
        if not phrase:
            continue
        mots = phrase.split()
        for mot in mots:
            proposition = (courant + " " + mot).strip()
            if len(proposition) > max_chars and courant:
                resultat.append(courant)
                courant = mot
            else:
                courant = proposition
        if courant:
            resultat.append(courant)
            courant = ""
    return resultat


def exec_cmd(args: list[str]) -> None:
    subprocess.run(args, check=True)


def main() -> None:
    texte = os.getenv("DEEG_TEXT", "").strip() or DEFAULT_TEXT.read_text(encoding="utf-8").strip()
    if len(texte) > 5000:
        raise ValueError("Limiter le texte à 5000 caractères par lancement.")
    vitesse_pct = vitesse(os.getenv("DEEG_SPEED", "85"))
    chemin = Path(os.getenv("DEEG_REFERENCE_PATH", str(REFERENCE))).resolve()
    if not chemin.is_file():
        raise FileNotFoundError(
            "Référence introuvable. Ne l'ajoutez pas au dépôt public ; "
            "configurez le secret GitHub DEEG_TANGUY_REFERENCE_URL."
        )

    OUT.mkdir(exist_ok=True)
    # Les bibliothèques volumineuses sont importées uniquement pendant la génération.
    import torch
    import torchaudio
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS

    if torch.cuda.is_available():
        device = "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    print(f"Chatterbox V3 — dispositif: {device} ; langue: français", flush=True)
    model = ChatterboxMultilingualTTS.from_pretrained(device=device, t3_model="v3")
    model.prepare_conditionals(str(chemin), exaggeration=0.32)

    portions = passages(texte)
    resultat = []
    taille_silence = round(model.sr * 0.32)
    with torch.inference_mode():
        for i, part in enumerate(portions, start=1):
            print(f"Synthèse {i}/{len(portions)} ({len(part)} caractères)", flush=True)
            audio = model.generate(
                part,
                language_id="fr",
                exaggeration=0.32,
                cfg_weight=0.35,
                temperature=0.7,
            ).flatten().cpu()
            resultat.append(audio)
            if i < len(portions):
                resultat.append(torch.zeros(taille_silence, dtype=audio.dtype))

    brut = OUT / "narrateur_deeg_brut.wav"
    torchaudio.save(str(brut), torch.cat(resultat).unsqueeze(0), model.sr)

    wav = OUT / "narrateur_deeg.wav"
    mp3 = OUT / "narrateur_deeg.mp3"
    # atempo à 0,85 réduit la vitesse tout en préservant mieux la hauteur.
    exec_cmd(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
              "-i", str(brut), "-filter:a", f"atempo={vitesse_pct / 100:.3f}",
              "-ar", "48000", "-ac", "1", str(wav)])
    exec_cmd(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
              "-i", str(wav), "-codec:a", "libmp3lame", "-q:a", "3", str(mp3)])
    brut.unlink(missing_ok=True)
    (OUT / "texte_narre.txt").write_text(texte + "\n", encoding="utf-8")
    (OUT / "rapport.json").write_text(
        json.dumps({
            "moteur": "Chatterbox Multilingual V3",
            "mode": "adaptation par référence audio, sans réentraînement",
            "langue": "fr",
            "vitesse_pct": vitesse_pct,
            "dispositif": device,
            "fragments": len(portions),
            "remarque": "Voix approchante, fidélité et prononciation à contrôler manuellement.",
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("Audio généré, aucun enregistrement de référence dans les fichiers exportés.")


if __name__ == "__main__":
    main()
