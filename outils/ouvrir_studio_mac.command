#!/bin/bash
# DEEG Studio Vocal : interface française locale, sans publication du son source.
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v python3.11 >/dev/null 2>&1; then
  echo "Python 3.11 requis. Installez-le puis recommencez."
  exit 1
fi
if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v ffprobe >/dev/null 2>&1; then
  echo "FFmpeg/FFprobe requis. Sur Mac avec Homebrew : brew install ffmpeg"
  exit 1
fi

if [[ ! -d .venv ]]; then
  python3.11 -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip
if [[ ! -f .venv/.deeg_ui_pret ]]; then
  python -m pip install -r requirements-interface.txt
  touch .venv/.deeg_ui_pret
fi

printf "\nStudio vocal local : http://127.0.0.1:7860\n"
printf "La reference audio n'est pas publiee dans GitHub.\n"
printf "Pour générer une narration, installez aussi le moteur si nécessaire :\n"
printf "  python -m pip install -r requirements-clonage.txt\n\n"
python scripts/interface_studio.py
