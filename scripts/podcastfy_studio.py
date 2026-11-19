"""Podcasts français à deux voix grâce à Podcastfy + Edge TTS.

Mode dialogue : gratuit sans clé API ; dialogue déjà rédigé.
Mode ia_gemini : transforme un texte source en dialogue avec Gemini (opt-in),
puis crée l'audio par Edge. Les coûts/quotas dépendent du fournisseur.
"""
from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PODCASTS = ROOT / "podcasts"
SORTIES = PODCASTS / "sorties"
EXEMPLE = PODCASTS / "exemple_dialogue.txt"
EXEMPLE_SOURCE = PODCASTS / "exemple_source.txt"

VOIX_FR = {
    "fr-FR-DeniseNeural",
    "fr-FR-EloiseNeural",
    "fr-FR-VivienneMultilingualNeural",
    "fr-FR-HenriNeural",
    "fr-FR-RemyMultilingualNeural",
}
ETIQUETTES = {
    "ANIMATRICE": "Person1",
    "ANIMATEUR": "Person1",
    "HOTE": "Person1",
    "HÔTE": "Person1",
    "PERSON1": "Person1",
    "EXPERT": "Person2",
    "EXPERTE": "Person2",
    "INVITE": "Person2",
    "INVITÉ": "Person2",
    "INVITEE": "Person2",
    "INVITÉE": "Person2",
    "PERSON2": "Person2",
}


def verifier_voix(voix_a: str, voix_b: str) -> tuple[str, str]:
    if voix_a not in VOIX_FR or voix_b not in VOIX_FR:
        raise ValueError("Sélectionnez deux voix françaises proposées dans le studio.")
    if voix_a == voix_b:
        raise ValueError("Sélectionnez deux voix différentes pour le podcast.")
    return voix_a, voix_b


def verifier_mode(mode: str, cle: str, consentement: str) -> None:
    if mode not in {"dialogue", "ia_gemini"}:
        raise ValueError("Mode inconnu : choisissez dialogue ou ia_gemini.")
    if mode == "ia_gemini":
        if consentement.lower() != "true":
            raise ValueError("L'utilisation facultative de Gemini doit être autorisée.")
        if not cle.strip():
            raise ValueError(
                "Clé absente : configurer le secret GitHub PODCAST_GEMINI_API_KEY. "
                "Le mode dialogue fonctionne sans aucune clé."
            )


def lignes_dialogue(texte: str) -> list[tuple[str, str]]:
    """Analyse des lignes « ANIMATRICE: ... » puis « EXPERT: ... ».
    
    L'interface GitHub accepte aussi un séparateur ' | ' sur une seule ligne.
    """
    texte = (texte or "").strip()
    if not texte or len(texte) > 10000:
        raise ValueError("Dialogue vide ou trop long : 10 000 caractères maximum.")
    lignes = [part.strip() for part in re.split(r"\r?\n|\s+\|\s+", texte) if part.strip()]
    if len(lignes) < 2 or len(lignes) > 40 or len(lignes) % 2:
        raise ValueError("Prévoir de 1 à 20 paires ANIMATRICE puis EXPERT.")
    tours = []
    for i, ligne in enumerate(lignes):
        match = re.fullmatch(r"([^:：]+)[:：]\s*(.+)", ligne, flags=re.DOTALL)
        if not match:
            raise ValueError(f"Ligne {i + 1} : utiliser ANIMATRICE: texte ou EXPERT: texte.")
        etiquette = match.group(1).strip().upper()
        locuteur = ETIQUETTES.get(etiquette)
        if locuteur != ("Person1" if i % 2 == 0 else "Person2"):
            raise ValueError(f"Ligne {i + 1} : alterner ANIMATRICE et EXPERT.")
        contenu = match.group(2).strip()
        if not contenu:
            raise ValueError(f"Ligne {i + 1} : réplique vide.")
        if len(contenu) > 1200:
            raise ValueError(f"Ligne {i + 1} : réplique trop longue pour un essai.")
        tours.append((locuteur, contenu))
    return tours


