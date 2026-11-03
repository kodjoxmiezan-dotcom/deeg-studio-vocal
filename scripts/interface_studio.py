"""Interface française locale pour le Studio Vocal DEEG.

L'interface écoute UNIQUEMENT sur 127.0.0.1 ; les références vocales ne sont
jamais envoyées vers GitHub. La première génération nécessite les poids
Chatterbox installés/téléchargés par le moteur (connexion Internet initiale).
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

from produire_voix_video_locale import produire, verifier_texte
from preparer_reference_video import preparer

OUTPUT = ROOT / "sorties-video-local"
TEXTE_DEFAUT = (
    "Bienvenue dans ATHÉNÉE, votre espace de formation. "
    "Ensemble, développons une école plus équitable et inclusive."
)


def _chemin(source: str | None) -> Path:
    if not source:
        raise ValueError("Sélectionnez d'abord la vidéo ou le fichier audio de référence.")
    chemin = Path(source).expanduser().resolve()
    if not chemin.is_file():
        raise FileNotFoundError("Enregistrement de référence introuvable.")
    return chemin


def diagnostiquer(source: str | None, texte: str, debut: float, vitesse: int) -> dict:
    """Préparation sans modèle de synthèse, résultat exploitable dans l'interface."""
    try:
        resultat = produire(
            source=_chemin(source),
            sortie=OUTPUT,
            texte=verifier_texte(texte),
            debut=float(debut),
            vitesse=int(vitesse),
            diagnostic=True,
        )
        return {"etat": "Référence validée techniquement", **resultat,
                "controle_humain": "Écouter la source : une seule voix et aucune musique."}
    except Exception as exc:
        return {"etat": "Échec du diagnostic", "erreur": str(exc)}



def previsualiser_reference(source: str | None, debut: float) -> tuple[str, str | None, dict]:
    """Écouter les 10 secondes qui serviront à la synthèse vocale."""
    sortie = OUTPUT / "reference_previsualisation.wav"
    sortie.unlink(missing_ok=True)
    try:
        chemin = _chemin(source)
        stats = preparer(chemin, sortie, float(debut), 10.0)
        return (
            "✅ Extrait préparé. Écoutez-le pour vérifier l'absence de musique, de bruit et de voix concurrentes.",
            str(sortie),
            {"extrait_secondes": round(stats["duree_secondes"], 2),
             "niveau_rms": round(stats["rms_normalise"], 4),
             "part_ecretee": round(stats["part_ecretee"], 6),
             "controle": "La qualité de la voix doit être évaluée à l'écoute."},
        )
    except Exception as exc:
        return "❌ Prévisualisation impossible : " + str(exc), None, {}


def generer(
    source: str | None,
    texte: str,
    debut: float,
    vitesse: int,
    consentement: bool,
) -> tuple[str, str | None, list[str], dict]:
    """Synthétise à partir d'une référence privée ; aucune voix source exportée."""
    if not consentement:
        return ("⚠️ Confirmez que vous disposez des droits nécessaires pour "
                "reproduire cette voix.", None, [], {})
    try:
        texte = verifier_texte(texte)
        resultat = produire(
            source=_chemin(source),
            sortie=OUTPUT,
            texte=texte,
            debut=float(debut),
            vitesse=int(vitesse),
            autorisation=True,
        )
    except Exception as exc:
        return ("❌ Génération impossible : " + str(exc), None, [], {})
    wav = OUTPUT / "DEEG_voix_video.wav"
    fichiers = [
        OUTPUT / "DEEG_voix_video.mp3",
        wav,
        OUTPUT / "DEEG_voix_video.srt",
        OUTPUT / "rapport.json",
        OUTPUT / "texte_narre.txt",
    ]
    if not all(p.is_file() for p in fichiers):
        return ("❌ Sorties incomplètes. Vérifiez le journal de génération.",
                None, [], resultat)
    return (
        "✅ **Essai créé.** Écoutez le résultat puis contrôlez le timbre, "
        "les intonations et la prononciation. Les sous-titres SRT sont estimatifs.",
        str(wav),
        [str(p) for p in fichiers],
        resultat,
    )


