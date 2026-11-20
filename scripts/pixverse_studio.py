"""Connecteur PixVerse pour Studio Audiovisuel Éboulé.

Simulation (défaut) : zéro requête et zéro débit de crédits.
Génération : nécessite API key + double confirmation et plafond indicatif.
Statut : lecture d'un video_id existant, sans nouvelle tâche de génération.
Aucune API/clé n'est écrite dans un fichier ou un journal.
Sources : docs.platform.pixverse.ai (API v2, tarifs V6 de novembre 2026).
"""
from __future__ import annotations

import json
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, request

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "pixverse" / "sorties"
BASE_URL = "https://app-api.pixverse.ai"
RATES_V6_NO_AUDIO = {"360p": 5, "540p": 7, "720p": 9, "1080p": 18}
RATIOS = {"16:9", "9:16", "1:1", "4:3", "3:4"}
DURATIONS = {5, 8, 10}
OPERATIONS = {"simulation", "generation", "statut"}
VIDEO_TYPES = {"texte", "image"}


def credits_estimes(duree: int, qualite: str) -> int:
    """Tarifs indicatifs PixVerse V6 sans piste audio, non plafonnement API."""
    if duree not in DURATIONS or qualite not in RATES_V6_NO_AUDIO:
        raise ValueError("Durée ou qualité non prise en charge dans ce pilote.")
    return duree * RATES_V6_NO_AUDIO[qualite]


def preparer_demande(mode: str, prompt: str, duree: int, qualite: str,
                     ratio: str, img_id: str = "") -> dict:
    if mode not in VIDEO_TYPES:
        raise ValueError("Mode vidéo attendu : texte ou image.")
    if not 10 <= len(prompt.strip()) <= 1500:
        raise ValueError("Décrire la scène sur 10 à 1 500 caractères.")
    credits_estimes(duree, qualite)
    if ratio not in RATIOS:
        raise ValueError("Format non pris en charge.")
    payload = {
        "model": "v6",
        "duration": duree,
        "quality": qualite,
        "prompt": prompt.strip(),
        "generate_audio_switch": False,
        "seed": 0,
    }
    if mode == "image":
        if not img_id or not re.fullmatch(r"[0-9]{1,20}", img_id) or int(img_id) <= 0:
            raise ValueError("Image vers vidéo : saisir un img_id PixVerse positif déjà téléversé.")
        payload["img_id"] = int(img_id)
    else:
        if img_id.strip():
            raise ValueError("Ne fournir un img_id que pour le mode image.")
        payload["aspect_ratio"] = ratio
    return payload


def autoriser_generation(autorisation: str, limite: str, estimation: int,
                        cle: str) -> int:
    if autorisation.lower() != "true":
        raise ValueError("Génération refusée : autorisation explicite des crédits manquante.")
    if not cle.strip():
        raise ValueError("Configurer le secret GitHub PIXVERSE_API_KEY avant toute génération.")
    try:
        maximum = int(limite)
    except (TypeError, ValueError) as exc:
        raise ValueError("Plafond indicatif de crédits invalide.") from exc
    if not estimation <= maximum <= 500:
        raise ValueError(
            f"Plafond indiqué insuffisant ou hors limites : prévoir au moins {estimation} crédits "
            "(500 au maximum pour ce pilote). Ceci ne bloque PAS une surfacturation fournisseur."
        )
    return maximum


def appel_api(methode: str, chemin: str, cle: str, donnees: dict | None = None) -> dict:
    """Appel limité au domaine API officiel. Aucun retry d'une création facturable."""
    if methode not in {"GET", "POST"} or not chemin.startswith("/openapi/v2/"):
        raise ValueError("Requête PixVerse non autorisée.")
    body = None if donnees is None else json.dumps(donnees).encode("utf-8")
    headers = {"API-KEY": cle, "Ai-trace-id": str(uuid.uuid4())}
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = request.Request(BASE_URL + chemin, data=body, headers=headers, method=methode)
    try:
        with request.urlopen(req, timeout=35) as res:
            resultat = json.loads(res.read(1_000_000).decode("utf-8"))
    except (error.HTTPError, error.URLError, TimeoutError) as exc:
        # Ne pas afficher la réponse brute, potentiellement sensible.
        code = getattr(exc, "code", "réseau")
        raise RuntimeError(f"PixVerse a refusé la requête ou le réseau est indisponible ({code}).") from None
    if not isinstance(resultat, dict) or resultat.get("ErrCode") != 0:
        code = resultat.get("ErrCode", "inconnu") if isinstance(resultat, dict) else "réponse"
        raise RuntimeError(f"PixVerse : code d'erreur métier {code}. Vérifier le compte et les paramètres.")
    if not isinstance(resultat.get("Resp"), dict):
        raise RuntimeError("PixVerse : corps de réponse incomplet.")
    return resultat["Resp"]


def lire_statut(cle: str, video_id: int) -> dict:
    if video_id <= 0:
        raise ValueError("Identifiant vidéo invalide.")
    return appel_api("GET", f"/openapi/v2/video/result/{video_id}", cle)


def surveiller(cle: str, video_id: int, essais: int = 24) -> dict:
    """Une seule tâche soumise ; maximum deux minutes de vérifications."""
    for i in range(essais):
        resultat = lire_statut(cle, video_id)
        etat = resultat.get("status")
        if etat in (1, 7, 8):
            return resultat
        if i + 1 < essais:
            time.sleep(5)
    return {"status": 5, "id": video_id, "note": "Encore en traitement. Utiliser mode statut."}