def baliser(tours: list[tuple[str, str]]) -> str:
    return "\n".join(
        f"<{speaker}>{html.escape(texte, quote=False)}</{speaker}>"
        for speaker, texte in tours
    ) + "\n"


def dialogue_lisible(tours: list[tuple[str, str]]) -> str:
    return "\n".join(
        f"{'ANIMATRICE' if speaker == 'Person1' else 'EXPERT'} : {texte}"
        for speaker, texte in tours
    ) + "\n"


def extraire_dialogue_balise(texte: str) -> list[tuple[str, str]]:
    expression = r"<(Person1|Person2)>(.*?)</\1>"
    resultat = [
        (speaker, html.unescape(" ".join(contenu.split())))
        for speaker, contenu in re.findall(expression, texte, flags=re.DOTALL)
        if contenu.strip()
    ]
    return resultat


def configuration(voix_a: str, voix_b: str) -> dict:
    return {
        "podcast_name": "Studio Vocal Éboulé",
        "podcast_tagline": "Des savoirs qui prennent la parole",
        "output_language": "French",
        "conversation_style": ["pédagogique", "naturel", "accessible"],
        "roles_person1": "animatrice",
        "roles_person2": "expert",
        "creativity": 0.3,
        "word_count": 280,
        "user_instructions": (
            "Présente exclusivement les idées appuyées par le texte fourni ; "
            "dialogue français clair entre animatrice et expert, questions "
            "pertinentes, sans informations inventées ni promotions."
        ),
        "text_to_speech": {
            "default_tts_model": "edge",
            "edge": {"default_voices": {
                "question": voix_a, "answer": voix_b,
            }},
            "output_directories": {
                "transcripts": str(SORTIES / "transcripts"),
                "audio": str(SORTIES / "audio"),
            },
            "audio_format": "mp3",
            "ending_message": "Merci et à bientôt pour un nouvel épisode.",
        },
    }


def source_validee(texte: str) -> str:
    texte = (texte or "").strip()
    if not texte or len(texte) > 8000:
        raise ValueError("Texte source requis : 1 à 8 000 caractères maximum.")
    return texte


def duree_audio(chemin: Path) -> float:
    resultat = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(chemin)],
        check=True, capture_output=True, text=True,
    )
    return float(resultat.stdout.strip())


def sous_titres(tours: list[tuple[str, str]], duree: float, cible: Path) -> None:
    """Minutage proportionnel : il n'est PAS un alignement mot par mot."""
    if not tours:
        cible.write_text("", encoding="utf-8")
        return
    poids = [max(len(texte), 1) for _, texte in tours]
    total = sum(poids)
    t = 0.0

    def horodatage(secondes: float) -> str:
        millis = max(0, round(secondes * 1000))
        heures, reste = divmod(millis, 3600000)
        minutes, reste = divmod(reste, 60000)
        secondes_entieres, ms = divmod(reste, 1000)
        return f"{heures:02d}:{minutes:02d}:{secondes_entieres:02d},{ms:03d}"

    with cible.open("w", encoding="utf-8") as fichier:
        for i, ((speaker, texte), p) in enumerate(zip(tours, poids), start=1):
            fin = duree if i == len(tours) else min(duree, t + duree * p / total)
            label = "Animatrice" if speaker == "Person1" else "Expert"
            fichier.write(f"{i}\n{horodatage(t)} --> {horodatage(fin)}\n{label} : {texte}\n\n")
            t = fin