def creer_interface():
    """Chargement différé de Gradio : tests et diagnostic CLI sans dépendance UI."""
    import gradio as gr

    couleurs = """
    .gradio-container {max-width: 1100px !important; margin: auto;}
    .deeg-titre {border-left: 9px solid #F28C28; padding: 12px 18px;
                 background: linear-gradient(90deg, #fff6e8, #f7fcf8);}
    .deeg-titre h1 {color: #1c4835;}
    """
    source_initiale = os.getenv("DEEG_REFERENCE_INITIALE", "").strip()
    if source_initiale and not Path(source_initiale).is_file():
        source_initiale = ""
    with gr.Blocks(title="Studio Vocal DEEG — Voix vidéo", css=couleurs) as demo:
        gr.HTML('<div class="deeg-titre"><h1>🎙️ STUDIO VOCAL DEEG</h1>'
                '<p>Création de narrations en français à partir de votre '
                'référence vocale — mode privé sur cet ordinateur.</p></div>')
        gr.Markdown(
            "**Mode local uniquement :** la vidéo de référence reste sur votre "
            "ordinateur. Le premier usage peut nécessiter le téléchargement "
            "du modèle Chatterbox Multilingual V3. "
            "**Aucun modèle indépendant n'est entraîné.**"
        )
        with gr.Row():
            with gr.Column(scale=1):
                audio = gr.File(
                    label="1. Sélectionner la vidéo originale (20 s) ou un fichier audio",
                    file_types=[".mp4", ".mov", ".wav", ".mp3", ".m4a", ".aac"],
                    type="filepath",
                    value=source_initiale or None,
                )
                debut = gr.Slider(0, 60, value=0, step=1,
                                  label="Début de l'extrait de référence (10 s)")
                vitesse = gr.Slider(60, 130, value=85, step=5,
                                    label="Vitesse de lecture (%)")
                consentement = gr.Checkbox(
                    label="Je dispose des droits nécessaires pour reproduire cette voix.",
                    value=False,
                )
            with gr.Column(scale=2):
                texte = gr.Textbox(
                    label="2. Texte de la narration (500 caractères maximum)",
                    lines=5, max_lines=8, value=TEXTE_DEFAUT,
                    max_length=500,
                )
                with gr.Row():
                    btn_diagnostic = gr.Button("🔍 Vérifier la référence")
                    btn_previsualisation = gr.Button("▶ Écouter les 10 secondes choisies")
                    btn_generer = gr.Button("🎧 Générer la narration", variant="primary")
                resultat = gr.Markdown("Lancez un diagnostic ou la synthèse.")
                diagnostic = gr.JSON(label="Rapport technique")
                previsualisation = gr.Audio(label="Référence choisie : écouter avant génération", interactive=False)
        with gr.Row():
            ecoute = gr.Audio(label="Écouter la narration produite",
                              interactive=False)
            fichiers = gr.File(label="Télécharger MP3, WAV, SRT et rapport",
                               file_count="multiple")
        btn_diagnostic.click(
            fn=diagnostiquer,
            inputs=[audio, texte, debut, vitesse],
            outputs=[diagnostic],
        )
        btn_previsualisation.click(
            fn=previsualiser_reference,
            inputs=[audio, debut],
            outputs=[resultat, previsualisation, diagnostic],
            concurrency_limit=1,
        )
        btn_generer.click(
            fn=generer,
            inputs=[audio, texte, debut, vitesse, consentement],
            outputs=[resultat, ecoute, fichiers, diagnostic],
            concurrency_limit=1,
        )
        gr.Markdown(
            "📌 **Conseil :** privilégiez dix secondes de parole claire sans "
            "musique. Si la génération échoue sur un ordinateur sans GPU, "
            "essayez une phrase plus courte. Les résultats sont conservés dans "
            "le dossier local `sorties-video-local/`."
        )
    return demo


def main() -> None:
    os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    app = creer_interface()
    # Ne jamais changer l'hôte pour 0.0.0.0 ni activer share=True :
    # cela exposerait des échantillons sensibles sur le réseau.
    app.launch(
        server_name="127.0.0.1", server_port=7860,
        inbrowser=True, share=False,
        allowed_paths=[str(OUTPUT.resolve())],
        show_error=True,
    )


if __name__ == "__main__":
    main()
