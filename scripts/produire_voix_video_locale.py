"""Créer un essai vocal DEEG directement depuis une vidéo locale, sans GitHub secret.

Exemple (diagnostic sans modèle IA) :
  python scripts/produire_voix_video_locale.py --source video.mp4 --diagnostic

Exemple (synthèse avec consentement et Chatterbox installé) :
  python scripts/produire_voix_video_locale.py --source video.mp4 \
    --texte "Bienvenue dans la formation DEEG." --autorisation
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from preparer_reference_video import preparer
from generer import check_speed, duration_seconds, estimate_srt

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEXTE = "Bienvenue dans le studio vocal DEEG. Ensemble, construisons une école plus équitable."


def verifier_texte(texte: str) -> str:
    texte = texte.strip()
    if not 1 <= len(texte) <= 500:
        raise ValueError("Pour cet essai sur ordinateur : texte de 1 à 500 caractères.")
    return texte


def produire(
    source: Path,
    sortie: Path,
    texte: str,
    debut: float = 0.0,
    vitesse: int = 85,
    autorisation: bool = False,
    diagnostic: bool = False,
) -> dict:
    """Préparer 10 s d'audio et, sauf diagnostic, créer MP3/WAV/SRT privés."""
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("FFmpeg et FFprobe sont requis. Sur Mac : brew install ffmpeg")
    vitesse = check_speed(str(vitesse))
    texte = verifier_texte(texte)
    if not diagnostic and not autorisation:
        raise PermissionError(
            "Confirmation requise : fournissez --autorisation uniquement si "
            "vous avez le droit de reproduire cette voix."
        )

    with tempfile.TemporaryDirectory(prefix="deeg_reference_privee_") as tmp:
        reference = Path(tmp) / "reference.wav"
        mesures = preparer(source.expanduser().resolve(), reference, debut, 10.0)
        rapport = {
            "source": source.name,
            "profil": "deeg_voix_video_2026_11",
            "duree_reference_secondes": round(mesures["duree_secondes"], 2),
            "rms_normalise": round(mesures["rms_normalise"], 4),
            "ecretage_fraction": round(mesures["part_ecretee"], 6),
            "vitesse_pct": vitesse,
            "mode": "diagnostic" if diagnostic else "synthese_reference",
            "avertissement": (
                "Vérifier à l'écoute : une seule voix, absence de musique, prononciation, timbre. "
                "Le moteur utilise un conditionnement vocal et ne réentraîne pas de modèle."
            ),
        }
        if diagnostic:
            return rapport

        variables = dict(
            os.environ,
            DEEG_REFERENCE_PATH=str(reference),
            DEEG_TEXT=texte,
            DEEG_SPEED=str(vitesse),
        )
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "cloner_voix.py")],
            cwd=str(ROOT), env=variables, check=True,
        )

        provenance = ROOT / "sorties-clonage"
        noms = {
            "narrateur_deeg.wav": "DEEG_voix_video.wav",
            "narrateur_deeg.mp3": "DEEG_voix_video.mp3",
            "texte_narre.txt": "texte_narre.txt",
        }
        sortie = sortie.expanduser().resolve()
        sortie.mkdir(parents=True, exist_ok=True)
        for origine, destination in noms.items():
            shutil.copyfile(provenance / origine, sortie / destination)
        chemin_wav = sortie / "DEEG_voix_video.wav"
        estimate_srt(texte, duration_seconds(chemin_wav),
                     sortie / "DEEG_voix_video.srt")
        rapport["duree_synthese_secondes"] = round(duration_seconds(chemin_wav), 2)
        rapport["sous_titres"] = "estimation à vérifier"
        (sortie / "rapport.json").write_text(
            json.dumps(rapport, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return rapport


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True,
                   help="Vidéo de 20 secondes ou enregistrement WAV/MP3 local")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--texte", default=None, help="Phrase française à narrer")
    g.add_argument("--texte-fichier", type=Path, default=None,
                   help="Fichier UTF-8 contenant la narration")
    p.add_argument("--debut", type=float, default=0.0,
                   help="Seconde de début de la référence de 10 s (défaut : 0)")
    p.add_argument("--vitesse", type=int, default=85,
                   help="Vitesse en pourcentage de 60 à 130 (défaut : 85)")
    p.add_argument("--sortie", type=Path, default=ROOT / "sorties-video-local",
                   help="Dossier privé de sortie")
    p.add_argument("--diagnostic", action="store_true",
                   help="Valider l'extraction sans installer ni exécuter Chatterbox")
    p.add_argument("--autorisation", action="store_true",
                   help="Confirme avoir le droit de reproduire la voix de référence")
    args = p.parse_args(argv)
    texte = (args.texte_fichier.read_text(encoding="utf-8") if args.texte_fichier
             else args.texte if args.texte is not None else DEFAULT_TEXTE)
    rapport = produire(args.source, args.sortie, texte, args.debut, args.vitesse,
                      args.autorisation, args.diagnostic)
    print(json.dumps(rapport, ensure_ascii=False, indent=2))
    if args.diagnostic:
        print("Diagnostic réussi. Aucun modèle ni fichier vocal publié.")
    else:
        print("Fichiers MP3, WAV et SRT créés dans :", args.sortie.resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
