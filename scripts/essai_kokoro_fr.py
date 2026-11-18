"""Essai isolé de Kokoro-82M (français) sans modifier le studio principal.

Utilisation : DEEG_TEXT="Votre texte" DEEG_SPEED=85 python scripts/essai_kokoro_fr.py
Les poids sont téléchargés depuis Hugging Face lors de la première exécution.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "sorties-kokoro"
EXEMPLE = (
    "Bienvenue dans le studio vocal. Chaque matin, à l'école, les filles et "
    "les garçons apprennent ensemble. Le rôle de chaque adulte est de créer "
    "un environnement protecteur et inclusif."
)


def verifier_texte(texte: str) -> str:
    texte = (texte or "").strip()
    if not texte:
        raise ValueError("Saisir un texte français pour la synthèse Kokoro.")
    if len(texte) > 800:
        raise ValueError("Essai Kokoro : 800 caractères maximum.")
    return texte


def verifier_vitesse(valeur: str) -> int:
    try:
        vitesse = int(valeur)
    except (ValueError, TypeError) as exc:
        raise ValueError("Vitesse Kokoro invalide.") from exc
    if not 60 <= vitesse <= 130:
        raise ValueError("Vitesse Kokoro attendue entre 60 et 130 %.")
    return vitesse


def main() -> None:
    texte = verifier_texte(os.getenv("DEEG_TEXT", "").strip() or EXEMPLE)
    vitesse = verifier_vitesse(os.getenv("DEEG_SPEED", "85"))
    OUTPUT.mkdir(parents=True, exist_ok=True)

    # Imports lourds uniquement à la génération, pour permettre les tests sans modèle.
    import numpy as np
    import soundfile as sf
    from kokoro import KPipeline
    from generer import duration_seconds, estimate_srt

    pipeline = KPipeline(lang_code="f")
    morceaux = []
    frequence = 24000
    for numero, (_texte, _phonemes, audio) in enumerate(
        pipeline(texte, voice="ff_siwis", speed=1.0, split_pattern=r"\n+"), start=1
    ):
        if hasattr(audio, "detach"):
            audio = audio.detach().cpu().numpy()
        signal = np.asarray(audio, dtype=np.float32).reshape(-1)
        if signal.size:
            if morceaux:
                morceaux.append(np.zeros(int(frequence * 0.30), dtype=np.float32))
            morceaux.append(signal)
            print(f"Segment Kokoro {numero} produit : {signal.size} echantillons", flush=True)
    if not morceaux:
        raise RuntimeError("Kokoro n'a produit aucun signal audio.")

    brut = OUTPUT / "kokoro_original_24k.wav"
    sf.write(brut, np.concatenate(morceaux), frequence)
    wav = OUTPUT / "kokoro_fr_deeg.wav"
    mp3 = OUTPUT / "kokoro_fr_deeg.mp3"
    srt = OUTPUT / "kokoro_fr_deeg.srt"
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(brut), "-filter:a", f"atempo={vitesse / 100:.3f}",
        "-ar", "48000", "-ac", "1", str(wav),
    ], check=True)
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(wav), "-codec:a", "libmp3lame", "-q:a", "3", str(mp3),
    ], check=True)
    brut.unlink(missing_ok=True)
    duree = duration_seconds(wav)
    estimate_srt(texte, duree, srt)
    (OUTPUT / "texte_narre.txt").write_text(texte + "\n", encoding="utf-8")
    (OUTPUT / "rapport.json").write_text(
        json.dumps({
            "moteur": "Kokoro 82M",
            "voix": "ff_siwis",
            "langue": "fr",
            "vitesse_pct": vitesse,
            "duree_secondes": round(duree, 2),
            "statut": "experimental, validation a l'ecoute requise",
            "srt": "estimation, non forcee sur l'audio",
            "reference_privee": False,
            "source_modele": "hexgrad/Kokoro-82M",
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("Essai Kokoro terminé : MP3, WAV et SRT exportés.", flush=True)


if __name__ == "__main__":
    main()
