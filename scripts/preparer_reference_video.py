"""Prépare un extrait vocal privé depuis un fichier audio ou vidéo local.

La référence n'est jamais publiée dans le dépôt ou les artefacts.
"""
from __future__ import annotations

import argparse
from array import array
import json
import math
from pathlib import Path
import subprocess
import sys
import wave


def inspecter(source: Path) -> float:
    if not source.is_file() or source.stat().st_size == 0:
        raise ValueError("Fichier source absent ou vide.")
    if source.stat().st_size > 20_000_000:
        raise ValueError("Source trop volumineuse (maximum 20 Mo).")
    resultat = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type",
         "-of", "json", str(source)],
        check=True, capture_output=True, text=True,
    )
    info = json.loads(resultat.stdout)
    if not any(p.get("codec_type") == "audio" for p in info.get("streams", [])):
        raise ValueError("Aucune piste audio détectée.")
    duree = float(info.get("format", {}).get("duration", 0))
    if not math.isfinite(duree) or duree < 5:
        raise ValueError("Enregistrement trop court : 5 secondes minimum.")
    if duree > 300:
        raise ValueError("Source trop longue : 5 minutes maximum.")
    return duree


def valider_parametres(debut: float, longueur: float, duree: float) -> None:
    if not math.isfinite(debut) or not math.isfinite(longueur):
        raise ValueError("Début et durée doivent être des valeurs finies.")
    if debut < 0 or not 5 <= longueur <= 20:
        raise ValueError("Début positif ou nul ; extrait entre 5 et 20 secondes.")
    if debut + longueur > duree + 0.05:
        raise ValueError("L'extrait dépasse la durée de la source.")


def qualite_audio(wav: Path) -> dict[str, float]:
    with wave.open(str(wav), "rb") as f:
        if f.getnchannels() != 1 or f.getframerate() != 24000 or f.getsampwidth() != 2:
            raise ValueError("Format WAV inattendu (attendu : mono 24 kHz / PCM16).")
        samples = array("h")
        samples.frombytes(f.readframes(f.getnframes()))
    if sys.byteorder == "big":
        samples.byteswap()
    if not samples:
        raise ValueError("Référence audio vide.")
    rms = math.sqrt(sum(int(s) ** 2 for s in samples) / len(samples)) / 32768
    ecretes = sum(abs(s) >= 32760 for s in samples) / len(samples)
    if rms < 0.002:
        raise ValueError("Volume trop faible ou extrait silencieux.")
    if ecretes > 0.03:
        raise ValueError("Écrêtage excessif : sélectionnez un autre passage.")
    return {"duree_secondes": len(samples) / 24000, "rms_normalise": rms,
            "part_ecretee": ecretes}


def preparer(source: Path, sortie: Path, debut: float, longueur: float) -> dict[str, float]:
    duree = inspecter(source)
    valider_parametres(debut, longueur, duree)
    sortie.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(source),
        "-ss", str(debut), "-t", str(longueur), "-vn", "-ar", "24000", "-ac", "1",
        "-c:a", "pcm_s16le", str(sortie),
    ], check=True)
    try:
        stats = qualite_audio(sortie)
    except Exception:
        sortie.unlink(missing_ok=True)
        raise
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--sortie", required=True, type=Path)
    parser.add_argument("--debut", required=True, type=float)
    parser.add_argument("--longueur", default=10, type=float)
    args = parser.parse_args()
    stats = preparer(args.source, args.sortie, args.debut, args.longueur)
    print("Référence préparée (privée), durée %.2fs, niveau RMS %.3f."
          % (stats["duree_secondes"], stats["rms_normalise"]))
    print("Vérifier à l'écoute : une seule voix, sans musique ni bruit de fond.")


if __name__ == "__main__":
    main()
