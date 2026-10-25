"""Synthèse vocale DEEG : MP3, WAV et SRT via Edge TTS ou Piper TTS."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "sorties"
TEXT_FILE = ROOT / "narrations" / "texte.txt"
MODELS = ROOT / ".modeles"


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


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    engine = os.getenv("DEEG_ENGINE", "edge").strip().lower()
    voice = os.getenv("DEEG_VOICE", "fr-FR-HenriNeural").strip()
    speed = check_speed(os.getenv("DEEG_SPEED", "85"))
    text = get_text()
    mp3 = OUTPUT / "deeg_narration.mp3"
    wav = OUTPUT / "deeg_narration.wav"
    srt = OUTPUT / "deeg_narration.srt"

    if engine == "edge":
        actual_voice = edge(text, voice, speed, mp3, wav, srt)
    elif engine == "piper":
        actual_voice = piper(text, voice, speed, mp3, wav, srt)
    else:
        raise ValueError(f"Moteur inconnu : {engine}")

    (OUTPUT / "texte_narre.txt").write_text(text + "\n", encoding="utf-8")
    (OUTPUT / "rapport.json").write_text(
        json.dumps({
            "moteur": engine,
            "voix": actual_voice,
            "vitesse_pct": speed,
            "duree_secondes": round(duration_seconds(wav), 2),
            "sous_titres": "horodatages_du_moteur" if engine == "edge" else "estimes_a_verifier",
            "note": "Les voix ne sont pas des clones de Tanguy de HeyGen.",
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Audio produit : {wav}, {mp3}, {srt}")


if __name__ == "__main__":
    main()
