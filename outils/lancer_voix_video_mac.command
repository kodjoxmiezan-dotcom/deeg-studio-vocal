#!/bin/bash
# Lancement local DEEG : référence privée, aucun téléversement de voix vers GitHub.
set -euo pipefail
cd "$(dirname "$0")/.."
RACINE="$(pwd)"

if [[ $# -gt 0 ]]; then
  SOURCE="$1"
else
  printf "Chemin de la vidéo source de 20 secondes : "
  IFS= read -r SOURCE
fi
SOURCE="${SOURCE/#\~/$HOME}"
if [[ ! -f "$SOURCE" ]]; then
  echo "ERREUR : vidéo introuvable : $SOURCE"
  exit 1
fi

for outil in git ffmpeg ffprobe; do
  if ! command -v "$outil" >/dev/null; then
    echo "ERREUR : $outil est nécessaire ; installer FFmpeg avec Homebrew : brew install ffmpeg"
    exit 1
  fi
done
if ! command -v python3.11 >/dev/null; then
  echo "ERREUR : Python 3.11 est requis pour ce moteur."
  exit 1
fi

echo ""
echo "Cette fonction réutilise le timbre de la voix de la vidéo pour une synthèse."
echo "Elle ne doit être utilisée qu'avec l'autorisation requise."
printf "Confirmez-vous disposer des droits nécessaires ? Saisir OUI : "
IFS= read -r REPONSE
if [[ "$REPONSE" != "OUI" ]]; then
  echo "Annulé : aucune génération vocale."
  exit 1
fi

if [[ ! -d ".venv" ]]; then
  python3.11 -m venv .venv
fi
source .venv/bin/activate

if [[ ! -f .venv/.deeg_clone_pret ]]; then
  python -m pip install --upgrade pip
  python -m pip install -r requirements-clonage.txt
  touch .venv/.deeg_clone_pret
fi

if [[ -f "$RACINE/narrations/essai_clonage.txt" ]]; then
  TEXTE="$RACINE/narrations/essai_clonage.txt"
else
  echo "ERREUR : narrations/essai_clonage.txt manquant."
  exit 1
fi
python scripts/produire_voix_video_locale.py \
  --source "$SOURCE" --texte-fichier "$TEXTE" \
  --vitesse 85 --debut 0 --autorisation \
  --sortie "$RACINE/sorties-video-local"
echo ""
echo "Narration disponible dans : $RACINE/sorties-video-local"