def rapport_initial(operation: str, mode: str, payload: dict | None,
                    credits: int | None) -> dict:
    return {
        "studio": "Studio Audiovisuel Éboulé",
        "fournisseur": "PixVerse API v2",
        "operation": operation,
        "mode_video": mode if operation != "statut" else None,
        "date_utc": datetime.now(timezone.utc).isoformat(),
        "simulation": operation == "simulation",
        "credits_estimes": credits,
        "cout_usd_indicatif": (round(credits / 225, 3) if credits is not None else None),
        "generation_audio": False,
        "requete": payload,
        "note_finance": (
            "Montant indicatif V6 sans audio (barème novembre 2026). "
            "Le vrai solde débité est déterminé par PixVerse ; le plafond indiqué "
            "par l'utilisateur n'est pas un verrou de facturation côté fournisseur."
        ),
        "confidentialite": (
            "Les artefacts GitHub d'un dépôt public sont consultables. "
            "Ne pas utiliser de scènes confidentielles."
        ),
    }


def ecrire_rapport(data: dict) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "rapport_pixverse.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def executer(environ: dict | None = None) -> dict:
    env = dict(os.environ) if environ is None else environ
    operation = env.get("PIXVERSE_OPERATION", "simulation").strip()
    if operation not in OPERATIONS:
        raise ValueError("Opération inconnue.")
    cle = env.get("PIXVERSE_API_KEY", "")
    if operation == "statut":
        if not cle:
            raise ValueError("Consultation impossible sans la clé PIXVERSE_API_KEY.")
        identifiant = env.get("PIXVERSE_VIDEO_ID", "")
        if not re.fullmatch(r"[0-9]{1,20}", identifiant) or int(identifiant) <= 0:
            raise ValueError("ID vidéo nécessaire pour consulter le statut.")
        vid = int(identifiant)
        resultat = lire_statut(cle, vid)
        r = rapport_initial(operation, "", None, None)
        r["video_id"] = vid
        r["statut"] = resultat.get("status")
        if env.get("PIXVERSE_PUBLIER_URL", "false").lower() == "true":
            url = resultat.get("url", "")
            if isinstance(url, str) and url.startswith("https://"):
                r["url"] = url
        ecrire_rapport(r)
        return r

    mode = env.get("PIXVERSE_MODE", "texte").strip()
    prompt = env.get("PIXVERSE_PROMPT") or (
        "Plan large d'une cour d'école primaire paisible au soleil du matin ; "
        "caméra fixe et mouvement léger des feuilles, scène documentaire."
    )
    duree = int(env.get("PIXVERSE_DUREE", "5"))
    qualite = env.get("PIXVERSE_QUALITE", "360p")
    ratio = env.get("PIXVERSE_RATIO", "16:9")
    img_id = env.get("PIXVERSE_IMG_ID", "").strip()
    payload = preparer_demande(mode, prompt, duree, qualite, ratio, img_id)
    estimation = credits_estimes(duree, qualite)
    rapport = rapport_initial(operation, mode, payload, estimation)

    if operation == "simulation":
        rapport["etat"] = "Simulation validée : aucun appel à PixVerse, aucun crédit utilisé."
        ecrire_rapport(rapport)
        return rapport

    autoriser_generation(
        env.get("PIXVERSE_AUTORISATION", "false"),
        env.get("PIXVERSE_CREDITS_MAX", "0"),
        estimation, cle,
    )
    route = (
        "/openapi/v2/video/text/generate" if mode == "texte"
        else "/openapi/v2/video/img/generate"
    )
    reponse = appel_api("POST", route, cle, payload)
    video_id = reponse.get("video_id")
    if not isinstance(video_id, int) or video_id <= 0:
        raise RuntimeError("PixVerse n'a pas retourné de video_id exploitable.")
    rapport["video_id"] = video_id
    rapport["credits_declares_par_api"] = reponse.get("credits")
    # Sauvegarde immédiate : en cas de délai, ne jamais créer un doublon facturable.
    rapport["etat"] = "Soumis, en attente de la génération."
    ecrire_rapport(rapport)
    resultat = surveiller(cle, video_id)
    rapport["statut"] = resultat.get("status")
    if rapport["statut"] == 1:
        rapport["etat"] = "Génération terminée."
    elif rapport["statut"] == 7:
        rapport["etat"] = "Échec de modération ; consulter PixVerse."
    elif rapport["statut"] == 8:
        rapport["etat"] = "Échec de génération ; contrôler le remboursement éventuel."
    else:
        rapport["etat"] = "Traitement toujours en cours. Rechercher le video_id via mode statut."
    if env.get("PIXVERSE_PUBLIER_URL", "false").lower() == "true":
        url = resultat.get("url")
        if isinstance(url, str) and url.startswith("https://"):
            rapport["url"] = url
    ecrire_rapport(rapport)
    return rapport


if __name__ == "__main__":
    resultat = executer()
    print(
        f"PixVerse : {resultat.get('etat', 'statut consulté')} "
        f"— vidéo {resultat.get('video_id', 'aucune')}. "
        "Le compte-rendu JSON est dans pixverse/sorties/."
    )