def produire() -> dict:
    mode = os.getenv("PODCAST_MODE", "dialogue").strip()
    verifier_mode(
        mode,
        os.getenv("GEMINI_API_KEY", ""),
        os.getenv("PODCAST_AUTORISATION_API", "false"),
    )
    voix_a, voix_b = verifier_voix(
        os.getenv("PODCAST_VOIX_A", "fr-FR-DeniseNeural"),
        os.getenv("PODCAST_VOIX_B", "fr-FR-HenriNeural"),
    )

    SORTIES.mkdir(parents=True, exist_ok=True)
    cfg = configuration(voix_a, voix_b)

    # Le mode gratuit utilise directement le fournisseur TTS de Podcastfy.
    # Ainsi, son import n'exige pas les extracteurs web/Playwright de Podcastfy.
    if mode == "dialogue":
        from podcastfy.text_to_speech import TextToSpeech
        contenu = os.getenv("PODCAST_DIALOGUE", "").strip() or EXEMPLE.read_text(encoding="utf-8")
        tours = lignes_dialogue(contenu)
        texte_balise = baliser(tours)
        transcription = SORTIES / "transcription_podcastfy.txt"
        transcription.write_text(texte_balise, encoding="utf-8")
        chemin_audio = SORTIES / "audio" / "podcastfy_direct.mp3"
        chemin_audio.parent.mkdir(parents=True, exist_ok=True)
        TextToSpeech(model="edge", conversation_config=cfg).convert_to_speech(
            texte_balise, str(chemin_audio)
        )
    else:
        # Le mode automatique utilise l'API principale de Podcastfy, avec IA
        # explicitement autorisée et une clé fournie par secret GitHub.
        from podcastfy.client import generate_podcast
        contenu = (
            os.getenv("PODCAST_SOURCE", "").strip()
            or EXEMPLE_SOURCE.read_text(encoding="utf-8")
        )
        texte_source = source_validee(contenu)
        anciens = set((SORTIES / "transcripts").glob("*.txt"))
        chemin_audio = generate_podcast(
            text=texte_source,
            tts_model="edge",
            conversation_config=cfg,
            llm_model_name="gemini-2.5-flash",
            api_key_label="GEMINI_API_KEY",
            longform=False,
        )
        nouveaux = list(set((SORTIES / "transcripts").glob("*.txt")) - anciens)
        if len(nouveaux) != 1:
            raise RuntimeError("Transcription IA introuvable ou ambiguë après génération.")
        texte_balise = nouveaux[0].read_text(encoding="utf-8")
        transcription = SORTIES / "transcription_podcastfy.txt"
        transcription.write_text(texte_balise, encoding="utf-8")
        tours = extraire_dialogue_balise(texte_balise)
        if not tours:
            raise RuntimeError("Dialogue IA non conforme au format Podcastfy.")

    if not chemin_audio or not Path(chemin_audio).is_file():
        raise RuntimeError("Podcastfy n'a pas retourné de fichier audio exploitable.")

    mp3 = SORTIES / "studio_eboule_podcast.mp3"
    wav = SORTIES / "studio_eboule_podcast.wav"
    chemin_audio = Path(chemin_audio).resolve()
    if chemin_audio != mp3.resolve():
        shutil.copyfile(chemin_audio, mp3)
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(mp3), "-ar", "48000", "-ac", "1", str(wav),
    ], check=True)

    duree = duree_audio(wav)
    sous_titres(tours, duree, SORTIES / "studio_eboule_podcast.srt")
    (SORTIES / "dialogue_lisible.txt").write_text(dialogue_lisible(tours), encoding="utf-8")
    rapport = {
        "studio": "Studio Vocal Éboulé",
        "moteur_podcast": "Podcastfy",
        "mode": mode,
        "voix_a": voix_a,
        "voix_b": voix_b,
        "tts": "Edge TTS (clé non requise)",
        "ia_externe": mode == "ia_gemini",
        "fournisseur_ia": "Gemini (optionnel)" if mode == "ia_gemini" else None,
        "duree_secondes": round(duree, 2),
        "tours": len(tours),
        "sous_titres": "estimes, synchronisation à vérifier à l'écoute",
        "licence_podcastfy": "Apache-2.0",
        "confidentialite": "GitHub Actions sur dépôt public : les artefacts ne sont pas privés",
    }
    (SORTIES / "rapport.json").write_text(
        json.dumps(rapport, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Podcast créé : {mp3} ({duree:.1f} s).")
    return rapport


if __name__ == "__main__":
    produire()
