"""Synthèse vocale DEEG : MP3, WAV et SRT via Edge TTS, Piper TTS ou une référence vidéo privée."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "sorties"
TEXT_FILE = ROOT / "narrations" / "texte.txt"
MODELS = ROOT / ".modeles"

CATALOGUE_VOIX = ROOT / "profils_vocaux" / "catalogue.json"


def charger_catalogue() -> dict:
    """Catalogue de présélections, sans poids IA ni référence vocale privée."""
    donnees = json.loads(CATALOGUE_VOIX.read_text(encoding="utf-8"))
    if donnees.get("version") != 1 or not isinstance(donnees.get("voix"), list):
        raise ValueError("Catalogue de voix invalide.")
    return donnees


def choisir_voix(moteur: str, presel: str, libre: str) -> str:
    """Choisit un profil sans changer les anciens réglages des workflows."""
    valeurs_defaut = {
        "edge": "fr-FR-HenriNeural",
        "piper": "fr_FR-tom-medium",
        "voix_video": "deeg_voix_video_2026_11",
    }
    if moteur not in valeurs_defaut:
        raise ValueError(f"Moteur inconnu : {moteur}")

    presel = (presel or "automatique").strip()
    if presel != "automatique":
        voix = {
            v["identifiant"]: v for v in charger_catalogue()["voix"]
        }.get(presel)
        if voix is None:
            raise ValueError(f"Présélection vocale inconnue : {presel}")
        if voix["moteur"] != moteur:
            raise ValueError(
                f"Présélection incompatible : {presel} ne fonctionne pas avec {moteur}."
            )
        return presel

    if moteur == "voix_video":
        return valeurs_defaut[moteur]
    if moteur == "piper":
        # Compatibilité : l'ancien workflow donnait Henri comme valeur
        # de champ, même lorsque le moteur Piper était sélectionné.
        return libre if libre.startswith("fr_FR-") else valeurs_defaut[moteur]
    return libre or valeurs_defaut[moteur]



def check_speed(value: str) -> int:
    try:
        speed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Vitesse invalide : nombre entier entre 60 et 130.") from exc
    if not 60 <= speed <= 130:
        raise ValueError("Vitesse autorisée : de 60 à 130 %.")
    return speed


def get_text() -> str:
    supplied = os.getenv("DEEG_TEXT", "").strip()
    text = supplied or TEXT_FILE.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError("Le texte à narrer est vide.")
    if len(text) > 15000:
        raise ValueError("Texte trop long : 15000 caractères maximum.")
    return text


def run(args: list[str]) -> None:
    subprocess.run(args, check=True)


def duration_seconds(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        check=True, capture_output=True, text=True,
    )
    return float(result.stdout.strip())


def stamp(seconds: float) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, remaining = divmod(milliseconds, 3600000)
    minutes, remaining = divmod(remaining, 60000)
    sec, millis = divmod(remaining, 1000)
    return f"{hours:02d}:{minutes:02d}:{sec:02d},{millis:03d}"


def estimate_srt(text: str, duration: float, target: Path) -> None:
    """Sous-titres Piper approximatifs : vérifier le minutage avant montage."""
    sentences = [
        s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()
    ]
    if not sentences:
        sentences = [text]
    weights = [max(len(s), 1) for s in sentences]
    total = sum(weights)
    position = 0.0
    with target.open("w", encoding="utf-8") as output:
        for i, (sentence, weight) in enumerate(zip(sentences, weights), start=1):
            end = min(duration, position + duration * weight / total)
            if i == len(sentences):
                end = duration
            output.write(f"{i}\n{stamp(position)} --> {stamp(end)}\n{sentence}\n\n")
            position = end


def edge(text: str, voice: str, speed: int, mp3: Path, wav: Path, srt: Path) -> str:
    if not re.fullmatch(r"fr-[A-Za-z]{2}-[A-Za-z0-9]+Neural", voice):
        raise ValueError("Voix Edge invalide, exemple : fr-FR-HenriNeural")
    run([
        "edge-tts", "--voice", voice, f"--rate={speed - 100:+d}%",
        "--text", text, "--write-media", str(mp3), "--write-subtitles", str(srt),
    ])
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp3),
         "-ac", "1", "-ar", "48000", str(wav)])
    return voice


def piper(text: str, voice: str, speed: int, mp3: Path, wav: Path, srt: Path) -> str:
    if not voice.startswith("fr_FR-"):
        voice = "fr_FR-tom-medium"
    if not re.fullmatch(r"fr_FR-[A-Za-z0-9_-]+", voice):
        raise ValueError("Voix Piper invalide.")
    MODELS.mkdir(parents=True, exist_ok=True)
    run([sys.executable, "-m", "piper.download_voices", "--data-dir", str(MODELS), voice])
    temporary = OUTPUT / "piper_brut.wav"
    run([sys.executable, "-m", "piper", "--data-dir", str(MODELS),
         "-m", voice, "-f", str(temporary), "--", text])
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(temporary),
         "-filter:a", f"atempo={speed / 100:.3f}",
         "-ac", "1", "-ar", "48000", str(wav)])
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav),
         "-codec:a", "libmp3lame", "-qscale:a", "3", str(mp3)])
    temporary.unlink(missing_ok=True)
    estimate_srt(text, duration_seconds(wav), srt)
    return voice


def voix_video(text: str, speed: int, mp3: Path, wav: Path, srt: Path) -> str:
    """Synthèse avec la référence privée de la vidéo, sans réentraînement."""
    if len(text) > 500:
        raise ValueError("Voix vidéo : 500 caractères maximum par essai CPU.")
    reference = Path(os.getenv(
        "DEEG_REFERENCE_PATH", str(MODELS / "reference_video.wav")
    )).resolve()
    if not reference.is_file():
        raise FileNotFoundError(
            "Référence privée absente. Configurer le secret "
            "DEEG_VIDEO_VOICE_REFERENCE_URL ou utiliser un fichier WAV local."
        )
    commande = [sys.executable, str(ROOT / "scripts" / "cloner_voix.py")]
    environnement = dict(os.environ, DEEG_TEXT=text, DEEG_SPEED=str(speed),
                         DEEG_REFERENCE_PATH=str(reference))
    subprocess.run(commande, check=True, env=environnement)
    resultat = ROOT / "sorties-clonage"
    shutil.copyfile(resultat / "narrateur_deeg.wav", wav)
    shutil.copyfile(resultat / "narrateur_deeg.mp3", mp3)
    estimate_srt(text, duration_seconds(wav), srt)
    return "deeg_voix_video_2026_11"


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    engine = os.getenv("DEEG_ENGINE", "edge").strip().lower()
    choix_catalogue = os.getenv("DEEG_VOICE_CATALOGUE", "automatique").strip()
    voice = choisir_voix(engine, choix_catalogue, os.getenv("DEEG_VOICE", "fr-FR-HenriNeural").strip())
    speed = check_speed(os.getenv("DEEG_SPEED", "85"))
    text = get_text()
    mp3 = OUTPUT / "deeg_narration.mp3"
    wav = OUTPUT / "deeg_narration.wav"
    srt = OUTPUT / "deeg_narration.srt"

    if engine == "edge":
        actual_voice = edge(text, voice, speed, mp3, wav, srt)
    elif engine == "piper":
        actual_voice = piper(text, voice, speed, mp3, wav, srt)
    elif engine == "voix_video":
        actual_voice = voix_video(text, speed, mp3, wav, srt)
    else:
        raise ValueError(f"Moteur inconnu : {engine}")

    (OUTPUT / "texte_narre.txt").write_text(text + "\n", encoding="utf-8")
    (OUTPUT / "rapport.json").write_text(
        json.dumps({
            "moteur": engine,
            "voix": actual_voice,
            "selection_catalogue": choix_catalogue,
            "vitesse_pct": speed,
            "duree_secondes": round(duration_seconds(wav), 2),
            "sous_titres": "horodatages_du_moteur" if engine == "edge" else "estimes_a_verifier",
            "note": ("Synthèse conditionnée par une référence privée de la vidéo ; "
                     "fidelité à contrôler à l’écoute. Aucun modèle réentraîné."
                     if engine == "voix_video" else
                     "Les moteurs Edge et Piper ne reproduisent pas la voix Tanguy de HeyGen."),
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Audio produit : {wav}, {mp3}, {srt}")


if __name__ == "__main__":
    main()
