"""Comparer deux réglages vocaux Chatterbox V3, sans publier les références privées."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "sorties-optimisation"
REF_FOLDER = ROOT / ".modeles"

PROFILES = (
    {
        "id": "A_fidelite",
        "label": "Fidélité du timbre",
        "ref": "tanguy_explicatif.wav",
        "exaggeration": 0.38,
        "cfg_weight": 0.48,
        "temperature": 0.66,
        "repetition_penalty": 1.15,
    },
    {
        "id": "B_institutionnel",
        "label": "Intonation institutionnelle",
        "ref": "tanguy_pose.wav",
        "exaggeration": 0.26,
        "cfg_weight": 0.30,
        "temperature": 0.68,
        "repetition_penalty": 1.16,
    },
)


def valid_speed(value: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Vitesse invalide.") from exc
    if not 60 <= number <= 130:
        raise ValueError("Vitesse autorisée de 60 à 130 %.")
    return number


def get_text() -> str:
    custom = os.getenv("DEEG_TEXT", "").strip()
    text = custom or (ROOT / "narrations" / "texte.txt").read_text(encoding="utf-8").strip()
    if not (1 <= len(text) <= 600):
        raise ValueError("L'essai doit contenir entre 1 et 600 caractères.")
    return text


def command(args: list[str]) -> None:
    subprocess.run(args, check=True)


def make_audio(model, torch, text: str, profile: dict, speed: int, device: str) -> dict:
    ref_path = REF_FOLDER / profile["ref"]
    if not ref_path.exists():
        raise FileNotFoundError("Référence manquante : " + profile["ref"])
    import torchaudio

    print(f"Profil {profile['id']} : chargement de la référence privée...", flush=True)
    model.prepare_conditionals(str(ref_path), exaggeration=profile["exaggeration"])
    print(f"Profil {profile['id']} : génération française...", flush=True)
    with torch.inference_mode():
        tensor = model.generate(
            text,
            language_id="fr",
            exaggeration=profile["exaggeration"],
            cfg_weight=profile["cfg_weight"],
            temperature=profile["temperature"],
            repetition_penalty=profile["repetition_penalty"],
        )

    original = OUTPUT / (profile["id"] + "_brut.wav")
    wav = OUTPUT / (profile["id"] + ".wav")
    mp3 = OUTPUT / (profile["id"] + ".mp3")
    torchaudio.save(str(original), tensor.detach().cpu(), model.sr)

    # Ralentissement sans changement de hauteur; traitement léger de la dynamique.
    command([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(original),
        "-af", f"atempo={speed / 100:.3f},highpass=f=65,loudnorm=I=-18:TP=-2.5:LRA=11",
        "-ac", "1", "-ar", "48000", str(wav),
    ])
    command([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(wav), "-codec:a", "libmp3lame", "-q:a", "3", str(mp3),
    ])
    original.unlink(missing_ok=True)
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nokey=1:noprint_wrappers=1", str(wav)],
        capture_output=True, check=True, text=True,
    )
    return {
        "nom": profile["id"],
        "description": profile["label"],
        "exaggeration": profile["exaggeration"],
        "cfg_weight": profile["cfg_weight"],
        "temperature": profile["temperature"],
        "duree_secondes": round(float(probe.stdout.strip()), 2),
        "wav": wav.name,
        "mp3": mp3.name,
        "moteur": "Chatterbox Multilingual V3",
        "device": device,
    }


def main() -> None:
    speed = valid_speed(os.getenv("DEEG_SPEED", "85"))
    text = get_text()
    OUTPUT.mkdir(exist_ok=True)
    import torch
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Comparaison DEEG : {device}, voix française, vitesse {speed} %", flush=True)
    model = ChatterboxMultilingualTTS.from_pretrained(device=device, t3_model="v3")

    results = []
    for profile in PROFILES:
        results.append(make_audio(model, torch, text, profile, speed, device))
    (OUTPUT / "texte_identique_pour_les_deux.txt").write_text(text + "\n", encoding="utf-8")
    (OUTPUT / "rapport_comparatif.json").write_text(
        json.dumps({
            "description": "Deux variantes expérimentales sur le même texte.",
            "vitesse": speed,
            "profils": results,
            "reference_audio_publiee": False,
            "attention": "Les réglages sont des hypothèses à juger à l'écoute ; "
                         "ils ne démontrent pas une meilleure similarité acoustique.",
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("Deux variantes terminées. La référence privée n'est pas exportée.", flush=True)


if __name__ == "__main__":
    main()
