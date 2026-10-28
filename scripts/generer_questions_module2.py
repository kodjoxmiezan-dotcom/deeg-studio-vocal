"""Lire intégralement les trois questions finales du module 2 (voix DEEG B)."""
from __future__ import annotations

import json
import os
import torch
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
import optimiser_tanguy as opt

QUESTIONS = [
    "Quels droits sont menacés dans ces différentes situations ?",
    "Quels textes internationaux, régionaux et ivoiriens peuvent être mobilisés ?",
    "Quelles mesures concrètes l’établissement doit-il prendre pour protéger les élèves et prévenir les discriminations ?",
]

def main():
    opt.OUTPUT = opt.ROOT / "sorties-questions-module2"
    opt.OUTPUT.mkdir(parents=True, exist_ok=True)
    speed = opt.valid_speed(os.getenv("DEEG_SPEED", "85"))
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("Génération DEEG Module 2 — voix B, trois questions exactes", flush=True)
    model = ChatterboxMultilingualTTS.from_pretrained(device=device, t3_model="v3")
    base = next(p for p in opt.PROFILES if p["id"] == "B_institutionnel")
    manifest = []
    for i, question in enumerate(QUESTIONS, 1):
        profile = dict(base)
        profile["id"] = f"question_{i}"
        info = opt.make_audio(model, torch, question, profile, speed, device)
        info["question"] = question
        manifest.append(info)
    (opt.OUTPUT / "questions_integrales.txt").write_text("\n\n".join(QUESTIONS) + "\n", encoding="utf-8")
    (opt.OUTPUT / "questions_rapport.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("FIN : trois questions au complet, jamais de référence privée exportée.", flush=True)

if __name__ == "__main__":
    main()
